import cv2
import numpy as np
import pytesseract
from PIL import Image
import os


class TraditionalCaptchaRecognizer:
    def __init__(self):
        """初始化传统识别器"""
        # 设置Tesseract路径（根据你的安装位置调整）
        import platform
        if platform.system() == 'Windows':
            # 尝试多个可能的路径
            possible_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            ]
            # 尝试从环境变量获取用户名
            try:
                username = os.getenv('USERNAME', '')
                if username:
                    possible_paths.append(
                        rf'C:\Users\{username}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
                    )
            except:
                pass
            
            # 查找存在的路径
            tesseract_found = False
            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    tesseract_found = True
                    print(f"Tesseract路径已设置为: {path}")
                    break
            
            # 如果都没找到，使用用户指定的路径
            if not tesseract_found:
                default_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
                pytesseract.pytesseract.tesseract_cmd = default_path
                print(f"使用默认Tesseract路径: {default_path}")
                if not os.path.exists(default_path):
                    print(f"警告: Tesseract路径不存在: {default_path}")

    def preprocess_image(self, image, enhance_for_tesseract=False):
        """
        预处理图像
        :param image: PIL图像对象或文件路径
        :param enhance_for_tesseract: 是否针对Tesseract进行增强处理
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

        if enhance_for_tesseract:
            # 针对Tesseract的增强预处理
            # 1. 放大图像（Tesseract在小图像上表现不佳）
            scale_factor = 3
            height, width = gray.shape
            gray = cv2.resize(gray, (width * scale_factor, height * scale_factor), interpolation=cv2.INTER_CUBIC)
            
            # 2. 增强对比度
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            gray = clahe.apply(gray)
            
            # 3. 去噪
            gray = cv2.medianBlur(gray, 3)
            
            # 4. 应用自适应二值化（比全局二值化更好）
            binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            
            # 5. 形态学操作去除小噪点
            kernel = np.ones((2, 2), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
            
            return binary
        else:
            # 标准预处理（用于模板匹配等）
            # 应用二值化
            _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            
            # 去噪
            denoised = cv2.medianBlur(binary, 3)
            
            return denoised

    def recognize_with_tesseract(self, image):
        """
        使用Tesseract OCR识别验证码
        使用多种策略提高识别准确率
        :param image: 图像
        :return: 识别结果
        """
        try:
            # 策略1: 增强预处理 + 整体识别
            processed = self.preprocess_image(image, enhance_for_tesseract=True)
            
            # 尝试多种PSM模式
            psm_modes = [
                ('8', '单个单词'),  # 单个单词
                ('7', '单行文本'),  # 单行文本
                ('13', '原始行'),   # 原始行，不进行特殊处理
                ('6', '统一文本块') # 统一文本块
            ]
            
            results = []
            for psm, desc in psm_modes:
                try:
                    config = f'--psm {psm} --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                    text = pytesseract.image_to_string(processed, config=config)
                    text = text.strip().replace(' ', '').replace('\n', '').replace('\t', '').upper()
                    # 过滤无效字符
                    text = ''.join(c for c in text if c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
                    if text:
                        results.append((text, desc))
                        print(f"PSM {psm} ({desc}) 识别结果: {text}")
                except Exception as e:
                    print(f"PSM {psm} 识别失败: {str(e)}")
                    continue
            
            # 策略2: 如果整体识别效果不好，尝试字符分割后逐个识别
            if not results or len(results[0][0]) < 3:
                print("尝试字符分割识别...")
                try:
                    # 使用标准预处理进行字符分割
                    processed_seg = self.preprocess_image(image, enhance_for_tesseract=False)
                    characters, bounding_boxes = self.segment_characters(processed_seg)
                    
                    if characters and len(characters) >= 3:
                        char_results = []
                        for i, char_img in enumerate(characters):
                            # 放大单个字符
                            h, w = char_img.shape
                            if h > 0 and w > 0:
                                char_img_large = cv2.resize(char_img, (w * 4, h * 4), interpolation=cv2.INTER_CUBIC)
                                
                                # 增强对比度
                                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
                                char_img_large = clahe.apply(char_img_large)
                                
                                # 识别单个字符
                                config = '--psm 10 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                                char_text = pytesseract.image_to_string(char_img_large, config=config)
                                char_text = char_text.strip().replace(' ', '').replace('\n', '').upper()
                                char_text = ''.join(c for c in char_text if c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
                                
                                if char_text:
                                    char_results.append(char_text[0])  # 只取第一个字符
                                else:
                                    char_results.append('?')
                            else:
                                char_results.append('?')
                        
                        segmented_result = ''.join(char_results)
                        if segmented_result and '?' not in segmented_result:
                            results.append((segmented_result, '字符分割识别'))
                            print(f"字符分割识别结果: {segmented_result}")
                except Exception as e:
                    print(f"字符分割识别失败: {str(e)}")
            
            # 选择最佳结果
            if results:
                # 优先选择长度合理的结果（4-6个字符）
                best_result = None
                for text, desc in results:
                    if 3 <= len(text) <= 6:
                        best_result = text
                        print(f"选择结果: {text} (来源: {desc})")
                        break
                
                # 如果没有长度合理的，选择最长的
                if not best_result:
                    best_result = max(results, key=lambda x: len(x[0]))[0]
                    print(f"选择最长结果: {best_result}")
                
                return best_result
            else:
                raise Exception("所有识别策略都失败了，无法识别验证码")
                
        except pytesseract.TesseractNotFoundError:
            raise Exception("未找到Tesseract OCR。请安装Tesseract并配置路径。Windows用户需要在代码中设置tesseract_cmd路径。")
        except Exception as e:
            raise Exception(f"Tesseract识别时出错: {str(e)}")

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
        
        if not characters:
            raise Exception("无法分割字符，请检查验证码图像")

        # 转换为绝对路径
        if not os.path.isabs(template_folder):
            # 如果是相对路径，尝试从当前工作目录和脚本目录查找
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            template_folder = os.path.join(base_dir, template_folder)
        
        # 检查模板文件夹
        if not os.path.exists(template_folder):
            raise Exception(f"模板文件夹不存在: {template_folder}。请先创建模板文件夹并添加字符模板文件。")

        # 加载模板
        templates = {}
        try:
            template_files = [f for f in os.listdir(template_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        except Exception as e:
            raise Exception(f"无法读取模板文件夹: {template_folder}，错误: {str(e)}")
        
        if not template_files:
            raise Exception(f"模板文件夹为空: {template_folder}。请添加字符模板文件（文件名格式：A.png, B.png等）。")
        
        print(f"找到 {len(template_files)} 个模板文件: {', '.join(template_files[:10])}")
        
        for filename in template_files:
            char = filename[0].upper()  # 假设文件名第一个字符是模板字符
            template_path = os.path.join(template_folder, filename)
            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                print(f"警告: 无法加载模板文件 {template_path}")
                continue
            _, template = cv2.threshold(template, 128, 255, cv2.THRESH_BINARY)
            templates[char] = template
            print(f"加载模板: {char} <- {filename}")

        if not templates:
            raise Exception(f"无法加载模板文件，请检查模板文件格式是否正确。已尝试加载 {len(template_files)} 个文件，但都失败了。")
        
        print(f"成功加载 {len(templates)} 个模板: {', '.join(sorted(templates.keys()))}")

        recognized_text = ""

        # 对每个字符进行模板匹配
        for char_img in characters:
            best_match = None
            best_score = -1

            for char, template in templates.items():
                # 调整模板大小以匹配字符
                if char_img.shape[0] > 0 and char_img.shape[1] > 0:
                    try:
                        resized_template = cv2.resize(template, (char_img.shape[1], char_img.shape[0]))

                        # 模板匹配
                        result = cv2.matchTemplate(char_img, resized_template, cv2.TM_CCOEFF_NORMED)
                        score = cv2.minMaxLoc(result)[1]

                        if score > best_score:
                            best_score = score
                            best_match = char
                    except Exception:
                        continue

            # 如果找到匹配，添加到结果
            if best_match and best_score > 0.5:
                recognized_text += best_match
            else:
                recognized_text += "?"

        if not recognized_text or recognized_text == "?" * len(characters):
            raise Exception("模板匹配失败，未找到合适的匹配。请检查模板文件是否与验证码字符样式匹配。")

        return recognized_text