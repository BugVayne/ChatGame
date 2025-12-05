import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import train_test_split
import json


class ProblemSolver:
    def __init__(self):
        with open('data.json', 'r', encoding='utf-8') as file:
            json_data = json.load(file)

        data = []
        self.known_entities = set()

        # Flatten data for training
        for intent, subcats in json_data.items():
            for subcat, phrases in subcats.items():
                for entry in phrases:
                    # Append phrase and intent pair
                    data.append((entry['phrase'], intent))

                    # Collect entities for extraction
                    ent = entry.get('entity', '').lower()
                    if ent:
                        self.known_entities.add(ent)

        messages, labels = zip(*data)

        # Use ALL data for training since dataset is small, but keep split for validation metric
        X_train, X_test, y_train, y_test = train_test_split(messages, labels, test_size=0.1, random_state=42)

        # TF-IDF with N-grams (1-2 words) to capture "attack up" vs "go up"
        self.model = make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), MultinomialNB(alpha=0.1))

        self.model.fit(X_train, y_train)
        print(f"Model accuracy on test set: {self.model.score(X_test, y_test):.2f}")

        # Refit on FULL dataset for better production performance
        self.model.fit(messages, labels)

    def classify_message(self, message):
        message_lower = message.lower()

        # 1. Predict Intent
        probabilities = self.model.predict_proba([message_lower])[0]
        max_prob = np.max(probabilities)
        predicted_index = np.argmax(probabilities)
        predicted_intent = self.model.classes_[predicted_index]

        # DEBUG PRINT: Show what model thinks
        print(f"DEBUG NLP: Msg='{message}' | Intent='{predicted_intent}' ({max_prob:.3f})")

        # Threshold for "I don't understand"
        if max_prob < 0.25:  # Lowered threshold slightly
            print("DEBUG NLP: Rejected by threshold")
            return ["unknown", ""]

        # 2. Extract Entity (Direction)
        entity = ""
        # Search for known entities in the message
        for known in self.known_entities:
            # Check strictly as a whole word
            if known in message_lower.split():
                entity = known
                break

        print(f"Message: '{message}' -> Intent: '{predicted_intent}' ({max_prob:.2f}), Entity: '{entity}'")
        return [str(predicted_intent), entity]

    @staticmethod
    def ask_message(data):
        intent, entity = data[0], data[1]

        if intent == 'unknown':
            return "Я не совсем понял команду. Попробуй 'иди вверх' или 'атака вниз'."
        if intent == 'greeting':
            return "Привет! Готов к приключениям?"
        if intent == 'fight':
            return f"Атакую мечом {entity}!"
        if intent == 'shoot':
            return f"Стреляю из лука {entity}!"
        if intent == 'movement':
            return f"Иду {entity}."
        if intent == 'dash':
            return f"Рывок {entity}!"
        if intent == 'heal':
            return "Пью зелье здоровья."
        if intent == 'reset':
            return "Перезапускаю уровень..."

        return "Команда принята."
