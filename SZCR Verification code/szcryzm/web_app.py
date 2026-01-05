import os
import sys
import json
import base64
import io
import threading
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from captcha_generator.generator import CaptchaGenerator
from captcha_recognizer.traditional_recognizer import TraditionalCaptchaRecognizer
from captcha_recognizer.ml_recognizer import MLCaptchaRecognizer
from utils.utils import HistoryManager, validate_captcha

app = Flask(__name__)
app.secret_key = os.urandom(24)  # 用于session加密
app.config['UPLOAD_FOLDER'] = 'data/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 创建必要的目录
os.makedirs('data/captchas', exist_ok=True)
os.makedirs('data/models', exist_ok=True)
os.makedirs('data/templates', exist_ok=True)
os.makedirs('data/uploads', exist_ok=True)
os.makedirs('data/users', exist_ok=True)
os.makedirs('data/dataset', exist_ok=True)

# 创建数据集目录结构（如果不存在）
characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
for char in characters:
    char_folder = os.path.join('data/dataset', char)
    os.makedirs(char_folder, exist_ok=True)

# 用户系统实例存储（使用字典存储，因为session不能存储对象）
user_systems = {}

def get_user_system():
    """获取当前用户的系统实例"""
    user_id = session.get('user_id', 'default')
    if user_id not in user_systems:
        user_systems[user_id] = {
            'generator': CaptchaGenerator(),
            'traditional_recognizer': TraditionalCaptchaRecognizer(),
            'ml_recognizer': MLCaptchaRecognizer(),
            'history_manager': HistoryManager(
                history_file=f"data/users/{user_id}_history.json"
            ),
            'current_captcha_text': None
        }
        # 尝试加载模型
        user_systems[user_id]['ml_recognizer'].load_model()
    return user_systems[user_id]

def init_user_system():
    """初始化用户系统组件（兼容性函数）"""
    return get_user_system()

# 用户管理
USERS_FILE = 'data/users.json'

def load_users():
    """加载用户数据"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_users(users):
    """保存用户数据"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def init_default_user():
    """初始化默认用户"""
    users = load_users()
    # 确保szcr用户存在且是管理员
    if 'szcr' not in users:
        users['szcr'] = {
            'password': generate_password_hash('dbbhs'),
            'email': 'admin@szcr.com',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'is_admin': True,
            'role': 'admin'
        }
        save_users(users)
    else:
        # 如果szcr已存在，确保它是管理员
        if not users['szcr'].get('is_admin', False) or users['szcr'].get('role') != 'admin':
            users['szcr']['is_admin'] = True
            users['szcr']['role'] = 'admin'
            # 如果密码不是dbbhs，更新密码
            if not check_password_hash(users['szcr']['password'], 'dbbhs'):
                users['szcr']['password'] = generate_password_hash('dbbhs')
            save_users(users)

def is_admin(username):
    """检查用户是否为管理员"""
    users = load_users()
    if username in users:
        return users[username].get('is_admin', False) or users[username].get('role') == 'admin'
    return False

# 登录装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # 如果是API请求，返回JSON错误
            if request.path.startswith('/api/'):
                return jsonify({'error': '请先登录'}), 401
            # 否则重定向到登录页
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 普通用户权限装饰器（只允许生成验证码）
def user_allowed(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_type = session.get('user_type', 'user')
        if user_type == 'admin':
            # 管理员可以使用所有功能
            return f(*args, **kwargs)
        # 普通用户只能使用生成验证码功能
        if request.path == '/api/generate':
            return f(*args, **kwargs)
        # 其他功能需要管理员权限
        if request.path.startswith('/api/'):
            return jsonify({'error': '此功能需要管理员权限'}), 403
        return redirect(url_for('dashboard'))
    return decorated_function

# 管理员权限装饰器
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'error': '请先登录'}), 401
            return redirect(url_for('login'))
        
        if not is_admin(session.get('user_id')):
            if request.path.startswith('/api/'):
                return jsonify({'error': '需要管理员权限'}), 403
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

