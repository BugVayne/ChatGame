import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC # Новая модель
from sklearn.pipeline import make_pipeline

# Чтение данных
with open("data.json", "r", encoding="utf-8") as file:
    json_data = json.load(file)

data = []
for intent, directions in json_data.items():
    for direction, phrases in directions.items():
        for phrase in phrases:
            data.append((phrase["phrase"], f"{intent}_{direction}"))

messages, labels = zip(*data)

# Увеличим random_state для стабильности на маленьких данных
X_train, X_test, y_train, y_test = train_test_split(
    messages, labels, test_size=0.2, random_state=42, stratify=labels
)

# Создаем продвинутую модель
# TfidfVectorizer сделает редкие слова (ударь, лети) более важными, чем частые (вверх, вниз)
model = make_pipeline(
    TfidfVectorizer(ngram_range=(1, 2)),
    LinearSVC(C=1.0, random_state=42)
)

model.fit(X_train, y_train)

accuracy = model.score(X_test, y_test)
print(f"Новая точность (LinearSVC): {accuracy:.2f}")

# Пример классификации
new_messages = ["атакуй вверх", "быстро прыгни влево", "купи зелье"]
for msg in new_messages:
    pred = model.predict([msg])[0]
    print(f"'{msg}' -> {pred}")