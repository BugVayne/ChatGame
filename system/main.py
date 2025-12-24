from user import User
from system import System
from problem_solver import ProblemSolver

from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import datetime
import json
import websockets  # ВАЖНО: Добавлено
import os  # ВАЖНО: Добавлено

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

user = User("Пользователь")
game_system = System()
problem_solver = ProblemSolver()

# --- CONFIG ---
GAME_HOST = os.getenv("GAME_HOST", "localhost")
GAME_WS_URL = f"ws://{GAME_HOST}:8765"


# --------------

class StudyState:
    STEP_MOVEMENT = 0
    STEP_INVENTORY = 1
    STEP_EQUIP = 2
    STEP_FIGHT = 3
    COMPLETED = 4


study_status = StudyState.STEP_MOVEMENT


@app.get("/", response_class=HTMLResponse)
async def get_chat(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request, "history": user.history})


# --- ФУНКЦИЯ УПРАВЛЕНИЯ ИГРОЙ ---
async def send_command_to_game(nlp_data):
    intent, direction_ru = nlp_data[0], nlp_data[1]

    direction_map = {
        "вверх": "up", "выше": "up", "наверх": "up",
        "вниз": "down", "ниже": "down",
        "влево": "left", "налево": "left",
        "вправо": "right", "направо": "right",
    }
    direction_eng = direction_map.get(direction_ru)
    command = {}

    # Основные команды
    if intent == "movement" and direction_eng:
        command = {"action": "move", "direction": direction_eng}
    elif intent == "dash" and direction_eng:
        command = {"action": "dash", "direction": direction_eng}
    elif intent == "attack" and direction_eng:
        command = {"action": "attack_sword", "direction": direction_eng}
    elif intent == "shoot" and direction_eng:
        command = {"action": "attack_bow", "direction": direction_eng}
    elif intent == "heal":
        command = {"action": "use_item", "item_type": "health"}
    elif intent == "reset":
        command = {"action": "reset"}

    # Расширенные команды
    elif intent == "menu_control":
        if direction_ru in ["пауза", "открыть"]:
            command = {"action": "pause"}
        elif direction_ru in ["закрыть", "продолжить"]:
            command = {"action": "resume"}
    elif intent == "trade_interact":
        command = {"action": "interact_merchant"}
    elif intent == "shop_actions":
        if "хилка" in direction_ru:
            command = {"action": "buy_item", "item_index": 0}
        elif "стрела" in direction_ru:
            command = {"action": "buy_item", "item_index": 1}
    elif intent == "main_menu_navigation":
        if direction_ru in ["меню", "выход"]:
            command = {"action": "main_menu"}
        elif direction_ru in ["рестарт", "повтор"]:
            command = {"action": "retry"}

    if command:
        try:
            async with websockets.connect(GAME_WS_URL) as ws:
                payload = {"type": "game_command", "command": command}
                await ws.send(json.dumps(payload))
            return True
        except Exception as e:
            print(f"Game connection error: {e}")
    return False


# ---------------------------------

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global study_status
    await websocket.accept()

    if not user.history:
        welcome = game_system.greating_message()
        user.history.append({"role": "system", "text": welcome, "time": datetime.datetime.now().strftime("%H:%M:%S")})

    await websocket.send_json({"type": "history", "messages": user.history})

    try:
        while True:
            data = await websocket.receive_json()
            message_from_user = data.get("text", "").strip()

            if not message_from_user:
                continue

            # Классифицируем
            classification = problem_solver.classify_message(message_from_user)
            # Отправляем в игру
            await send_command_to_game(classification)

            user_msg = {
                "role": "user",
                "text": message_from_user,
                "time": datetime.datetime.now().strftime("%H:%M:%S")
            }
            user.history.append(user_msg)
            await websocket.send_json({"type": "message", "message": user_msg})

            response_text = ""

            if message_from_user.lower() == 'стоп игра':
                response_text = "Игра остановлена."

            elif study_status == StudyState.STEP_MOVEMENT:
                if classification[0] == 'movement':
                    response_text = "Супер! Теперь ты знаешь, как тебе передвигаться. Далее давай узнаем, что у тебя есть в инвентаре. Чтобы узнать, напиши 'инвентарь'"
                    study_status = StudyState.STEP_INVENTORY
                else:
                    response_text = "Попробуй еще раз! (Нужно действие движения)"

            elif study_status == StudyState.STEP_INVENTORY:
                if message_from_user.lower() == 'инвентарь':
                    response_text = "В инвентаре у тебя меч! Супер. Давай возьмем меч в руки и попробуем ударить! Просто напиши мне свое действие!"
                    study_status = StudyState.STEP_EQUIP
                else:
                    response_text = "Попробуй еще! Напиши 'инвентарь'"

            elif study_status == StudyState.STEP_EQUIP:
                if classification[0] == 'act' and classification[1] == 'меч':
                    response_text = "Круто! Попробуй ударить в каком-нибудь направлении"
                    study_status = StudyState.STEP_FIGHT
                else:
                    response_text = "Не сдавайся! У тебя получится! (Используй меч)"

            elif study_status == StudyState.STEP_FIGHT:
                if classification[0] == 'fight' or classification[0] == 'attack':  # Обработаем оба варианта
                    response_text = "Ура! Теперь ты знаешь, как тебе спасаться от врагов. Постарайся дойти до конца этой комнаты, чтобы узнать, что дальше:)"
                    study_status = StudyState.COMPLETED
                else:
                    response_text = "Попробуй еще раз. (Нужно действие боя)"

            else:
                response_text = problem_solver.ask_message(classification)

            system_msg = {
                "role": "system",
                "text": response_text,
                "time": datetime.datetime.now().strftime("%H:%M:%S")
            }
            user.history.append(system_msg)
            await websocket.send_json({"type": "message", "message": system_msg})

    except Exception as e:
        print(f"Ошибка WebSocket: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