# 路由
@app.route('/')
def index():
    """首页"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        login_type = data.get('login_type', 'user')  # 获取登录类型
        
        users = load_users()
        
        # 检查用户是否存在
        if username not in users:
            return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
        
        # 验证密码
        password_valid = check_password_hash(users[username]['password'], password)
        
        # 如果是szcr用户且密码是dbbhs，但哈希不匹配，更新密码
        if username == 'szcr' and password == 'dbbhs' and not password_valid:
            users['szcr']['password'] = generate_password_hash('dbbhs')
            users['szcr']['is_admin'] = True
            users['szcr']['role'] = 'admin'
            save_users(users)
            password_valid = True
        
        if password_valid:
            user_is_admin = is_admin(username)
            
            # 验证登录类型权限
            if login_type == 'admin' and not user_is_admin:
                return jsonify({'success': False, 'message': '该用户不是管理员，无法以管理员身份登录'}), 403
            
            session['user_id'] = username
            session['username'] = username
            session['user_type'] = login_type
            session['is_admin'] = user_is_admin
            init_user_system()  # 初始化用户系统
            
            # 根据登录类型返回重定向URL
            redirect_url = '/admin' if login_type == 'admin' else '/dashboard'
            return jsonify({'success': True, 'message': '登录成功', 'user_type': login_type, 'redirect_to': redirect_url})
        else:
            return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
    
    if 'user_id' in session:
        # 根据用户类型重定向
        user_type = session.get('user_type', 'user')
        if user_type == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """注册页面"""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip()
        
        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
        
        users = load_users()
        if username in users:
            return jsonify({'success': False, 'message': '用户名已存在'}), 400
        
        users[username] = {
            'password': generate_password_hash(password),
            'email': email,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'is_admin': False,
            'role': 'user'
        }
        save_users(users)
        
        return jsonify({'success': True, 'message': '注册成功，请登录'})
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """登出"""
    user_id = session.get('user_id')
    if user_id and user_id in user_systems:
        # 清理用户系统实例
        del user_systems[user_id]
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """主界面（普通用户和管理员都可以访问）"""
    user_type = session.get('user_type', 'user')
    is_admin_user = is_admin(session.get('user_id', ''))
    
    # 允许管理员访问dashboard，但显示管理员权限
    return render_template('dashboard.html', 
                         username=session.get('username', 'User'),
                         is_admin=is_admin_user,
                         user_type=user_type)

# API路由
@app.route('/api/generate', methods=['POST'])
@login_required
def api_generate():
    """生成验证码API"""
    try:
        data = request.get_json()
        difficulty = data.get('difficulty', 'medium')
        length = int(data.get('length', 5))
        
        system = init_user_system()
        generator = system['generator']
        
        if difficulty == 'simple':
            text, image = generator.generate_simple_captcha(length)
        elif difficulty == 'medium':
            text, image = generator.generate_medium_captcha(length)
        elif difficulty == 'hard':
            text, image = generator.generate_hard_captcha(length)
        else:
            return jsonify({'error': '无效的难度级别'}), 400
        
        # 保存到session
        system['current_captcha_text'] = text
        
        # 将图像转换为base64
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='PNG')
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'text': text,
            'image': f'data:image/png;base64,{img_str}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recognize', methods=['POST'])
@login_required
def api_recognize():
    """识别验证码API"""
    # 检查权限：只有管理员可以使用识别功能
    user_id = session.get('user_id', '')
    if not is_admin(user_id):
        return jsonify({'error': '此功能需要管理员权限'}), 403
    
    try:
        data = request.get_json()
        method = data.get('method', 'tesseract')
        
        system = init_user_system()
        
        # 从base64获取图像
        image_data = data.get('image', '')
        if not image_data:
            return jsonify({'error': '未提供图像'}), 400
        
        # 解码base64图像
        try:
            # 处理data URI格式: data:image/png;base64,...
            if ',' in image_data:
                img_data = base64.b64decode(image_data.split(',')[1])
            else:
                img_data = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(img_data))
        except Exception as e:
            return jsonify({'error': f'图像解码失败: {str(e)}'}), 400
        
        # 识别
        result = ""
        error_msg = None
        try:
            if method == 'tesseract':
                result = system['traditional_recognizer'].recognize_with_tesseract(image)
                if not result:
                    error_msg = 'Tesseract识别失败，可能未安装Tesseract OCR或路径未配置'
            elif method == 'template':
                # 使用绝对路径确保能找到模板文件夹
                # web_app.py 在 szcryzm/ 目录下，模板文件夹在 szcryzm/data/templates
                base_dir = os.path.dirname(os.path.abspath(__file__))
                template_folder = os.path.join(base_dir, 'data', 'templates')
                result = system['traditional_recognizer'].recognize_with_template_matching(image, template_folder)
                if not result:
                    error_msg = '模板匹配失败，可能模板文件夹不存在或未找到匹配模板'
            elif method == 'ml':
                if system['ml_recognizer'].model is None:
                    return jsonify({'error': '模型未加载，请先训练模型'}), 400
                result = system['ml_recognizer'].predict(image)
                if not result:
                    error_msg = '机器学习识别失败，可能无法分割字符或模型预测出错'
            else:
                return jsonify({'error': '无效的识别方法'}), 400
        except Exception as e:
            import traceback
            error_msg = f'识别过程出错: {str(e)}'
            print(f"识别错误: {traceback.format_exc()}")
        
        # 如果识别失败，返回错误
        if not result and error_msg:
            return jsonify({'error': error_msg, 'result': ''}), 400
        
        # 验证结果
        correct_text = system.get('current_captcha_text', '')
        success = (result == correct_text) if correct_text else False
        
        # 添加到历史记录
        system['history_manager'].add_record(
            correct_text or 'unknown',
            result,
            'unknown',
            method,
            success
        )
        
        return jsonify({
            'success': True,
            'result': result,
            'correct': correct_text,
            'match': success
        })
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/api/validate', methods=['POST'])
@admin_required
def api_validate():
    """验证用户输入API"""
    try:
        data = request.get_json()
        user_input = data.get('input', '').strip()
        
        system = init_user_system()
        correct_text = system.get('current_captcha_text', '')
        
        if not correct_text:
            return jsonify({'error': '请先生成验证码'}), 400
        
        success, message = validate_captcha(user_input, correct_text)
        
        # 添加到历史记录
        system['history_manager'].add_record(
            correct_text,
            user_input,
            'user_input',
            'manual',
            success
        )
        
        return jsonify({
            'success': success,
            'message': message
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/batch_generate', methods=['POST'])
@admin_required
def api_batch_generate():
    """批量生成验证码API"""
    try:
        data = request.get_json()
        count = int(data.get('count', 10))
        difficulty = data.get('difficulty', 'medium')
        length = int(data.get('length', 5))
        
        system = init_user_system()
        generator = system['generator']
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder = f"data/captchas/batch_{session.get('user_id', 'default')}_{timestamp}"
        os.makedirs(folder, exist_ok=True)
        
        results = []
        batch_gen = generator.batch_generate(count, difficulty, length)
        
        for i, (text, image) in enumerate(batch_gen, 1):
            filename = f"captcha_{i:03d}_{text}.png"
            filepath = os.path.join(folder, filename)
            image.save(filepath)
            results.append({
                'index': i,
                'text': text,
                'filename': filename
            })
        
        return jsonify({
            'success': True,
            'count': len(results),
            'folder': folder,
            'results': results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
@admin_required
def api_history():
    """获取历史记录API"""
    try:
        system = init_user_system()
        history = system['history_manager'].history
        return jsonify({
            'success': True,
            'history': history[-50:]  # 最近50条
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/statistics', methods=['GET'])
@admin_required
def api_statistics():
    """获取统计信息API"""
    try:
        system = init_user_system()
        stats = system['history_manager'].get_statistics()
        return jsonify({
            'success': True,
            'statistics': stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/train', methods=['POST'])
@login_required
def api_train():
    """训练模型API"""
    # 检查权限：只有管理员可以训练模型
    user_id = session.get('user_id', '')
    if not is_admin(user_id):
        return jsonify({'error': '此功能需要管理员权限'}), 403
    
    try:
        data = request.get_json()
        dataset_path = data.get('dataset_path', 'data/dataset')
        model_type = data.get('model_type', 'knn')
        
        # 检查数据集路径
        if not dataset_path:
            return jsonify({'error': '数据集路径不能为空'}), 400
        
        if not os.path.exists(dataset_path):
            return jsonify({
                'error': f'数据集路径不存在: {dataset_path}',
                'hint': '数据集应按照字符分类组织，例如: data/dataset/A/, data/dataset/B/, ...'
            }), 400
        
        # 检查数据集是否为空
        has_data = False
        characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        folders_with_data = []
        
        for char in characters:
            char_folder = os.path.join(dataset_path, char)
            if os.path.exists(char_folder):
                files = [f for f in os.listdir(char_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                if files:
                    has_data = True
                    folders_with_data.append(f"{char}({len(files)}个文件)")
        
        if not has_data:
            return jsonify({
                'error': '数据集为空，未找到训练数据',
                'hint': f'数据集应按照字符分类组织，例如: {dataset_path}/A/, {dataset_path}/B/, ... 每个文件夹包含该字符的图片文件(.png, .jpg, .jpeg)',
                'detail': f'当前数据集路径: {os.path.abspath(dataset_path)}，请确保每个字符文件夹包含至少一张图片'
            }), 400
        
        # 提供数据集统计信息
        dataset_info = f"找到数据的文件夹: {', '.join(folders_with_data[:10])}"  # 只显示前10个
        if len(folders_with_data) > 10:
            dataset_info += f" 等共{len(folders_with_data)}个文件夹"
        
        system = init_user_system()
        system['ml_recognizer'] = MLCaptchaRecognizer(model_type)
        
        try:
            accuracy = system['ml_recognizer'].train(dataset_path)
            
            if accuracy > 0:
                return jsonify({
                    'success': True,
                    'accuracy': accuracy,
                    'message': f'训练完成，准确率: {accuracy:.2%}',
                    'dataset_info': dataset_info if 'dataset_info' in locals() else ''
                })
            else:
                return jsonify({
                    'error': '训练失败，准确率为0',
                    'hint': '请检查数据集格式和内容是否正确'
                }), 500
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"训练错误: {error_trace}")
            return jsonify({
                'error': f'训练过程出错: {str(e)}',
                'hint': '请检查数据集格式是否正确，确保每个字符文件夹包含有效的图片文件'
            }), 500
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/api/clear_history', methods=['POST'])
@admin_required
def api_clear_history():
    """清空历史记录API"""
    try:
        system = init_user_system()
        system['history_manager'].clear_history()
        return jsonify({'success': True, 'message': '历史记录已清空'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 管理员路由
@app.route('/admin')
@admin_required
def admin_dashboard():
    """管理员主界面"""
    user_type = session.get('user_type', 'user')
    
    # 如果不是管理员身份登录，重定向到普通用户界面
    if user_type != 'admin':
        return redirect(url_for('dashboard'))
    
    return render_template('admin.html', username=session.get('username', 'Admin'))

@app.route('/api/admin/users', methods=['GET'])
@admin_required
def api_admin_users():
    """获取所有用户列表"""
    try:
        users = load_users()
        # 移除密码信息
        user_list = []
        for username, user_data in users.items():
            user_list.append({
                'username': username,
                'email': user_data.get('email', ''),
                'created_at': user_data.get('created_at', ''),
                'is_admin': user_data.get('is_admin', False),
                'role': user_data.get('role', 'user')
            })
        return jsonify({'success': True, 'users': user_list})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<username>', methods=['DELETE'])
@admin_required
def api_admin_delete_user(username):
    """删除用户"""
    try:
        if username == session.get('user_id'):
            return jsonify({'error': '不能删除自己的账号'}), 400
        
        users = load_users()
        if username not in users:
            return jsonify({'error': '用户不存在'}), 404
        
        # 删除用户历史记录文件
        history_file = f"data/users/{username}_history.json"
        if os.path.exists(history_file):
            os.remove(history_file)
        
        # 删除用户系统实例
        if username in user_systems:
            del user_systems[username]
        
        # 从用户列表中删除
        del users[username]
        save_users(users)
        
        return jsonify({'success': True, 'message': f'用户 {username} 已删除'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<username>', methods=['PUT'])
@admin_required
def api_admin_update_user(username):
    """更新用户信息"""
    try:
        data = request.get_json()
        users = load_users()
        
        if username not in users:
            return jsonify({'error': '用户不存在'}), 404
        
        # 更新用户信息
        if 'email' in data:
            users[username]['email'] = data['email']
        
        if 'is_admin' in data:
            users[username]['is_admin'] = bool(data['is_admin'])
            users[username]['role'] = 'admin' if data['is_admin'] else 'user'
        
        if 'password' in data and data['password']:
            users[username]['password'] = generate_password_hash(data['password'])
        
        save_users(users)
        
        return jsonify({'success': True, 'message': '用户信息已更新'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/statistics', methods=['GET'])
@admin_required
def api_admin_statistics():
    """获取系统统计信息"""
    try:
        users = load_users()
        total_users = len(users)
        admin_count = sum(1 for u in users.values() if u.get('is_admin', False))
        
        # 统计所有用户的历史记录
        total_records = 0
        total_success = 0
        all_history = []
        
        for username in users.keys():
            history_file = f"data/users/{username}_history.json"
            if os.path.exists(history_file):
                try:
                    with open(history_file, 'r', encoding='utf-8') as f:
                        user_history = json.load(f)
                        all_history.extend(user_history)
                        total_records += len(user_history)
                        total_success += sum(1 for r in user_history if r.get('success', False))
                except:
                    pass
        
        # 统计文件大小
        captcha_files = 0
        captcha_size = 0
        for root, dirs, files in os.walk('data/captchas'):
            for file in files:
                if file.endswith(('.png', '.jpg')):
                    captcha_files += 1
                    filepath = os.path.join(root, file)
                    captcha_size += os.path.getsize(filepath)
        
        model_files = 0
        model_size = 0
        if os.path.exists('data/models'):
            for file in os.listdir('data/models'):
                if file.endswith('.pkl'):
                    model_files += 1
                    filepath = os.path.join('data/models', file)
                    model_size += os.path.getsize(filepath)
        
        # 计算总体准确率
        overall_accuracy = (total_success / total_records * 100) if total_records > 0 else 0
        
        return jsonify({
            'success': True,
            'statistics': {
                'users': {
                    'total': total_users,
                    'admins': admin_count,
                    'regular': total_users - admin_count
                },
                'records': {
                    'total': total_records,
                    'success': total_success,
                    'accuracy': overall_accuracy
                },
                'storage': {
                    'captcha_files': captcha_files,
                    'captcha_size_mb': round(captcha_size / (1024 * 1024), 2),
                    'model_files': model_files,
                    'model_size_mb': round(model_size / (1024 * 1024), 2)
                },
                'recent_activity': all_history[-20:] if all_history else []
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/cleanup', methods=['POST'])
@admin_required
def api_admin_cleanup():
    """清理系统数据"""
    try:
        data = request.get_json()
        cleanup_type = data.get('type', 'all')
        
        cleaned = []
        
        if cleanup_type in ['captchas', 'all']:
            # 清理验证码文件
            count = 0
            for root, dirs, files in os.walk('data/captchas'):
                for file in files:
                    if file.endswith(('.png', '.jpg')):
                        filepath = os.path.join(root, file)
                        os.remove(filepath)
                        count += 1
            cleaned.append(f'删除了 {count} 个验证码文件')
        
        if cleanup_type in ['history', 'all']:
            # 清理所有用户历史记录
            count = 0
            for username in load_users().keys():
                history_file = f"data/users/{username}_history.json"
                if os.path.exists(history_file):
                    os.remove(history_file)
                    count += 1
            cleaned.append(f'删除了 {count} 个历史记录文件')
        
        if cleanup_type in ['models', 'all']:
            # 清理模型文件
            count = 0
            if os.path.exists('data/models'):
                for file in os.listdir('data/models'):
                    if file.endswith('.pkl'):
                        filepath = os.path.join('data/models', file)
                        os.remove(filepath)
                        count += 1
            cleaned.append(f'删除了 {count} 个模型文件')
        
        return jsonify({
            'success': True,
            'message': '清理完成',
            'cleaned': cleaned
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/history', methods=['GET'])
@admin_required
def api_admin_history():
    """获取所有用户的历史记录"""
    try:
        username_filter = request.args.get('username', '')
        users = load_users()
        all_history = []
        
        for username in users.keys():
            if username_filter and username != username_filter:
                continue
                
            history_file = f"data/users/{username}_history.json"
            if os.path.exists(history_file):
                try:
                    with open(history_file, 'r', encoding='utf-8') as f:
                        user_history = json.load(f)
                        for record in user_history:
                            record['user'] = username
                            all_history.append(record)
                except:
                    pass
        
        # 按时间排序
        all_history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # 返回最近200条
        return jsonify({
            'success': True,
            'history': all_history[:200],
            'users': list(users.keys())
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/logs', methods=['GET'])
@admin_required
def api_admin_logs():
    """获取系统日志"""
    try:
        # 获取所有用户的操作历史作为日志
        logs = []
        users = load_users()
        
        for username in users.keys():
            history_file = f"data/users/{username}_history.json"
            if os.path.exists(history_file):
                try:
                    with open(history_file, 'r', encoding='utf-8') as f:
                        user_history = json.load(f)
                        for record in user_history:
                            logs.append({
                                'user': username,
                                'timestamp': record.get('timestamp', ''),
                                'action': f"识别验证码: {record.get('captcha', '')} -> {record.get('recognized', '')}",
                                'method': record.get('method', ''),
                                'success': record.get('success', False)
                            })
                except:
                    pass
        
        # 按时间排序
        logs.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # 返回最近100条
        return jsonify({
            'success': True,
            'logs': logs[:100]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_default_user()
    app.run(debug=True, host='0.0.0.0', port=5000)

