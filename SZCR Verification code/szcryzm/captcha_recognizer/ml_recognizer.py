import numpy as np
import os
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pickle
import cv2


class MLCaptchaRecognizer:
    def __init__(self, model_type='knn'):
        """
        初始化机器学习识别器
        :param model_type: 模型类型 ('knn', 'svm', 'random_forest')
        """
        self.model_type = model_type
        self.model = None
        self.characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        self.char_to_index = {char: i for i, char in enumerate(self.characters)}
        self.index_to_char = {i: char for i, char in enumerate(self.characters)}

    def extract_features(self, image):
        """
        从图像中提取特征
        :param image: 灰度图像
        :return: 特征向量
        """
        # 确保是灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # 调整大小
        resized = cv2.resize(gray, (20, 20))

        # 展平为特征向量
        features = resized.flatten() / 255.0  # 归一化

        return features

    def load_dataset(self, dataset_path='data/dataset'):
        """
        加载数据集
        :param dataset_path: 数据集路径
        :return: 特征和标签
        """
        features = []
        labels = []

        if not os.path.exists(dataset_path):
            print(f"数据集路径不存在: {dataset_path}")
            return np.array(features), np.array(labels)

        # 遍历所有子文件夹（每个文件夹对应一个字符）
        for char in self.characters:
            char_folder = os.path.join(dataset_path, char)

            if os.path.exists(char_folder):
                for filename in os.listdir(char_folder):
                    if filename.endswith('.png') or filename.endswith('.jpg'):
                        # 加载图像
                        img_path = os.path.join(char_folder, filename)
                        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

                        # 提取特征
                        feature = self.extract_features(img)
                        features.append(feature)
                        labels.append(self.char_to_index[char])

        return np.array(features), np.array(labels)

    def train(self, dataset_path='data/dataset', save_model=True):
        """
        训练模型
        :param dataset_path: 数据集路径
        :param save_model: 是否保存模型
        :return: 训练准确率
        """
        # 加载数据集
        X, y = self.load_dataset(dataset_path)

        if len(X) == 0:
            print("没有找到训练数据")
            return 0

        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # 创建模型
        if self.model_type == 'knn':
            self.model = KNeighborsClassifier(n_neighbors=3)
        elif self.model_type == 'svm':
            self.model = SVC(kernel='linear', probability=True)
        elif self.model_type == 'random_forest':
            self.model = RandomForestClassifier(n_estimators=100)
        else:
            raise ValueError(f"不支持的模型类型: {self.model_type}")

        # 训练模型
        self.model.fit(X_train, y_train)

        # 评估模型
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        print(f"模型训练完成，测试集准确率: {accuracy:.2%}")

        # 保存模型
        if save_model:
            model_dir = 'data/models'
            os.makedirs(model_dir, exist_ok=True)
            model_path = os.path.join(model_dir, f'{self.model_type}_model.pkl')
            with open(model_path, 'wb') as f:
                pickle.dump(self.model, f)
            print(f"模型已保存到: {model_path}")

        return accuracy

    def load_model(self, model_path=None):
        """
        加载已训练的模型
        :param model_path: 模型文件路径
        """
        if model_path is None:
            model_path = f'data/models/{self.model_type}_model.pkl'

        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            print(f"模型已从 {model_path} 加载")
            return True
        else:
            print(f"模型文件不存在: {model_path}")
            return False

    def predict(self, image):
        """
        识别验证码
        :param image: 图像
        :return: 识别结果
        """
        if self.model is None:
            print("模型未加载，请先训练或加载模型")
            return ""

        # 预处理图像
        if isinstance(image, str):
            img = cv2.imread(image)
        else:
            img = image

        # 分割字符
        from captcha_recognizer.traditional_recognizer import TraditionalCaptchaRecognizer
        recognizer = TraditionalCaptchaRecognizer()
        processed = recognizer.preprocess_image(img)
        characters, _ = recognizer.segment_characters(processed)

        # 如果没有分割到字符，返回空字符串
        if not characters:
            print("警告：无法分割字符")
            return ""

        # 识别每个字符
        result = ""
        for char_img in characters:
            try:
                # 提取特征
                features = self.extract_features(char_img).reshape(1, -1)

                # 预测
                prediction = self.model.predict(features)[0]
                char = self.index_to_char[prediction]
                result += char
            except Exception as e:
                print(f"识别字符时出错: {e}")
                result += "?"

        return result