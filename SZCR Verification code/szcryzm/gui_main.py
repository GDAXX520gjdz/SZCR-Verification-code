import os
import sys
import threading
from datetime import datetime
from tkinter import *
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import io

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from captcha_generator.generator import CaptchaGenerator
from captcha_recognizer.traditional_recognizer import TraditionalCaptchaRecognizer
from captcha_recognizer.ml_recognizer import MLCaptchaRecognizer
from utils.utils import HistoryManager, validate_captcha


class ModernCaptchaGUI:
    """现代化的验证码生成与识别系统GUI"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("验证码生成与识别系统")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')
        
        # 初始化系统组件
        self.generator = CaptchaGenerator()
        self.traditional_recognizer = TraditionalCaptchaRecognizer()
        self.ml_recognizer = MLCaptchaRecognizer()
        self.history_manager = HistoryManager()
        self.current_captcha = None
        self.current_captcha_text = None
        self.current_captcha_image_tk = None
        
        # 设置样式
        self.setup_styles()
        
        # 创建界面
        self.create_widgets()
        
        # 加载模型（如果存在）
        self.ml_recognizer.load_model()
    
    def setup_styles(self):
        """设置现代化样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置按钮样式
        style.configure('Primary.TButton', 
                       font=('Microsoft YaHei UI', 10, 'bold'),
                       padding=10)
        style.configure('Success.TButton',
                       font=('Microsoft YaHei UI', 9),
                       padding=8)
        style.configure('Info.TButton',
                       font=('Microsoft YaHei UI', 9),
                       padding=8)
        
        # 配置标签样式
        style.configure('Title.TLabel',
                       font=('Microsoft YaHei UI', 16, 'bold'),
                       background='#f0f0f0',
                       foreground='#2c3e50')
        style.configure('Heading.TLabel',
                       font=('Microsoft YaHei UI', 12, 'bold'),
                       background='#f0f0f0',
                       foreground='#34495e')
        style.configure('Normal.TLabel',
                       font=('Microsoft YaHei UI', 10),
                       background='#f0f0f0',
                       foreground='#555555')
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建主容器
        main_frame = Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        # 标题
        title_frame = Frame(main_frame, bg='#f0f0f0')
        title_frame.pack(fill=X, pady=(0, 20))
        
        title_label = Label(title_frame, 
                           text="🔐 验证码生成与识别系统",
                           font=('Microsoft YaHei UI', 20, 'bold'),
                           bg='#f0f0f0',
                           fg='#2c3e50')
        title_label.pack()
        
        subtitle_label = Label(title_frame,
                               text="CAPTCHA Generator & Recognizer",
                               font=('Microsoft YaHei UI', 11),
                               bg='#f0f0f0',
                               fg='#7f8c8d')
        subtitle_label.pack()
        
        # 创建左右分栏
        content_frame = Frame(main_frame, bg='#f0f0f0')
        content_frame.pack(fill=BOTH, expand=True)
        
        # 左侧面板 - 验证码显示和控制
        left_panel = Frame(content_frame, bg='white', relief=RAISED, bd=1)
        left_panel.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))
        
        # 右侧面板 - 功能按钮和信息
        right_panel = Frame(content_frame, bg='white', relief=RAISED, bd=1)
        right_panel.pack(side=RIGHT, fill=Y, padx=(10, 0))
        
        self.create_left_panel(left_panel)
        self.create_right_panel(right_panel)
    
    def create_left_panel(self, parent):
        """创建左侧面板"""
        # 验证码显示区域
        display_frame = Frame(parent, bg='white')
        display_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        Label(display_frame,
              text="验证码预览",
              font=('Microsoft YaHei UI', 12, 'bold'),
              bg='white',
              fg='#34495e').pack(pady=(0, 10))
        
        # 验证码图像显示
        self.captcha_canvas = Canvas(display_frame,
                                     width=400,
                                     height=200,
                                     bg='#f8f9fa',
                                     highlightthickness=1,
                                     highlightbackground='#dee2e6')
        self.captcha_canvas.pack(pady=10)
        
        # 验证码文本显示
        self.captcha_text_label = Label(display_frame,
                                        text="点击下方按钮生成验证码",
                                        font=('Microsoft YaHei UI', 14),
                                        bg='white',
                                        fg='#6c757d')
        self.captcha_text_label.pack(pady=10)
        
        # 识别结果显示
        result_frame = Frame(display_frame, bg='white')
        result_frame.pack(fill=X, pady=10)
        
        Label(result_frame,
              text="识别结果:",
              font=('Microsoft YaHei UI', 10, 'bold'),
              bg='white',
              fg='#495057').pack(side=LEFT)
        
        self.result_label = Label(result_frame,
                                  text="未识别",
                                  font=('Microsoft YaHei UI', 11),
                                  bg='white',
                                  fg='#28a745')
        self.result_label.pack(side=LEFT, padx=10)
        
        # 用户输入区域
        input_frame = Frame(display_frame, bg='white')
        input_frame.pack(fill=X, pady=10)
        
        Label(input_frame,
              text="手动输入验证码:",
              font=('Microsoft YaHei UI', 10),
              bg='white',
              fg='#495057').pack(side=LEFT, padx=(0, 10))
        
        self.input_entry = Entry(input_frame,
                                 font=('Microsoft YaHei UI', 12),
                                 width=15,
                                 relief=SOLID,
                                 bd=1)
        self.input_entry.pack(side=LEFT, padx=5)
        
        validate_btn = Button(input_frame,
                             text="验证",
                             font=('Microsoft YaHei UI', 9),
                             bg='#17a2b8',
                             fg='white',
                             relief=FLAT,
                             padx=15,
                             pady=5,
                             cursor='hand2',
                             command=self.validate_input)
        validate_btn.pack(side=LEFT, padx=5)
    
    def create_right_panel(self, parent):
        """创建右侧面板"""
        # 功能按钮区域
        button_frame = Frame(parent, bg='white')
        button_frame.pack(fill=X, padx=20, pady=20)
        
        Label(button_frame,
              text="功能菜单",
              font=('Microsoft YaHei UI', 14, 'bold'),
              bg='white',
              fg='#2c3e50').pack(pady=(0, 15))
        
        # 生成验证码按钮组
        gen_frame = Frame(button_frame, bg='white')
        gen_frame.pack(fill=X, pady=5)
        
        Label(gen_frame,
              text="生成验证码",
              font=('Microsoft YaHei UI', 10, 'bold'),
              bg='white',
              fg='#495057').pack(anchor=W, pady=(0, 5))
        
        btn_simple = Button(gen_frame,
                           text="简单 (4位)",
                           font=('Microsoft YaHei UI', 9),
                           bg='#28a745',
                           fg='white',
                           relief=FLAT,
                           padx=20,
                           pady=8,
                           cursor='hand2',
                           command=lambda: self.generate_captcha('simple', 4))
        btn_simple.pack(fill=X, pady=2)
        
        btn_medium = Button(gen_frame,
                           text="中等 (5位)",
                           font=('Microsoft YaHei UI', 9),
                           bg='#ffc107',
                           fg='#212529',
                           relief=FLAT,
                           padx=20,
                           pady=8,
                           cursor='hand2',
                           command=lambda: self.generate_captcha('medium', 5))
        btn_medium.pack(fill=X, pady=2)
        
        btn_hard = Button(gen_frame,
                         text="困难 (6位)",
                         font=('Microsoft YaHei UI', 9),
                         bg='#dc3545',
                         fg='white',
                         relief=FLAT,
                         padx=20,
                         pady=8,
                         cursor='hand2',
                         command=lambda: self.generate_captcha('hard', 6))
        btn_hard.pack(fill=X, pady=2)
        
        # 识别按钮组
        recog_frame = Frame(button_frame, bg='white')
        recog_frame.pack(fill=X, pady=(15, 5))
        
        Label(recog_frame,
              text="识别验证码",
              font=('Microsoft YaHei UI', 10, 'bold'),
              bg='white',
              fg='#495057').pack(anchor=W, pady=(0, 5))
        
        btn_tesseract = Button(recog_frame,
                              text="Tesseract OCR",
                              font=('Microsoft YaHei UI', 9),
                              bg='#17a2b8',
                              fg='white',
                              relief=FLAT,
                              padx=20,
                              pady=8,
                              cursor='hand2',
                              command=lambda: self.recognize_captcha('tesseract'))
        btn_tesseract.pack(fill=X, pady=2)
        
        btn_template = Button(recog_frame,
                             text="模板匹配",
                             font=('Microsoft YaHei UI', 9),
                             bg='#6c757d',
                             fg='white',
                             relief=FLAT,
                             padx=20,
                             pady=8,
                             cursor='hand2',
                             command=lambda: self.recognize_captcha('template'))
        btn_template.pack(fill=X, pady=2)
        
        btn_ml = Button(recog_frame,
                       text="机器学习",
                       font=('Microsoft YaHei UI', 9),
                       bg='#6f42c1',
                       fg='white',
                       relief=FLAT,
                       padx=20,
                       pady=8,
                       cursor='hand2',
                       command=lambda: self.recognize_captcha('ml'))
        btn_ml.pack(fill=X, pady=2)
        
        # 其他功能按钮
        other_frame = Frame(button_frame, bg='white')
        other_frame.pack(fill=X, pady=(15, 5))
        
        btn_batch = Button(other_frame,
                          text="批量生成",
                          font=('Microsoft YaHei UI', 9),
                          bg='#fd7e14',
                          fg='white',
                          relief=FLAT,
                          padx=20,
                          pady=8,
                          cursor='hand2',
                          command=self.batch_generate_dialog)
        btn_batch.pack(fill=X, pady=2)
        
        btn_history = Button(other_frame,
                            text="历史记录",
                            font=('Microsoft YaHei UI', 9),
                            bg='#20c997',
                            fg='white',
                            relief=FLAT,
                            padx=20,
                            pady=8,
                            cursor='hand2',
                            command=self.show_history)
        btn_history.pack(fill=X, pady=2)
        
        btn_stats = Button(other_frame,
                          text="统计信息",
                          font=('Microsoft YaHei UI', 9),
                          bg='#e83e8c',
                          fg='white',
                          relief=FLAT,
                          padx=20,
                          pady=8,
                          cursor='hand2',
                          command=self.show_statistics)
        btn_stats.pack(fill=X, pady=2)
        
        btn_train = Button(other_frame,
                          text="训练模型",
                          font=('Microsoft YaHei UI', 9),
                          bg='#6610f2',
                          fg='white',
                          relief=FLAT,
                          padx=20,
                          pady=8,
                          cursor='hand2',
                          command=self.train_model_dialog)
        btn_train.pack(fill=X, pady=2)
        
        # 保存按钮
        save_frame = Frame(button_frame, bg='white')
        save_frame.pack(fill=X, pady=(15, 5))
        
        btn_save = Button(save_frame,
                         text="💾 保存验证码",
                         font=('Microsoft YaHei UI', 9),
                         bg='#007bff',
                         fg='white',
                         relief=FLAT,
                         padx=20,
                         pady=8,
                         cursor='hand2',
                         command=self.save_captcha)
        btn_save.pack(fill=X)
        
        # 清空历史按钮
        clear_frame = Frame(button_frame, bg='white')
        clear_frame.pack(fill=X, pady=(10, 0))
        
        btn_clear = Button(clear_frame,
                          text="🗑️ 清空历史",
                          font=('Microsoft YaHei UI', 9),
                          bg='#dc3545',
                          fg='white',
                          relief=FLAT,
                          padx=20,
                          pady=8,
                          cursor='hand2',
                          command=self.clear_history)
        btn_clear.pack(fill=X)
    
    def generate_captcha(self, difficulty, length):
        """生成验证码"""
        try:
            if difficulty == 'simple':
                self.current_captcha_text, self.current_captcha = self.generator.generate_simple_captcha(length)
            elif difficulty == 'medium':
                self.current_captcha_text, self.current_captcha = self.generator.generate_medium_captcha(length)
            elif difficulty == 'hard':
                self.current_captcha_text, self.current_captcha = self.generator.generate_hard_captcha(length)
            
            # 更新显示
            self.update_captcha_display()
            self.result_label.config(text="未识别", fg='#6c757d')
            self.input_entry.delete(0, END)
            
        except Exception as e:
            messagebox.showerror("错误", f"生成验证码失败: {str(e)}")
    
    def update_captcha_display(self):
        """更新验证码显示"""
        if self.current_captcha:
            # 调整图像大小以适应画布
            display_size = (400, 200)
            try:
                # 新版本PIL使用Image.Resampling
                img_resized = self.current_captcha.resize(display_size, Image.Resampling.LANCZOS)
            except AttributeError:
                # 旧版本PIL使用Image.LANCZOS
                img_resized = self.current_captcha.resize(display_size, Image.LANCZOS)
            
            # 转换为Tkinter格式
            self.current_captcha_image_tk = ImageTk.PhotoImage(img_resized)
            
            # 清除画布并显示新图像
            self.captcha_canvas.delete("all")
            self.captcha_canvas.create_image(200, 100, image=self.current_captcha_image_tk)
            
            # 更新文本标签
            self.captcha_text_label.config(
                text=f"验证码: {self.current_captcha_text}",
                fg='#2c3e50'
            )
    
    def recognize_captcha(self, method):
        """识别验证码"""
        if self.current_captcha is None:
            messagebox.showwarning("警告", "请先生成验证码")
            return
        
        def recognize_thread():
            try:
                if method == 'tesseract':
                    result = self.traditional_recognizer.recognize_with_tesseract(self.current_captcha)
                elif method == 'template':
                    result = self.traditional_recognizer.recognize_with_template_matching(self.current_captcha)
                elif method == 'ml':
                    if self.ml_recognizer.model is None:
                        if not messagebox.askyesno("提示", "模型未加载，是否现在训练？"):
                            return
                        self.train_model_dialog()
                        if self.ml_recognizer.model is None:
                            return
                    result = self.ml_recognizer.predict(self.current_captcha)
                
                # 更新UI（需要在主线程中执行）
                self.root.after(0, lambda: self.update_recognition_result(result, method))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("错误", f"识别失败: {str(e)}"))
        
        # 在后台线程中执行识别
        thread = threading.Thread(target=recognize_thread)
        thread.daemon = True
        thread.start()
        
        # 显示加载提示
        self.result_label.config(text="识别中...", fg='#ffc107')
    
    def update_recognition_result(self, result, method):
        """更新识别结果"""
        self.result_label.config(text=result, fg='#28a745' if result == self.current_captcha_text else '#dc3545')
        
        # 添加到历史记录
        success = (result == self.current_captcha_text)
        self.history_manager.add_record(
            self.current_captcha_text,
            result,
            'unknown',
            method,
            success
        )
        
        if success:
            messagebox.showinfo("成功", f"识别正确！\n结果: {result}")
        else:
            messagebox.showwarning("识别错误", f"识别结果: {result}\n正确答案: {self.current_captcha_text}")
    
    def validate_input(self):
        """验证用户输入"""
        user_input = self.input_entry.get().strip()
        if not user_input:
            messagebox.showwarning("警告", "请输入验证码")
            return
        
        if self.current_captcha_text is None:
            messagebox.showwarning("警告", "请先生成验证码")
            return
        
        success, message = validate_captcha(user_input, self.current_captcha_text)
        
        # 添加到历史记录
        self.history_manager.add_record(
            self.current_captcha_text,
            user_input,
            'user_input',
            'manual',
            success
        )
        
        if success:
            self.result_label.config(text=user_input, fg='#28a745')
            messagebox.showinfo("成功", message)
        else:
            self.result_label.config(text=user_input, fg='#dc3545')
            messagebox.showwarning("错误", message)
    
    def batch_generate_dialog(self):
        """批量生成对话框"""
        dialog = Toplevel(self.root)
        dialog.title("批量生成验证码")
        dialog.geometry("400x300")
        dialog.configure(bg='white')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        frame = Frame(dialog, bg='white', padx=30, pady=30)
        frame.pack(fill=BOTH, expand=True)
        
        Label(frame, text="批量生成验证码", font=('Microsoft YaHei UI', 14, 'bold'), bg='white').pack(pady=(0, 20))
        
        # 数量输入
        Label(frame, text="生成数量:", font=('Microsoft YaHei UI', 10), bg='white').pack(anchor=W, pady=5)
        count_var = StringVar(value="10")
        Entry(frame, textvariable=count_var, font=('Microsoft YaHei UI', 10), width=20).pack(pady=5)
        
        # 长度输入
        Label(frame, text="验证码长度:", font=('Microsoft YaHei UI', 10), bg='white').pack(anchor=W, pady=5)
        length_var = StringVar(value="5")
        Entry(frame, textvariable=length_var, font=('Microsoft YaHei UI', 10), width=20).pack(pady=5)
        
        # 难度选择
        Label(frame, text="难度:", font=('Microsoft YaHei UI', 10), bg='white').pack(anchor=W, pady=5)
        difficulty_var = StringVar(value="medium")
        difficulty_frame = Frame(frame, bg='white')
        difficulty_frame.pack(pady=5)
        Radiobutton(difficulty_frame, text="简单", variable=difficulty_var, value="simple", bg='white').pack(side=LEFT, padx=5)
        Radiobutton(difficulty_frame, text="中等", variable=difficulty_var, value="medium", bg='white').pack(side=LEFT, padx=5)
        Radiobutton(difficulty_frame, text="困难", variable=difficulty_var, value="hard", bg='white').pack(side=LEFT, padx=5)
        
        def start_batch():
            try:
                count = int(count_var.get())
                length = int(length_var.get())
                difficulty = difficulty_var.get()
                
                dialog.destroy()
                self.batch_generate(count, difficulty, length)
            except ValueError:
                messagebox.showerror("错误", "请输入有效的数字")
        
        Button(frame, text="开始生成", font=('Microsoft YaHei UI', 10),
               bg='#28a745', fg='white', relief=FLAT, padx=20, pady=8,
               command=start_batch).pack(pady=20)
    
    def batch_generate(self, count, difficulty, length):
        """批量生成验证码"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder = f"data/batch_{difficulty}_{timestamp}"
        os.makedirs(folder, exist_ok=True)
        
        progress = Toplevel(self.root)
        progress.title("批量生成中...")
        progress.geometry("400x150")
        progress.configure(bg='white')
        progress.transient(self.root)
        
        Label(progress, text="正在批量生成验证码...", font=('Microsoft YaHei UI', 11), bg='white').pack(pady=20)
        
        progress_var = StringVar(value=f"0/{count}")
        progress_label = Label(progress, textvariable=progress_var, font=('Microsoft YaHei UI', 10), bg='white')
        progress_label.pack()
        
        def generate_thread():
            success_count = 0
            batch_gen = self.generator.batch_generate(count, difficulty, length)
            
            for i, (text, image) in enumerate(batch_gen, 1):
                filename = f"captcha_{i:03d}_{text}.png"
                filepath = os.path.join(folder, filename)
                image.save(filepath)
                success_count += 1
                
                self.root.after(0, lambda i=i: progress_var.set(f"{i}/{count}"))
            
            self.root.after(0, lambda: progress.destroy())
            self.root.after(0, lambda: messagebox.showinfo("完成", f"成功生成 {success_count} 个验证码\n保存位置: {folder}"))
        
        thread = threading.Thread(target=generate_thread)
        thread.daemon = True
        thread.start()
    
    def show_history(self):
        """显示历史记录"""
        history = self.history_manager.history
        
        if not history:
            messagebox.showinfo("提示", "暂无历史记录")
            return
        
        history_window = Toplevel(self.root)
        history_window.title("历史记录")
        history_window.geometry("800x500")
        history_window.configure(bg='white')
        
        # 创建表格
        frame = Frame(history_window, bg='white')
        frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # 表格标题
        headers = ["时间", "验证码", "识别结果", "方法", "难度", "状态"]
        for i, header in enumerate(headers):
            Label(frame, text=header, font=('Microsoft YaHei UI', 10, 'bold'),
                  bg='#343a40', fg='white', width=15, height=2).grid(row=0, column=i, sticky='nsew', padx=1, pady=1)
        
        # 显示最近50条记录
        for idx, record in enumerate(history[-50:], 1):
            row_data = [
                record['timestamp'],
                record['captcha'],
                record['recognized'],
                record['method'],
                record['difficulty'],
                "✓" if record['success'] else "✗"
            ]
            
            for col, data in enumerate(row_data):
                bg_color = '#f8f9fa' if idx % 2 == 0 else 'white'
                fg_color = '#28a745' if col == 5 and record['success'] else ('#dc3545' if col == 5 else '#212529')
                Label(frame, text=str(data), font=('Microsoft YaHei UI', 9),
                      bg=bg_color, fg=fg_color, width=15, anchor='w',
                      padx=5).grid(row=idx, column=col, sticky='nsew', padx=1, pady=1)
        
        # 配置列权重
        for i in range(len(headers)):
            frame.columnconfigure(i, weight=1)
    
    def show_statistics(self):
        """显示统计信息"""
        stats = self.history_manager.get_statistics()
        
        stats_window = Toplevel(self.root)
        stats_window.title("统计信息")
        stats_window.geometry("500x400")
        stats_window.configure(bg='white')
        
        frame = Frame(stats_window, bg='white', padx=30, pady=30)
        frame.pack(fill=BOTH, expand=True)
        
        Label(frame, text="统计信息", font=('Microsoft YaHei UI', 16, 'bold'),
              bg='white', fg='#2c3e50').pack(pady=(0, 20))
        
        # 总体统计
        stats_text = f"总验证次数: {stats['total']}\n"
        stats_text += f"成功次数: {stats['success']}\n"
        stats_text += f"总体准确率: {stats['accuracy']:.2%}\n\n"
        
        # 按难度统计
        if stats['by_difficulty']:
            stats_text += "按难度统计:\n"
            for diff, diff_stats in stats['by_difficulty'].items():
                stats_text += f"  {diff}: {diff_stats['success']}/{diff_stats['total']} = {diff_stats['accuracy']:.2%}\n"
            stats_text += "\n"
        
        # 按方法统计
        if stats['by_method']:
            stats_text += "按方法统计:\n"
            for method, method_stats in stats['by_method'].items():
                stats_text += f"  {method}: {method_stats['success']}/{method_stats['total']} = {method_stats['accuracy']:.2%}\n"
        
        Label(frame, text=stats_text, font=('Microsoft YaHei UI', 11),
              bg='white', fg='#495057', justify=LEFT).pack(anchor=W)
    
    def train_model_dialog(self):
        """训练模型对话框"""
        dialog = Toplevel(self.root)
        dialog.title("训练机器学习模型")
        dialog.geometry("450x350")
        dialog.configure(bg='white')
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = Frame(dialog, bg='white', padx=30, pady=30)
        frame.pack(fill=BOTH, expand=True)
        
        Label(frame, text="训练机器学习模型", font=('Microsoft YaHei UI', 14, 'bold'),
              bg='white').pack(pady=(0, 20))
        
        # 数据集路径
        Label(frame, text="数据集路径:", font=('Microsoft YaHei UI', 10), bg='white').pack(anchor=W, pady=5)
        dataset_var = StringVar(value="data/dataset")
        Entry(frame, textvariable=dataset_var, font=('Microsoft YaHei UI', 10), width=30).pack(pady=5)
        
        Button(frame, text="浏览...", font=('Microsoft YaHei UI', 9),
               bg='#6c757d', fg='white', relief=FLAT, padx=15, pady=5,
               command=lambda: dataset_var.set(filedialog.askdirectory(initialdir="data"))).pack(pady=5)
        
        # 模型类型选择
        Label(frame, text="模型类型:", font=('Microsoft YaHei UI', 10), bg='white').pack(anchor=W, pady=(15, 5))
        model_var = StringVar(value="knn")
        model_frame = Frame(frame, bg='white')
        model_frame.pack(pady=5)
        Radiobutton(model_frame, text="KNN", variable=model_var, value="knn", bg='white').pack(side=LEFT, padx=10)
        Radiobutton(model_frame, text="SVM", variable=model_var, value="svm", bg='white').pack(side=LEFT, padx=10)
        Radiobutton(model_frame, text="Random Forest", variable=model_var, value="random_forest", bg='white').pack(side=LEFT, padx=10)
        
        progress_label = Label(frame, text="", font=('Microsoft YaHei UI', 10), bg='white', fg='#28a745')
        progress_label.pack(pady=10)
        
        def start_train():
            dataset_path = dataset_var.get()
            model_type = model_var.get()
            
            if not os.path.exists(dataset_path):
                messagebox.showerror("错误", f"数据集路径不存在: {dataset_path}")
                return
            
            dialog.destroy()
            
            # 显示训练进度窗口
            train_window = Toplevel(self.root)
            train_window.title("训练中...")
            train_window.geometry("400x150")
            train_window.configure(bg='white')
            train_window.transient(self.root)
            
            Label(train_window, text="正在训练模型，请稍候...", font=('Microsoft YaHei UI', 11),
                  bg='white').pack(pady=30)
            
            def train_thread():
                try:
                    self.ml_recognizer = MLCaptchaRecognizer(model_type)
                    accuracy = self.ml_recognizer.train(dataset_path)
                    
                    self.root.after(0, lambda: train_window.destroy())
                    if accuracy > 0:
                        self.root.after(0, lambda: messagebox.showinfo("成功", f"训练完成！\n准确率: {accuracy:.2%}"))
                    else:
                        self.root.after(0, lambda: messagebox.showerror("失败", "训练失败，请检查数据集"))
                except Exception as e:
                    self.root.after(0, lambda: train_window.destroy())
                    self.root.after(0, lambda: messagebox.showerror("错误", f"训练出错: {str(e)}"))
            
            thread = threading.Thread(target=train_thread)
            thread.daemon = True
            thread.start()
        
        Button(frame, text="开始训练", font=('Microsoft YaHei UI', 10),
               bg='#28a745', fg='white', relief=FLAT, padx=20, pady=8,
               command=start_train).pack(pady=20)
    
    def save_captcha(self):
        """保存验证码"""
        if self.current_captcha is None:
            messagebox.showwarning("警告", "请先生成验证码")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
            initialdir="data/captchas"
        )
        
        if filename:
            try:
                self.current_captcha.save(filename)
                messagebox.showinfo("成功", f"验证码已保存到:\n{filename}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")
    
    def clear_history(self):
        """清空历史记录"""
        if messagebox.askyesno("确认", "确定要清空所有历史记录吗？"):
            self.history_manager.clear_history()
            messagebox.showinfo("成功", "历史记录已清空")


def main():
    """主函数"""
    # 创建必要的目录
    os.makedirs('data/captchas', exist_ok=True)
    os.makedirs('data/models', exist_ok=True)
    os.makedirs('data/templates', exist_ok=True)
    
    root = Tk()
    app = ModernCaptchaGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

