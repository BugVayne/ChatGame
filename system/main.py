from user import User
from system import System
from problem_solver import ProblemSolver


def studying(user, system, problem_solver):
    user.history.append(system.greating_message())
    message_from_user = input()
    data = problem_solver.classify_message(message_from_user)
    while True:
        if data[0] == 'movement':
            r_message = "Супер! Теперь ты знаешь, как тебе передвигаться. Далее давай узнаем, что у тебя есть в инвентаре. Чтобы узнать, напиши 'инвентарь'"
            user.history.append(r_message)
            print(r_message)
            break
        else:
            r_message = "Попробуй еще раз!"
            message = input()
            data = problem_solver.classify_message(message)
            user.history.append(r_message)
            print(r_message)

    while True:
        message = input()
        if message == 'инвентарь':
            r_message = "В инвентаре у тебя меч! Супер. В следующий раз, как захочешь узнать, что у тебя инвентаре, напиши 'инвентарь'. Давай возьмем меч в руки и попробуем ударить! Просто напиши мне свое действие!"
            print(r_message)
            break
        else:
            r_message = "Попробуй еще!"
            print(r_message)
            user.history.append(r_message)
    user.history.append(r_message)
    while True:
        message = input()
        data = problem_solver.classify_message(message)
        if data[0] == 'act' and data[1] == 'меч':
            r_message = "Круто! Попробуй ударить в каком-нибудь направлении"
            user.history.append(r_message)
            print(r_message)
            break
        else:
            r_message = "Не сдавайся! У тебя получится!"
            user.history.append(r_message)
            print(r_message)
    while True:
        message = input()
        data = problem_solver.classify_message(message)
        print(data[0])
        if data[0] == 'fight':
            r_message = "Ура! Теперь ты знаешь, как тебе спасаться от врагов."
            user.history.append(r_message)
            print(r_message)
            break
        else:
            r_message = "Попробуй еще раз."
            user.history.append(r_message)
            print(r_message)
    r_message = "Что ж, пора опробовать себя в деле. Постарайся дойти до конца этой комнаты, чтобы узнать, что дальше:)"
    user.history.append(r_message)
    print(r_message)


def main():
    user = User("Пользователь")
    print(f"Инициализирован пользователь: {user.name}")
    system = System()
    problem_solver = ProblemSolver()
    studying(user, system, problem_solver)
    message = input()
    while message != 'стоп игра':
        data = problem_solver.classify_message(message)
        r_message = problem_solver.ask_message(data)
        user.history.append(r_message)
        print(r_message)
        message = input()


if __name__ == "__main__":
    main()
