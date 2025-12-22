import json
import random
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import make_pipeline
from nltk.stem.snowball import RussianStemmer


class ProblemSolver:
    def __init__(self, data_path="data.json", responses_path="responses.json"):
        self.stemmer = RussianStemmer()

        with open(data_path, "r", encoding="utf-8") as file:
            json_data = json.load(file)

        with open(responses_path, "r", encoding="utf-8") as file:
            self.responses = json.load(file)

        self.entity_roots = {}
        raw_data = []

        # 1. Сбор данных и сущностей
        for intent, subcats in json_data.items():
            for subcat, phrases in subcats.items():
                for entry in phrases:
                    phrase = entry["phrase"].lower()
                    raw_data.append((phrase, intent))

                    # Сохраняем корни сущностей для поиска
                    full_entity = entry.get("entity", "").lower()
                    if full_entity:
                        root = self.stemmer.stem(full_entity)
                        self.entity_roots[root] = full_entity

        # 2. Аугментация данных (Увеличение выборки)
        # Мы добавляем "шумовые" слова, чтобы модель лучше понимала контекст
        augmented_data = self._augment_data(raw_data)

        # Объединяем оригинальные и сгенерированные данные
        final_data = raw_data + augmented_data

        messages, labels = zip(*final_data)

        # 3. Обучение
        # Используем char_wb и ngram 2-5. Это позволяет ловить корни слов и игнорировать окончания.
        # Например: "атак" найдется и в "атака", и в "атакуй", и в "атаковать"
        X_train, X_test, y_train, y_test = train_test_split(
            messages, labels, test_size=0.1, random_state=42, stratify=labels
        )

        vectorizer = TfidfVectorizer(
            analyzer='char_wb',
            ngram_range=(2, 5),  # Смотрим на куски слов от 2 до 5 букв
            min_df=1  # Учитываем даже редкие слова
        )

        base_svc = LinearSVC(C=1.5, random_state=42, tol=1e-4, max_iter=5000)

        self.model = make_pipeline(
            vectorizer,
            CalibratedClassifierCV(base_svc, cv=3)
        )

        self.model.fit(X_train, y_train)

        # Вывод точности на тестовой выборке
        acc = self.model.score(X_test, y_test)
        print(f"Система обучена. Точность (Accuracy): {acc:.2%}")
        print(f"Размер обучающей выборки: {len(messages)} фраз")

        # Переобучаем на всех данных для продакшна
        self.model.fit(messages, labels)

    def _augment_data(self, data):
        """Генерирует новые фразы, добавляя вводные слова."""
        noise_words = [
            "быстро", "пожалуйста", "ну", "давай", "хочу", "можешь", "сейчас", "срочно", "прошу"
        ]
        augmented = []
        for phrase, label in data:
            # Добавляем случайное слово в начало
            for _ in range(2):  # Генерируем по 2 вариации на каждую фразу
                noise = random.choice(noise_words)
                new_phrase = f"{noise} {phrase}"
                augmented.append((new_phrase, label))
        return augmented

    def classify_message(self, message):
        message_lower = message.lower()

        # Предсказание
        probs = self.model.predict_proba([message_lower])[0]
        max_prob = np.max(probs)
        predicted_intent = self.model.classes_[np.argmax(probs)]

        # Порог уверенности
        if max_prob < 0.25:
            return ["unknown", ""]

        # Извлечение сущности (через стемминг + прямой поиск)
        entity = ""
        # 1. Поиск по корням (надежнее)
        words = "".join([c for c in message_lower if c.isalnum() or c.isspace()]).split()
        for word in words:
            word_root = self.stemmer.stem(word)
            if word_root in self.entity_roots:
                entity = self.entity_roots[word_root]
                break

        # 2. Поиск по прямому вхождению корня в текст (если слова склеились или сложные)
        if not entity:
            for root, full_name in self.entity_roots.items():
                if root in message_lower:
                    entity = full_name
                    break

        return [str(predicted_intent), entity]

    def ask_message(self, classification_data):
        intent, entity = classification_data[0], classification_data[1]
        phrases = self.responses.get(intent, self.responses["unknown"])
        response_template = random.choice(phrases)
        display_entity = entity if entity else ""
        return response_template.format(entity=display_entity).strip()
