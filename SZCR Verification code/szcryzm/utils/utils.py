import json
import os
from datetime import datetime
from PIL import Image


class HistoryManager:
    """历史记录管理器"""

    def __init__(self, history_file='data/history.json'):
        """
        初始化历史记录管理器
        :param history_file: 历史记录文件路径
        """
        self.history_file = history_file
        self.history = self.load_history()

    def load_history(self):
        """加载历史记录"""
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def save_history(self):
        """保存历史记录"""
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)

    def add_record(self, captcha_text, recognized_text, difficulty, method, success):
        """
        添加记录
        :param captcha_text: 验证码文本
        :param recognized_text: 识别结果
        :param difficulty: 难度
        :param method: 识别方法
        :param success: 是否成功
        """
        record = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'captcha': captcha_text,
            'recognized': recognized_text,
            'difficulty': difficulty,
            'method': method,
            'success': success
        }

        self.history.append(record)
        self.save_history()

    def get_statistics(self):
        """获取统计信息"""
        if not self.history:
            return {
                'total': 0,
                'success': 0,
                'accuracy': 0,
                'by_difficulty': {},
                'by_method': {}
            }

        stats = {
            'total': len(self.history),
            'success': sum(1 for r in self.history if r['success']),
            'by_difficulty': {},
            'by_method': {}
        }

        # 按难度统计
        difficulties = set(r['difficulty'] for r in self.history)
        for diff in difficulties:
            diff_records = [r for r in self.history if r['difficulty'] == diff]
            diff_success = sum(1 for r in diff_records if r['success'])
            stats['by_difficulty'][diff] = {
                'total': len(diff_records),
                'success': diff_success,
                'accuracy': diff_success / len(diff_records) if len(diff_records) > 0 else 0
            }

        # 按方法统计
        methods = set(r['method'] for r in self.history)
        for method in methods:
            method_records = [r for r in self.history if r['method'] == method]
            method_success = sum(1 for r in method_records if r['success'])
            stats['by_method'][method] = {
                'total': len(method_records),
                'success': method_success,
                'accuracy': method_success / len(method_records) if len(method_records) > 0 else 0
            }

        # 总准确率
        stats['accuracy'] = stats['success'] / stats['total'] if stats['total'] > 0 else 0

        return stats

    def clear_history(self):
        """清空历史记录"""
        self.history = []
        self.save_history()
        print("历史记录已清空")


def display_image(image, title="验证码"):
    """
    显示图像
    :param image: PIL图像对象
    :param title: 窗口标题
    """
    try:
        import matplotlib.pyplot as plt

        # 确保是PIL Image对象
        if not isinstance(image, Image.Image):
            from PIL import Image as PILImage
            if isinstance(image, str):
                image = PILImage.open(image)
            else:
                # 尝试转换为PIL Image
                image = PILImage.fromarray(image)

        plt.figure(figsize=(6, 4))
        plt.imshow(image)
        plt.title(title)
        plt.axis('off')
        plt.show()
    except ImportError:
        print("无法显示图像，请确保已安装matplotlib")
        # 保存到临时文件并打开
        try:
            from PIL import Image as PILImage
            if not isinstance(image, PILImage.Image):
                if isinstance(image, str):
                    image = PILImage.open(image)
                else:
                    image = PILImage.fromarray(image)
            temp_path = 'temp_captcha.png'
            image.save(temp_path)
            print(f"验证码已保存到: {temp_path}")
            os.system(f'start {temp_path}' if os.name == 'nt' else f'open {temp_path}')
        except Exception as e:
            print(f"保存图像时出错: {e}")


def validate_captcha(input_text, captcha_text, case_sensitive=False):
    """
    验证用户输入是否正确
    :param input_text: 用户输入
    :param captcha_text: 验证码文本
    :param case_sensitive: 是否区分大小写
    :return: (是否正确, 消息)
    """
    if not input_text:
        return False, "输入不能为空"

    if not case_sensitive:
        input_text = input_text.upper()
        captcha_text = captcha_text.upper()

    if input_text == captcha_text:
        return True, "验证码正确！"
    else:
        return False, f"验证码错误！正确应为: {captcha_text}"