import asyncio
from aiogram.fsm.state import State, StatesGroup
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from os import getenv
from db_scripts import get_db_connection, create_users_table
import sys


# Здесь нужно задать переменную окружения "BOT_TOKEN" перед запуском скрипта

TOKEN = getenv("BOT_TOKEN")
if not TOKEN :
    print ("Please enter your token  in  the environment")
    sys.exit(1)

class GroupRegistration(StatesGroup):
    waiting_for_group_number = State()
    waiting_for_secret_token = State()




bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()


def make_row_keyboard(items: list[str]) -> ReplyKeyboardMarkup:
    """
    Создаёт реплай-клавиатуру с кнопками в один ряд
    :param items: список текстов для кнопок
    :return: объект реплай-клавиатуры
    """
    row = [KeyboardButton(text=item) for item in items]
    return ReplyKeyboardMarkup(keyboard=[row], resize_keyboard=True)


# Регистрация пользователя при начале работы с ботом
@router.message(CommandStart())
async def command_start_handler(message: types.Message):

    user_id = message.from_user.id
    full_name = message.from_user.full_name

    async with await get_db_connection() as db:
        # Проверяем, зарегистрирован ли уже пользователь

        cursor = await db.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
        user = await cursor.fetchone()

        if user:
            # Пользователь уже существует, можно обновить информацию или отправить приветственное сообщение
            await message.reply(f"Привет, {full_name}! Вы уже зарегистрированы как {user[0]}")

        else:
            # Регистрируем пользователя как студента
            await db.execute("INSERT INTO users (user_id, full_name, role) VALUES (?, ?, ?)", (user_id, full_name, "student"))
            await db.commit()
            await message.reply(f"Добро пожаловать, {full_name}! Вы зарегистрированы как студент. ")





# Команда для старосты, чтобы отправить уведомление всем студентам
@router.message(Command(commands="send_to_all"))
async def send_to_all_handler(message: types.Message):

    # Проверка, является ли пользователь старостой
    user_id = message.from_user.id
    async with await get_db_connection() as db:
        cursor = await db.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
        user_role = await cursor.fetchone()

        if user_role and user_role[0] == "prefect":
            # Отправка уведомления всем студентам
            cursor = await db.execute("SELECT user_id FROM users WHERE role = ?", ("student",))
            students = await cursor.fetchall()


            for student in students:
                try:
                    await bot.send_message(student[0], message.text[12:])  # Содержимое сообщения после '/send_to_all '
                except Exception as e:
                    print(f"Не удалось отправить сообщение пользователю {student[0]}: {e}")
                    

            await message.reply("Уведомление отправлено всем студентам")
        else:
            await message.reply("У вас нет прав для выполнения этой команды")






# Регистрация старосты (должен быть реализован безопасный механизм проверки)
@router.message(Command(commands="star_reg"))
async def register_as_prefect(message: types.Message):
    
    # Здесь должна быть логика проверки секретного кода...
    pass


dp.include_router(router)


async def main():
    await create_users_table()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())    