import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from captcha_generator.generator import CaptchaGenerator
from captcha_recognizer.traditional_recognizer import TraditionalCaptchaRecognizer
from utils.utils import validate_captcha


def test_generator():
    """测试验证码生成器"""
    print("=== 测试验证码生成器 ===")

    generator = CaptchaGenerator()

    # 测试简单验证码
    text, image = generator.generate_simple_captcha(4)
    print(f"简单验证码: {text}")
    image.save('test_simple.png')

    # 测试中等验证码
    text, image = generator.generate_medium_captcha(5)
    print(f"中等验证码: {text}")
    image.save('test_medium.png')

    # 测试困难验证码
    text, image = generator.generate_hard_captcha(6)
    print(f"困难验证码: {text}")
    image.save('test_hard.png')

    print("验证码图片已保存到当前目录")


def test_recognizer():
    """测试验证码识别器"""
    print("\n=== 测试验证码识别器 ===")

    recognizer = TraditionalCaptchaRecognizer()

    # 使用生成的验证码测试
    test_files = ['test_simple.png', 'test_medium.png', 'test_hard.png']

    for file in test_files:
        if os.path.exists(file):
            result = recognizer.recognize_with_tesseract(file)
            print(f"{file}: 识别结果 = {result}")
        else:
            print(f"{file}: 文件不存在")


def test_validation():
    """测试验证功能"""
    print("\n=== 测试验证功能 ===")

    # 测试验证函数
    test_cases = [
        ("ABCD", "ABCD", True, "完全匹配"),
        ("abcd", "ABCD", False, "大小写不匹配（区分大小写）"),
        ("1234", "1234", True, "数字匹配"),
        ("ABCD", "ABCE", False, "部分匹配错误"),
        ("", "ABCD", False, "空输入"),
    ]

    for user_input, captcha, expected_success, description in test_cases:
        success, message = validate_captcha(user_input, captcha, case_sensitive=True)
        status = "通过" if (success == expected_success) else "失败"
        print(f"{description}: {status} - {message}")


def test_batch_generation():
    """测试批量生成"""
    print("\n=== 测试批量生成 ===")

    generator = CaptchaGenerator()
    count = 5

    print(f"批量生成 {count} 个中等难度验证码:")
    batch = generator.batch_generate(count, 'medium', 5)

    for i, (text, image) in enumerate(batch, 1):
        print(f"  {i:2d}. {text}")
        image.save(f'batch_{i:02d}.png')

    print(f"已保存 {count} 个验证码图片")


if __name__ == "__main__":
    print("开始测试验证码系统...")

    # 运行所有测试
    test_generator()
    test_recognizer()
    test_validation()
    test_batch_generation()

    print("\n所有测试完成!")