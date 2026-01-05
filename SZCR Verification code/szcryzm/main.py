import os
import sys
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from captcha_generator.generator import CaptchaGenerator
from captcha_recognizer.traditional_recognizer import TraditionalCaptchaRecognizer
from captcha_recognizer.ml_recognizer import MLCaptchaRecognizer
from utils.utils import HistoryManager, display_image, validate_captcha


class CaptchaSystem:
    """验证码生成与识别系统"""

    def __init__(self):
        """初始化系统"""
        self.generator = CaptchaGenerator()
        self.traditional_recognizer = TraditionalCaptchaRecognizer()
        self.ml_recognizer = MLCaptchaRecognizer()
        self.history_manager = HistoryManager()
        self.current_captcha = None
        self.current_captcha_text = None

    def display_menu(self):
        """显示主菜单"""
        print("\n" + "=" * 50)
        print("        验证码生成与识别系统")
        print("=" * 50)
        print("1. 生成验证码")
        print("2. 识别验证码")
        print("3. 批量生成验证码")
        print("4. 验证验证码")
        print("5. 查看历史记录")
        print("6. 查看统计信息")
        print("7. 训练机器学习模型")
        print("8. 清空历史记录")
        print("0. 退出系统")
        print("=" * 50)

    def generate_captcha_menu(self):
        """生成验证码菜单"""
        print("\n--- 生成验证码 ---")
        print("1. 简单验证码")
        print("2. 中等验证码")
        print("3. 困难验证码")
        print("4. 返回主菜单")

        choice = input("请选择难度: ").strip()

        if choice == '1':
            difficulty = 'simple'
            length = 4
        elif choice == '2':
            difficulty = 'medium'
            length = 5
        elif choice == '3':
            difficulty = 'hard'
            length = 6
        elif choice == '4':
            return
        else:
            print("无效选择，返回主菜单")
            return

        # 生成验证码
        if difficulty == 'simple':
            self.current_captcha_text, self.current_captcha = self.generator.generate_simple_captcha(length)
        elif difficulty == 'medium':
            self.current_captcha_text, self.current_captcha = self.generator.generate_medium_captcha(length)
        elif difficulty == 'hard':
            self.current_captcha_text, self.current_captcha = self.generator.generate_hard_captcha(length)

        print(f"\n生成的验证码: {self.current_captcha_text}")
        print(f"难度: {difficulty}, 长度: {length}")

        # 显示验证码
        display_image(self.current_captcha, f"{difficulty.capitalize()} 验证码")

        # 保存验证码
        save_choice = input("是否保存验证码图片? (y/n): ").strip().lower()
        if save_choice == 'y':
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"captcha_{difficulty}_{timestamp}.png"
            self.generator.save_captcha(self.current_captcha, filename)

    def recognize_captcha_menu(self):
        """识别验证码菜单"""
        if self.current_captcha is None:
            print("\n当前没有验证码，请先生成验证码")
            return

        print("\n--- 识别验证码 ---")
        print("1. 使用传统方法识别 (Tesseract OCR)")
        print("2. 使用传统方法识别 (模板匹配)")
        print("3. 使用机器学习识别 (需要先训练模型)")
        print("4. 返回主菜单")

        choice = input("请选择识别方法: ").strip()

        if choice == '1':
            method = "tesseract"
            result = self.traditional_recognizer.recognize_with_tesseract(self.current_captcha)
        elif choice == '2':
            method = "template_matching"
            result = self.traditional_recognizer.recognize_with_template_matching(self.current_captcha)
        elif choice == '3':
            method = "machine_learning"
            if not self.ml_recognizer.load_model():
                train_choice = input("模型未找到，是否现在训练? (y/n): ").strip().lower()
                if train_choice == 'y':
                    self.train_model_menu()
                    if self.ml_recognizer.model is None:
                        print("训练失败，无法使用机器学习识别")
                        return
                else:
                    print("无法使用机器学习识别")
                    return
            result = self.ml_recognizer.predict(self.current_captcha)
        elif choice == '4':
            return
        else:
            print("无效选择，返回主菜单")
            return

        print(f"\n识别结果: {result}")
        print(f"实际验证码: {self.current_captcha_text}")

        # 验证结果
        success = (result == self.current_captcha_text)
        if success:
            print("✓ 识别正确!")
        else:
            print("✗ 识别错误!")

        # 添加到历史记录
        self.history_manager.add_record(
            self.current_captcha_text,
            result,
            'unknown',  # 这里可以修改为实际难度
            method,
            success
        )

    def batch_generate_menu(self):
        """批量生成验证码菜单"""
        print("\n--- 批量生成验证码 ---")

        # 获取参数
        try:
            count = int(input("请输入生成数量 (默认10): ") or "10")
            length = int(input("请输入验证码长度 (默认5): ") or "5")
        except ValueError:
            print("输入无效，使用默认值")
            count = 10
            length = 5

        print("\n选择难度:")
        print("1. 简单")
        print("2. 中等")
        print("3. 困难")
        difficulty_choice = input("请选择: ").strip()

        if difficulty_choice == '1':
            difficulty = 'simple'
        elif difficulty_choice == '2':
            difficulty = 'medium'
        elif difficulty_choice == '3':
            difficulty = 'hard'
        else:
            print("无效选择，使用中等难度")
            difficulty = 'medium'

        # 创建保存文件夹
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder = f"data/batch_{difficulty}_{timestamp}"
        os.makedirs(folder, exist_ok=True)

        # 批量生成
        print(f"\n开始批量生成 {count} 个验证码...")
        batch_gen = self.generator.batch_generate(count, difficulty, length)

        success_count = 0
        for i, (text, image) in enumerate(batch_gen, 1):
            # 保存验证码
            filename = f"captcha_{i:03d}_{text}.png"
            filepath = os.path.join(folder, filename)
            image.save(filepath)
            success_count += 1

            # 显示进度
            if i % 10 == 0 or i == count:
                print(f"已生成 {i}/{count} 个验证码")

        print(f"\n批量生成完成!")
        print(f"成功生成: {success_count} 个验证码")
        print(f"保存位置: {folder}")

    def validate_captcha_menu(self):
        """验证验证码菜单"""
        if self.current_captcha is None:
            print("\n当前没有验证码，请先生成验证码")
            return

        print("\n--- 验证验证码 ---")
        print(f"当前验证码已生成，请查看图片")

        user_input = input("请输入您看到的验证码: ").strip()

        # 验证
        success, message = validate_captcha(user_input, self.current_captcha_text)

        print(f"\n{message}")

        # 添加到历史记录
        self.history_manager.add_record(
            self.current_captcha_text,
            user_input,
            'user_input',
            'manual',
            success
        )

    def view_history_menu(self):
        """查看历史记录菜单"""
        history = self.history_manager.history

        if not history:
            print("\n暂无历史记录")
            return

        print("\n--- 历史记录 ---")
        print(f"总计: {len(history)} 条记录")
        print("-" * 80)

        for i, record in enumerate(history[-10:], 1):  # 显示最近10条
            status = "✓" if record['success'] else "✗"
            print(f"{i:2d}. [{record['timestamp']}]")
            print(f"    验证码: {record['captcha']}, 识别: {record['recognized']}")
            print(f"    方法: {record['method']}, 难度: {record['difficulty']}, 状态: {status}")
            print("-" * 80)

    def view_statistics_menu(self):
        """查看统计信息菜单"""
        stats = self.history_manager.get_statistics()

        print("\n--- 统计信息 ---")
        print(f"总验证次数: {stats['total']}")
        print(f"成功次数: {stats['success']}")
        print(f"总体准确率: {stats['accuracy']:.2%}")

        if stats['by_difficulty']:
            print("\n按难度统计:")
            for diff, diff_stats in stats['by_difficulty'].items():
                print(f"  {diff}: {diff_stats['success']}/{diff_stats['total']} = {diff_stats['accuracy']:.2%}")

        if stats['by_method']:
            print("\n按方法统计:")
            for method, method_stats in stats['by_method'].items():
                print(f"  {method}: {method_stats['success']}/{method_stats['total']} = {method_stats['accuracy']:.2%}")

    def train_model_menu(self):
        """训练机器学习模型菜单"""
        print("\n--- 训练机器学习模型 ---")

        # 检查数据集
        dataset_path = 'data/dataset'
        if not os.path.exists(dataset_path):
            print(f"数据集路径不存在: {dataset_path}")
            print("请先创建数据集，每个字符一个文件夹，包含该字符的多个样本图片")
            return

        print("选择模型类型:")
        print("1. K近邻 (KNN)")
        print("2. 支持向量机 (SVM)")
        print("3. 随机森林 (Random Forest)")

        choice = input("请选择: ").strip()

        if choice == '1':
            model_type = 'knn'
        elif choice == '2':
            model_type = 'svm'
        elif choice == '3':
            model_type = 'random_forest'
        else:
            print("无效选择，使用KNN")
            model_type = 'knn'

        # 创建识别器并训练
        self.ml_recognizer = MLCaptchaRecognizer(model_type)
        accuracy = self.ml_recognizer.train(dataset_path)

        if accuracy > 0:
            print(f"\n训练完成，准确率: {accuracy:.2%}")
            print("模型已保存，可以在识别时使用")
        else:
            print("\n训练失败，请检查数据集")

    def run(self):
        """运行主程序"""
        print("欢迎使用验证码生成与识别系统!")

        while True:
            self.display_menu()
            choice = input("请选择操作 (0-8): ").strip()

            if choice == '0':
                print("感谢使用，再见!")
                break
            elif choice == '1':
                self.generate_captcha_menu()
            elif choice == '2':
                self.recognize_captcha_menu()
            elif choice == '3':
                self.batch_generate_menu()
            elif choice == '4':
                self.validate_captcha_menu()
            elif choice == '5':
                self.view_history_menu()
            elif choice == '6':
                self.view_statistics_menu()
            elif choice == '7':
                self.train_model_menu()
            elif choice == '8':
                confirm = input("确定要清空所有历史记录吗? (y/n): ").strip().lower()
                if confirm == 'y':
                    self.history_manager.clear_history()
            else:
                print("无效选择，请重新输入")

            input("\n按Enter键继续...")


if __name__ == "__main__":
    # 创建必要的目录
    os.makedirs('data/captchas', exist_ok=True)
    os.makedirs('data/models', exist_ok=True)
    os.makedirs('data/templates', exist_ok=True)

    # 检查是否使用命令行模式
    if len(sys.argv) > 1 and sys.argv[1] == '--cli':
        # 命令行模式
        system = CaptchaSystem()
        system.run()
    else:
        # 默认使用GUI模式
        try:
            from gui_main import main as gui_main
            gui_main()
        except ImportError as e:
            print(f"无法导入GUI模块: {e}")
            print("使用命令行模式...")
            system = CaptchaSystem()
            system.run()