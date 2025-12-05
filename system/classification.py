from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import train_test_split
import json

# Чтение данных из JSON файла
with open('data.json', 'r', encoding='utf-8') as file:
    json_data = json.load(file)

# Преобразование данных в нужный формат
data = []
for intent, directions in json_data.items():
    for direction, phrases in directions.items():
        for phrase in phrases:
            data.append((phrase['phrase'], intent))  # Используем только намерение

# Пример вывода результата
for item in data:
    print(item)

# Разделим данные на сообщения и метки
messages, labels = zip(*data)

# Разделим данные на обучающую и тестовую выборки
X_train, X_test, y_train, y_test = train_test_split(messages, labels, test_size=0.2, random_state=42)

# Создаем модель
model = make_pipeline(CountVectorizer(), MultinomialNB())

# Обучаем модель
model.fit(X_train, y_train)

# Оценка модели
accuracy = model.score(X_test, y_test)
print(f"Точность: {accuracy:.2f}")

# Пример классификации новых сообщений
new_messages = [
    "подняться выше",
    "спуститься вниз",
    "пойти налево",
    "двигаться вправо",
    "рывок вверх",
    "рывок налево",
    "возьми меч",
    "ударь вверх"
]

predictions = model.predict(new_messages)
for message in new_messages:
    predicted_intent = model.predict([message])[0]
    entity = message.split()[-1]  # Предполагается, что сущность - это последнее слово
    print(f"Сообщение: '{message}' -> Намерение: '{predicted_intent}', Сущность: '{entity}'")