import random
import string
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import os


class CaptchaGenerator:
    def __init__(self, width=200, height=80):
        """
        初始化验证码生成器
        :param width: 图片宽度
        :param height: 图片高度
        """
        self.width = width
        self.height = height
        self.font_path = self._get_font_path()

    def _get_font_path(self):
        """获取字体文件路径"""
        # 尝试常见字体路径
        common_fonts = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/times.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/Arial.ttf"
        ]

        for font in common_fonts:
            if os.path.exists(font):
                return font

        # 如果没有找到字体，使用默认字体
        return None

    def generate_simple_captcha(self, length=4):
        """
        生成简单验证码（纯文本，无干扰）
        :param length: 验证码长度
        :return: (验证码文本, PIL图像对象)
        """
        # 生成随机文本（大写字母+数字）
        chars = string.ascii_uppercase + string.digits
        text = ''.join(random.choice(chars) for _ in range(length))

        # 创建图片
        image = Image.new('RGB', (self.width, self.height), color='white')
        draw = ImageDraw.Draw(image)

        # 使用字体
        try:
            font = ImageFont.truetype(self.font_path, 40) if self.font_path else ImageFont.load_default()
        except (OSError, IOError, AttributeError):
            font = ImageFont.load_default()

        # 计算文本位置（使用textbbox替代已弃用的textsize）
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except AttributeError:
            # 兼容旧版本PIL
            text_width, text_height = draw.textsize(text, font=font)
        x = (self.width - text_width) / 2
        y = (self.height - text_height) / 2

        # 绘制文本
        draw.text((x, y), text, font=font, fill='black')

        return text, image

    def generate_medium_captcha(self, length=5):
        """
        生成中等难度验证码（有噪点和干扰线）
        :param length: 验证码长度
        :return: (验证码文本, PIL图像对象)
        """
        # 生成随机文本
        chars = string.ascii_uppercase + string.digits
        text = ''.join(random.choice(chars) for _ in range(length))

        # 创建图片
        image = Image.new('RGB', (self.width, self.height), color='white')
        draw = ImageDraw.Draw(image)

        # 使用字体
        try:
            font = ImageFont.truetype(self.font_path, 40) if self.font_path else ImageFont.load_default()
        except (OSError, IOError, AttributeError):
            font = ImageFont.load_default()

        # 计算文本位置（使用textbbox替代已弃用的textsize）
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except AttributeError:
            # 兼容旧版本PIL
            text_width, text_height = draw.textsize(text, font=font)
        x = (self.width - text_width) / 2
        y = (self.height - text_height) / 2

        # 绘制文本（随机颜色）
        colors = ['black', 'darkblue', 'darkgreen', 'darkred']
        draw.text((x, y), text, font=font, fill=random.choice(colors))

        # 添加干扰线
        for _ in range(3):
            x1 = random.randint(0, self.width)
            y1 = random.randint(0, self.height)
            x2 = random.randint(0, self.width)
            y2 = random.randint(0, self.height)
            draw.line([(x1, y1), (x2, y2)], fill='gray', width=1)

        # 添加噪点
        for _ in range(100):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            draw.point((x, y), fill='gray')

        return text, image

    def generate_hard_captcha(self, length=5):
        """
        生成高难度验证码（扭曲、旋转、复杂背景）
        :param length: 验证码长度
        :return: (验证码文本, PIL图像对象)
        """
        # 生成随机文本
        chars = string.ascii_uppercase + string.digits
        text = ''.join(random.choice(chars) for _ in range(length))

        # 创建图片
        image = Image.new('RGB', (self.width, self.height), color='white')
        draw = ImageDraw.Draw(image)

        # 使用字体
        try:
            font = ImageFont.truetype(self.font_path, 40) if self.font_path else ImageFont.load_default()
        except (OSError, IOError, AttributeError):
            font = ImageFont.load_default()

        # 绘制每个字符，添加随机旋转和位置偏移
        char_width = self.width // length
        for i, char in enumerate(text):
            # 创建单个字符图像（增大字符区域以提高可读性）
            char_size = max(char_width, 50)
            char_image = Image.new('RGB', (char_size, self.height), color='white')
            char_draw = ImageDraw.Draw(char_image)

            # 计算字符在字符图像中的位置
            try:
                bbox = char_draw.textbbox((0, 0), char, font=font)
                char_text_width = bbox[2] - bbox[0]
                char_text_height = bbox[3] - bbox[1]
            except AttributeError:
                # 兼容旧版本PIL
                char_text_width, char_text_height = char_draw.textsize(char, font=font)
            
            char_x = (char_size - char_text_width) / 2
            char_y = (self.height - char_text_height) / 2

            # 随机颜色（使用更深的颜色以提高可读性）
            color = (random.randint(50, 100), random.randint(50, 100), random.randint(50, 100))
            char_draw.text((char_x, char_y), char, font=font, fill=color)

            # 随机旋转（减小角度范围）
            angle = random.randint(-15, 15)
            rotated_char = char_image.rotate(angle, expand=1, fillcolor='white')

            # 计算位置（考虑旋转后的尺寸）
            rotated_width, rotated_height = rotated_char.size
            x = i * char_width + random.randint(-5, 5)
            y = random.randint(-5, 5)
            # 确保不超出边界
            x = max(0, min(x, self.width - rotated_width))
            y = max(0, min(y, self.height - rotated_height))

            # 粘贴到主图像
            image.paste(rotated_char, (x, y), rotated_char if rotated_char.mode == 'RGBA' else None)

        # 添加复杂背景（在扭曲之前添加，因为draw对象在扭曲后会失效）
        self._add_complex_background(draw)

        # 添加波浪扭曲
        image = self._apply_wave_distortion(image)

        # 添加轻微高斯模糊（降低模糊程度）
        image = image.filter(ImageFilter.GaussianBlur(radius=0.3))

        return text, image

    def _apply_wave_distortion(self, image):
        """应用波浪扭曲效果"""
        # 转换为numpy数组
        img_array = np.array(image)
        rows, cols = img_array.shape[:2]
        is_rgb = len(img_array.shape) == 3

        # 创建坐标网格
        x, y = np.meshgrid(np.arange(cols), np.arange(rows))

        # 应用波浪扭曲（减小扭曲幅度）
        wave_x = x + 1.5 * np.sin(y / 12.0)
        wave_y = y + 1 * np.cos(x / 15.0)

        # 确保坐标在有效范围内
        wave_x = np.clip(wave_x, 0, cols - 1).astype(np.float32)
        wave_y = np.clip(wave_y, 0, rows - 1).astype(np.float32)

        # 使用双线性插值进行重映射
        try:
            from scipy.ndimage import map_coordinates
            # 使用scipy进行插值（如果可用）
            if is_rgb:
                distorted = np.zeros_like(img_array)
                for i in range(img_array.shape[2]):
                    distorted[:, :, i] = map_coordinates(img_array[:, :, i], [wave_y, wave_x], order=1, mode='reflect')
            else:
                distorted = map_coordinates(img_array, [wave_y, wave_x], order=1, mode='reflect')
            return Image.fromarray(distorted.astype(np.uint8))
        except ImportError:
            # 如果没有scipy，使用简单的最近邻插值方法
            distorted_array = np.zeros_like(img_array)
            for i in range(rows):
                for j in range(cols):
                    src_x = int(np.clip(wave_x[i, j], 0, cols - 1))
                    src_y = int(np.clip(wave_y[i, j], 0, rows - 1))
                    if is_rgb:
                        distorted_array[i, j] = img_array[src_y, src_x]
                    else:
                        distorted_array[i, j] = img_array[src_y, src_x]
            return Image.fromarray(distorted_array.astype(np.uint8))

    def _add_complex_background(self, draw):
        """添加复杂背景（减少干扰以提高可读性）"""
        # 添加干扰线（减少数量和降低对比度）
        for _ in range(3):
            x1 = random.randint(0, self.width)
            y1 = random.randint(0, self.height)
            x2 = random.randint(0, self.width)
            y2 = random.randint(0, self.height)
            color = (random.randint(200, 240), random.randint(200, 240), random.randint(200, 240))
            draw.line([(x1, y1), (x2, y2)], fill=color, width=1)

        # 添加随机噪点（减少数量）
        for _ in range(50):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            color = (random.randint(200, 240), random.randint(200, 240), random.randint(200, 240))
            draw.point((x, y), fill=color)

        # 添加随机圆形（减少数量和降低对比度）
        for _ in range(5):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            radius = random.randint(5, 15)
            color = (random.randint(220, 250), random.randint(220, 250), random.randint(220, 250))
            draw.ellipse([x, y, x + radius, y + radius], fill=color, outline=color)

    def batch_generate(self, count=10, difficulty='medium', length=5):
        """
        批量生成验证码
        :param count: 生成数量
        :param difficulty: 难度级别
        :param length: 验证码长度
        :return: 生成器，每次返回(文本, 图像)
        """
        for i in range(count):
            if difficulty == 'simple':
                text, image = self.generate_simple_captcha(length)
            elif difficulty == 'hard':
                text, image = self.generate_hard_captcha(length)
            else:
                text, image = self.generate_medium_captcha(length)

            yield text, image

    def save_captcha(self, image, filename, folder='data/captchas'):
        """
        保存验证码图片
        :param image: PIL图像对象
        :param filename: 文件名
        :param folder: 保存文件夹
        """
        # 确保文件夹存在
        os.makedirs(folder, exist_ok=True)

        # 保存图片
        filepath = os.path.join(folder, filename)
        image.save(filepath)
        print(f"验证码已保存到: {filepath}")