from aiogram import types, F, Router
from aiogram.types import Message, BotCommand
from aiogram.filters import Command

from db.models import SessionLocal, User, GroupMessage

from utilites.password_check import check_password
from config import admin_id

router = Router()

async def get_db():
    """
    Инициализирует подключение к бд
    """
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()







#/START  СТАРТОВОЕ СООБЩЕНИЕ
@router.message(Command("start"))
async def start_handler(msg: Message):
        """
        Стартовая комманда /start.
        """
        await msg.answer("""
                         
Вас приветствует Бот для помощи старостам в РГПУ им. Герцена!\n\n
Пожалуйста, выполните комманду /register для регистрации по такошу шаблону:

/register (Название вашей группы) (пароль, если вы староста)\n
Пример для студентов: /register ЭКО-22\n
Пример для старост: /register ЭКО-22 12345678\n\n
                         
Если вы хотите удалить себя из системы используйте /unregister         
                         
                         """)

#ПОКАЗЫВАЕТ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ
@router.message(Command("all"))
async def get_all_users_handler(msg: Message):
    """
    Отвечает за команду вызова всех пользователей /all
    Показывает всех зарегестрированных пользотелей, их группу и статус.
    """
    async with SessionLocal() as session:
        all_users = await User.get_all_users(session)
    if all_users:
        users_info = "\n".join([f"- ID: {user.id}, Группа: {user.group_name}, Староста: {'Да' if user.is_leader else 'Нет'}" for user in all_users])
        await msg.answer(f"Список всех пользователей:\n{users_info}")
    else:
        await msg.answer("Пользователей в системе пока нет.")

#КОМАНДА ДЛЯ РЕГИСТРАЦИИ
@router.message(Command("register"))
async def register_handler(msg: Message):
    """
    Отвечает за комманду регистрации /register. 
    Пользователь должен указать название группы.
    """
    args = msg.text.split()[1:]  # Получаем аргументы после команды
    if len(args):
        group = args[0] if args else ''
        
        # определяем leader 
        if len(args) > 1:
            is_leader = True if check_password(args[1]) else False
        else:
            is_leader = False
            
        user_id = msg.from_user.id

        # проверим, существует ли уже пользователь
        async with SessionLocal() as session:
            existing_user = await User.get_user_by_id(session, user_id)
        if existing_user:
            await msg.answer(f"Вы уже зарегистрированы.")
        else:
            async with SessionLocal() as session:
                await User.create_user(session, user_id, group, is_leader) #создание нового пользователя
                await msg.answer(f"Вы успешно зарегистрированы. Группа: {group}. Староста: {'Да' if is_leader else 'Нет'}")
    else:
        await msg.answer("""
                         
Пожалуйста, введите название вашей группы и пароль
(если вы староста, если вы просто студент, то ничего не вводите).
Регистрация не удалась. Пример сообщения для регистрации: 
/register ЭКО-22 12345678
                         
                         """)

#КОМАНДА ДЛЯ УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЯ ИЗ БД (ДЛЯ ПЕРЕРЕГИСТРАЦИИ)
@router.message(Command("unregister"))
async def unregister_handler(msg: types.Message):
    """
    Отвечает за команду удаления регистрации /unregister.
    Пользователь будет удалён из базы данных.
    """
    user_id = msg.from_user.id

    # Проверяем, существует ли уже пользователь
    async with SessionLocal() as session:
        existing_user = await User.get_user_by_id(session, user_id)
        if existing_user:
            # Если пользователь существует, удаляем его
                await User.delete_user(session, user_id)  # удаление пользователя из БД
                await msg.answer(f"Вы успешно удалены из базы данных.")
        else:
            await msg.answer("Вы не зарегистрированы.")

#КОМАНДА ДЛЯ ВЫЗОВА СООБЩЕНИЙ ДЛЯ ГРУППЫ
@router.message(Command("show_message"))
async def n_message(msg: types.Message):
    """"
    Отвечает за команду /show_message.
    Показывает список сообщений для группы.
    """
    async with SessionLocal() as session:
        group_name = await User._get_user_group_name(session, msg.from_user.id)
        group_messages = await GroupMessage.get_group_messages(session, group_name)
        if group_messages:
            await msg.answer(f"Список сообщений для группы: {GroupMessage.message}")
        else:
            await msg.answer(f"Сообщений для группы {group_name} пока нет.")


#TODO: хз че с ней не так, завтра переделать
# КОМАНДА ДЛЯ СОЗДАНИЯ СООБЩЕНИЯ ДЛЯ ГРУППЫ (ТОЛЬКО ДЛЯ СТАРОСТ)
@router.message(Command("create_message"))
async def create_message_handler(msg: types.Message):
    """
    Отвечает за комманду /create_message.
    Пользователь (если он староста) создает сообщение в группу.
    Сообщение отправляется всем участникам группы.
    """
    async with SessionLocal() as session:
        group_name = await User._get_user_group_name(session, msg.from_user.id)


        if User._is_leader(session, msg.from_user.id):
            
            message = ' '.join(msg.text.split()[1:])
            if len(message) > 0:
                await GroupMessage.delete_group_message(session, group_name)
                await GroupMessage.create_group_message(session, group_name, message)
                await msg.answer(f"Сообщение для группы {group_name} создано.")
            else:
                await msg.answer(f"Сообщение для группы {group_name} не создано. Вы не отправили сообщение.")
        else:

            await msg.answer(f"Сообщение для группы {group_name} не создано. У вас недостаточно прав для создания сообщения.")

#ДЛЯ ВЫЗОВА ВСЕХ КОМАНД (/HELP)
@router.message(Command("help"))
async def help(msg: types.Message):
    """
    Отвечает за команду /help.
    Показывает список команд.
    """
    await msg.answer("""
                         
Список команд:

/start - Стартовая команда.
/all - Отвечает за команду вызова всех пользователей.
/register - Отвечает за команду регистрации.
/unregister - Отвечает за команду удаления вас из системы регистрации.
/show_message - Отвечает за команду показ сообщений для группы.
/create_message - Отвечает за команду создания сообщений для группы (только для старост).

                    """)

#ДЛЯ СОЗДАНИЯ НОВОЙ ГРУППЫ (ТОЛЬКО ДЛЯ АДМИНИСТРАТОРОВ)   
@router.message(Command("new_group"))
async def new_group(msg: types.Message):
    """
    Отвечает за команду /new_group.
    Для регистрации новых групп в БД.
    Доступно только для администраторов.
    """
    async with SessionLocal() as session:

        if msg.from_user.id == admin_id:

            group_name =''.join(msg.text.split()[1:])
            if len(group_name) > 0 and await GroupMessage._create_group(session, group_name):
                await GroupMessage._create_group(session, group_name)
                await msg.answer(f"Группа {group_name} создана.")
            else:
                await msg.answer(f"Группа не создана. Вы не указали название группы либо такая группа уже сущетсвует.")

        else:

            await msg.answer("У вас недостаточно прав для выполнения этой комманды.")