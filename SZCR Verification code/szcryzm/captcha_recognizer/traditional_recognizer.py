import cv2
import numpy as np
import pytesseract
from PIL import Image
import os


class TraditionalCaptchaRecognizer:
    def __init__(self):
        """初始化传统识别器"""
        # 设置Tesseract路径（根据你的安装位置调整）
        # Windows用户需要取消注释下一行并设置正确路径
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    def preprocess_image(self, image):
        """
        预处理图像
        :param image: PIL图像对象或文件路径
        :return: 处理后的图像
        """
        # 如果输入是文件路径，加载图像
        if isinstance(image, str):
            image = Image.open(image)

        # 转换为OpenCV格式
        if isinstance(image, Image.Image):
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # 转换为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 应用二值化
        _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        # 去噪
        denoised = cv2.medianBlur(binary, 3)

        return denoised

    def recognize_with_tesseract(self, image):
        """
        使用Tesseract OCR识别验证码
        :param image: 图像
        :return: 识别结果
        """
        try:
            # 预处理图像
            processed = self.preprocess_image(image)

            # 使用Tesseract识别
            config = '--psm 8 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            text = pytesseract.image_to_string(processed, config=config)

            # 清理结果
            text = text.strip().replace(' ', '').replace('\n', '')

            return text
        except pytesseract.TesseractNotFoundError:
            print("错误：未找到Tesseract OCR。请安装Tesseract并配置路径。")
            return ""
        except Exception as e:
            print(f"Tesseract识别时出错: {e}")
            return ""

    def segment_characters(self, image):
        """
        分割验证码中的字符
        :param image: 预处理后的图像
        :return: 字符列表
        """
        # 查找轮廓（兼容不同版本的OpenCV）
        contours_result = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # OpenCV 3.x 返回 (image, contours, hierarchy)
        # OpenCV 4.x 返回 (contours, hierarchy)
        contours = contours_result[0] if len(contours_result) == 2 else contours_result[1]

        characters = []
        bounding_boxes = []

        for contour in contours:
            # 获取边界框
            x, y, w, h = cv2.boundingRect(contour)

            # 过滤太小的区域（可能是噪点）
            if w > 10 and h > 20:
                bounding_boxes.append((x, y, w, h))

        # 按x坐标排序（从左到右）
        bounding_boxes.sort(key=lambda box: box[0])

        # 提取每个字符
        for x, y, w, h in bounding_boxes:
            char_image = image[y:y + h, x:x + w]
            characters.append(char_image)

        return characters, bounding_boxes

    def recognize_with_template_matching(self, image, template_folder='data/templates'):
        """
        使用模板匹配识别验证码
        :param image: 图像
        :param template_folder: 模板文件夹
        :return: 识别结果
        """
        # 预处理图像
        processed = self.preprocess_image(image)

        # 分割字符
        characters, _ = self.segment_characters(processed)

        # 如果没有模板文件夹，返回空
        if not os.path.exists(template_folder):
            print(f"模板文件夹不存在: {template_folder}")
            return ""

        # 加载模板
        templates = {}
        for filename in os.listdir(template_folder):
            if filename.endswith('.png') or filename.endswith('.jpg'):
                char = filename[0]  # 假设文件名第一个字符是模板字符
                template_path = os.path.join(template_folder, filename)
                template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
                _, template = cv2.threshold(template, 128, 255, cv2.THRESH_BINARY)
                templates[char] = template

        recognized_text = ""

        # 对每个字符进行模板匹配
        for char_img in characters:
            best_match = None
            best_score = -1

            for char, template in templates.items():
                # 调整模板大小以匹配字符
                if char_img.shape[0] > 0 and char_img.shape[1] > 0:
                    resized_template = cv2.resize(template, (char_img.shape[1], char_img.shape[0]))

                    # 模板匹配
                    result = cv2.matchTemplate(char_img, resized_template, cv2.TM_CCOEFF_NORMED)
                    score = cv2.minMaxLoc(result)[1]

                    if score > best_score:
                        best_score = score
                        best_match = char

            # 如果找到匹配，添加到结果
            if best_match and best_score > 0.5:
                recognized_text += best_match
            else:
                recognized_text += "?"

        return recognized_text