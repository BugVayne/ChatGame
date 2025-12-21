from user import User
from system import System
from problem_solver import ProblemSolver

from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import datetime
import json

app = FastAPI()

# Подключаем папку со статикой (картинки, стили)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# Инициализация игровых объектов
user = User("Пользователь")
game_system = System()
problem_solver = ProblemSolver()


# Глобальное состояние обучения для простоты (в идеале хранить в объекте user)
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


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global study_status
    await websocket.accept()

    # Отправляем начальное приветствие при подключении, если история пуста
    if not user.history:
        welcome = game_system.greating_message()
        user.history.append({"role": "system", "text": welcome, "time": datetime.datetime.now().strftime("%H:%M:%S")})

    # Отправляем текущую историю сообщений
    await websocket.send_json({"type": "history", "messages": user.history})

    try:
        while True:
            data = await websocket.receive_json()
            message_from_user = data.get("text", "").strip()

            if not message_from_user:
                continue

            # 1. Сохраняем сообщение пользователя
            user_msg = {
                "role": "user",
                "text": message_from_user,
                "time": datetime.datetime.now().strftime("%H:%M:%S")
            }
            user.history.append(user_msg)
            await websocket.send_json({"type": "message", "message": user_msg})

            # 2. Логика ответа (заменяет вашу функцию studing и цикл main)
            response_text = ""

            if message_from_user.lower() == 'стоп игра':
                response_text = "Игра остановлена."

            elif study_status == StudyState.STEP_MOVEMENT:
                classification = problem_solver.classify_message(message_from_user)
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
                classification = problem_solver.classify_message(message_from_user)
                if classification[0] == 'act' and classification[1] == 'меч':
                    response_text = "Круто! Попробуй ударить в каком-нибудь направлении"
                    study_status = StudyState.STEP_FIGHT
                else:
                    response_text = "Не сдавайся! У тебя получится! (Используй меч)"

            elif study_status == StudyState.STEP_FIGHT:
                classification = problem_solver.classify_message(message_from_user)
                if classification[0] == 'fight':
                    response_text = "Ура! Теперь ты знаешь, как тебе спасаться от врагов. Постарайся дойти до конца этой комнаты, чтобы узнать, что дальше:)"
                    study_status = StudyState.COMPLETED
                else:
                    response_text = "Попробуй еще раз. (Нужно действие боя)"

            else:
                # Основной игровой цикл после обучения
                classification = problem_solver.classify_message(message_from_user)
                response_text = problem_solver.ask_message(classification)

            # 3. Отправка ответа системы
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