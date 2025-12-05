from flask import Flask, render_template
from flask_sock import Sock
from datetime import datetime
import json
import websocket

from user import User
from system import System
from problem_solver import ProblemSolver

app = Flask(__name__, template_folder="templates")
app.config["SECRET_KEY"] = "change_this_secret_key"

# WebSocket-расширение
sock = Sock(app)

# Твои игровые объекты (как в main.py)
user = User("Пользователь")
system = System()
problem_solver = ProblemSolver()

# Общая история чата (для простоты — в памяти процесса)
history = []  # элементы: {"role": "user"/"system", "text": "...", "time": "HH:MM:SS"}

GAME_WS_URL = "ws://localhost:8765"


def send_command_to_game(nlp_data):
    """
    Returns:
    - "OK" if sent
    - "CONNECT_ERROR" if connection failed
    - "INVALID_CMD" if NLP intent/entity didn't map to a game command
    """
    intent, direction_ru = nlp_data[0], nlp_data[1]

    # Extended map to handle cases from data.json better
    direction_map = {
        'вверх': 'up', 'выше': 'up', 'наверх': 'up',
        'вниз': 'down', 'ниже': 'down',
        'влево': 'left', 'налево': 'left',
        'вправо': 'right', 'направо': 'right'
    }

    direction_eng = direction_map.get(direction_ru)
    command = {}

    if intent == 'movement' and direction_eng:
        command = {"action": "move", "direction": direction_eng}

    elif intent == 'dash' and direction_eng:
        command = {"action": "dash", "direction": direction_eng}

    elif intent == 'attack' and direction_eng:
        command = {"action": "attack_sword", "direction": direction_eng}

    elif intent == 'shoot' and direction_eng:
        command = {"action": "attack_bow", "direction": direction_eng}

    elif intent == 'heal':
        command = {"action": "use_item", "item_type": "health"}

    elif intent == 'reset':
        command = {"action": "reset"}

    elif intent == 'greeting':
        return "OK"  # No game command needed

    elif intent == 'unknown':
        return "INVALID_CMD"

    else:
        # If intent requires direction but it's missing (e.g. "attack" without "up")
        if intent in ['movement', 'attack', 'shoot', 'dash'] and not direction_eng:
            return "INVALID_CMD"

    if command:
        try:
            ws = websocket.create_connection(GAME_WS_URL, timeout=0.5)
            payload = {
                "type": "game_command",
                "command": command
            }
            ws.send(json.dumps(payload))
            ws.close()
            return "OK"
        except Exception as e:
            print(f"Connection Error: {e}")
            return "CONNECT_ERROR"

    return "INVALID_CMD"


def now_time():
    return datetime.now().strftime("%H:%M:%S")


# Стартовое приветствие от системы — как в main.py через system.greating_message()
greeting = system.greating_message()
user.history.append(greeting)
history.append({
    "role": "system",
    "text": greeting,
    "time": now_time(),
})


@app.route("/")
def index():
    # Отрисовываем начальную страницу, history пробрасываем только для первой загрузки.
    return render_template("chat.html", history=history)


@sock.route("/ws")
def ws_chat(ws):
    """
    Обработчик WebSocket-соединения.
    На каждый подключившийся браузер — отдельный цикл while True.
    """
    # При подключении сразу отправляем клиенту всю историю
    ws.send(json.dumps({
        "type": "history",
        "messages": history,
    }, ensure_ascii=False))

    # Основной цикл обмена
    while True:
        data = ws.receive()
        if data is None:
            # Клиент отключился
            break

        try:
            payload = json.loads(data)
        except Exception:
            # Неверный формат — игнорируем
            continue

        text = str(payload.get("text", "")).strip()
        if not text:
            continue

        # === Сообщение пользователя ===
        send_time = now_time()
        user_msg = {
            "role": "user",
            "text": text,
            "time": send_time,
        }
        history.append(user_msg)

        # Эхо-посылка сообщения пользователя клиенту (чтобы не ждать ответа системы)
        ws.send(json.dumps({
            "type": "message",
            "message": user_msg,
        }, ensure_ascii=False))

        # === Генерация ответа системы (как в main.py) ===
        # === Генерация ответа системы (как в main.py) ===
        if text == "стоп игра":
            reply_text = "Игра остановлена. Обнови страницу, чтобы начать заново."
        else:
            # 1. Классификация
            data_for_solver = problem_solver.classify_message(text)

            # 2. Попытка отправить команду в игру
            # Используем system.answer для нормализации данных перед отправкой, если нужно,
            # но пока берем сырые данные из solver'а, так как там русский текст

            status = send_command_to_game(data_for_solver)

            # 3. Формирование текстового ответа
            reply_text = problem_solver.ask_message(data_for_solver)

            if status == "CONNECT_ERROR":
                reply_text += " [Ошибка: Игра не запущена или недоступна]"
            elif status == "INVALID_CMD" and data_for_solver[0] in ['movement', 'fight', 'jerk']:
                # Optional: Hint the user if we recognized intent but not direction
                pass

            user.history.append(reply_text)

        reply_time = now_time()
        system_msg = {
            "role": "system",
            "text": reply_text,
            "time": reply_time,
        }
        history.append(system_msg)

        # Отправляем ответ системы
        ws.send(json.dumps({
            "type": "message",
            "message": system_msg,
        }, ensure_ascii=False))


if __name__ == "__main__":
    # Обычный dev-сервер Flask, WebSocket работает через flask-sock + simple-websocket
    app.run(host="127.0.0.1", port=8000, debug=True)
