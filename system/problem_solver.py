import json
import random
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import make_pipeline
# Добавляем стеммер для русского языка
from nltk.stem.snowball import RussianStemmer


class ProblemSolver:
    def __init__(self, data_path="data.json", responses_path="responses.json"):
        # Инициализируем стеммер
        self.stemmer = RussianStemmer()

        with open(data_path, "r", encoding="utf-8") as file:
            json_data = json.load(file)

        with open(responses_path, "r", encoding="utf-8") as file:
            self.responses = json.load(file)

        data = []
        # Словарь вида {основа_слова: полное_название_сущности}
        # Например: {"хилк": "хилка", "стрел": "стрелы"}
        self.entity_roots = {}

        for intent, subcats in json_data.items():
            for subcat, phrases in subcats.items():
                for entry in phrases:
                    data.append((entry["phrase"].lower(), intent))

                    full_entity = entry.get("entity", "").lower()
                    if full_entity:
                        # Сохраняем основу сущности
                        # Если сущность "хилка", стеммер сделает "хилк"
                        root = self.stemmer.stem(full_entity)
                        self.entity_roots[root] = full_entity

        messages, labels = zip(*data)

        # Обучение модели (LinearSVC)
        X_train, X_test, y_train, y_test = train_test_split(
            messages, labels, test_size=0.2, random_state=42, stratify=labels
        )

        base_svc = LinearSVC(C=1.0, random_state=42, tol=1e-3, max_iter=2000)
        self.model = make_pipeline(
            TfidfVectorizer(ngram_range=(1, 2)),
            CalibratedClassifierCV(base_svc, cv=3)
        )

        self.model.fit(messages, labels)
        print(f"Система готова. База сущностей: {list(self.entity_roots.keys())}")

    def classify_message(self, message):
        message_lower = message.lower()

        # 1. Предсказание намерения
        probs = self.model.predict_proba([message_lower])[0]
        max_prob = np.max(probs)
        predicted_intent = self.model.classes_[np.argmax(probs)]

        if max_prob < 0.30:
            return ["unknown", ""]

        # 2. ИЗМЕНЕНО: Извлечение сущности через стемминг
        entity = ""
        # Очищаем сообщение от знаков препинания и разбиваем на слова
        words = "".join([c for c in message_lower if c.isalnum() or c.isspace()]).split()

        for word in words:
            word_root = self.stemmer.stem(word)  # "хилку" -> "хилк", "стрелами" -> "стрел"
            if word_root in self.entity_roots:
                entity = self.entity_roots[word_root]
                break

        # Запасной вариант: если стеммер не сработал, ищем прямое вхождение
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

        # Если сущность не найдена, а в шаблоне она нужна,
        # подставим пустую строку или "что-то"
        display_entity = entity if entity else ""
        return response_template.format(entity=display_entity).strip()