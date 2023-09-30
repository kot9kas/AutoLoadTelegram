from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from db import initialize
from datetime import datetime
from aiogram.dispatcher import FSMContext
from logic import add_user, check_user_rules_accepted, set_accepted_rules, add_file_info, get_user_by_file_id, add_user, add_file, get_file_info_by_record, add_balance, get_user_balance, get_registration_date, set_user_rating, get_user_rating

TOKEN = 'бла бла бла' #токен бота
ADMIN_ID = '1234567' #ваш телеграм ид

CHECK_EMOJI = "✅"
CROSS_EMOJI = "❌"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

user_categories = {}
user_comments = {}
user_state = {}
user_states = {}




@dp.message_handler(commands=['start'])
async def on_start(message: types.Message):
    user_id = message.from_user.id
    await add_user(user_id)
    rules_accepted = await check_user_rules_accepted(user_id)

    if not rules_accepted:
        keyboard = InlineKeyboardMarkup()
        btn_accept = InlineKeyboardButton(text="✅ Принять правила", callback_data="accept_rules")
        btn_decline = InlineKeyboardButton(text="❌ Отклонить правила", callback_data="decline_rules")
        keyboard.add(btn_accept, btn_decline)
        
        rules_text = (
            "📜 <b>Правила использования бота:</b>\n"
            "\n"
            "1. - Не злоупотребляйте ботом.\n"
            "2. - Все ваши данные хранятся в безопасности.\n"
            "3. - Бот предоставляется «как есть», без каких-либо гарантий.\n"
            "\n"
            "Пожалуйста, примите правила, чтобы продолжить."
        )
        await message.answer(rules_text, reply_markup=keyboard, parse_mode='HTML')
    else:
        await show_main_menu(message, user_id)


async def show_main_menu(message, user_id):
    # Получаем дату регистрации пользователя
    user_rating = get_user_rating(user_id)
    registration_date = await get_registration_date(user_id)

    # Создаем приветственное сообщение
    if message.from_user.username:
        greeting = f"👋 Привет, @{message.from_user.username}!\n"
    else:
        greeting = f"👋 Привет!\n"

    if registration_date:
        greeting += f"📅 Дата вашей регистрации: {registration_date}\n🌟 Ваш рейтинг: {user_rating}\n\n"
        

    

    # Создаем клавиатуру для главного меню
    markup = InlineKeyboardMarkup(row_width=2)
    item1 = InlineKeyboardButton("Загрузить файл", callback_data="upload_file")
    item2 = InlineKeyboardButton("Баланс", callback_data="check_balance")
    item3 = InlineKeyboardButton("Помощь", callback_data="help")
    markup.add(item1, item2, item3)

    full_message = greeting + "Выберите опцию:"

    await bot.send_message(
        message.chat.id,
        full_message,
        reply_markup=markup
    )



@dp.callback_query_handler(lambda c: c.data == "accept_rules")
async def rules_accepted(callback_query: types.CallbackQuery):
    await set_accepted_rules(callback_query.from_user.id)
    await bot.answer_callback_query(callback_query.id)
    await show_main_menu(callback_query.message, callback_query.from_user.id)

from aiogram.dispatcher.filters import Text

@dp.callback_query_handler(lambda c: c.data == "get_help")
async def get_help(callback_query: types.CallbackQuery):
    await bot.send_message(
        callback_query.message.chat.id,
        "Если у вас возникли вопросы или проблемы, обратитесь к администратору: @AdminUser."
    )
    await bot.answer_callback_query(callback_query.id)  # Это чтобы убрать "часики" в inline кнопке после нажатия


@dp.callback_query_handler(lambda c: c.data == "check_balance")
async def check_balance(message: types.Message):
    user_id = message.from_user.id
    balance = get_user_balance(user_id)
    await message.answer(f"Ваш баланс: {balance} рублей.")

# Обработчик для получения файла
# Глобальные переменные для хранения выбора пользователя
user_categories = {}

@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def handle_document(message: types.Message):
    user_id = message.from_user.id
    rules_accepted = await check_user_rules_accepted(user_id)

    # Проверка, принял ли пользователь правила
    if not rules_accepted:
        keyboard = InlineKeyboardMarkup()
        btn_accept = InlineKeyboardButton(text="✅ Принять правила", callback_data="accept_rules")
        btn_decline = InlineKeyboardButton(text="❌ Отклонить правила", callback_data="decline_rules")
        keyboard.add(btn_accept, btn_decline)
        
        rules_text = (
            "📜 <b>Правила использования бота:</b>\n"
            "\n"
            "1. - Не злоупотребляйте ботом.\n"
            "2. - Все ваши данные хранятся в безопасности.\n"
            "3. - Бот предоставляется «как есть», без каких-либо гарантий.\n"
            "\n"
            "Пожалуйста, примите правила, чтобы продолжить."
        )
        await message.answer(rules_text, reply_markup=keyboard, parse_mode='HTML')
    else:
        await show_main_menu(message, user_id)
    file_id = message.document.file_id
    file_record_id = add_file(message.from_user.id, file_id)

    # Создание клавиатуры с категориями и галочками/крестиками
    markup = InlineKeyboardMarkup(row_width=2)

    categories = ["Steam", "Origin", "Epic Games"]
    user_categories[message.from_user.id] = []

    for category in categories:
        markup.add(InlineKeyboardButton(f"{CROSS_EMOJI} {category}", callback_data=f"toggle_{category}_{file_record_id}"))

    markup.add(InlineKeyboardButton("Отправить", callback_data=f"send_{file_record_id}"))
    markup.add(InlineKeyboardButton("Добавить комментарий", callback_data=f"comment_{file_record_id}"))


    await bot.send_message(message.from_user.id, "Выберите категории для файла:", reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data.startswith("comment_"))
async def comment_file(callback_query: types.CallbackQuery):
    data = callback_query.data.split("_")
    file_record_id = data[1]
    
    user_comments[callback_query.from_user.id] = file_record_id
    await bot.send_message(callback_query.from_user.id, "Введите ваш комментарий:")

user_file_comments = {}  # Для хранения комментариев к файлам

@dp.message_handler(lambda message: message.from_user.id in user_comments, content_types=types.ContentType.TEXT)
async def handle_comment(message: types.Message):
    file_record_id = user_comments.pop(message.from_user.id)
    comment = message.text

    user_file_comments[file_record_id] = comment
    await bot.send_message(message.from_user.id, f"Ваш комментарий к файлу {file_record_id} был сохранен!")


@dp.callback_query_handler(lambda c: c.data.startswith("toggle_"))
async def toggle_category(callback_query: types.CallbackQuery):
    data = callback_query.data.split("_")
    category, file_record_id = data[1], data[2]
    user_id = callback_query.from_user.id

    # Обновляем список выбранных категорий пользователя
    if category in user_categories[user_id]:
        user_categories[user_id].remove(category)
    else:
        user_categories[user_id].append(category)

    # Обновляем клавиатуру с выбранными категориями
    markup = InlineKeyboardMarkup(row_width=2)
    categories = ["Steam", "Origin", "Epic Games"]
    for cat in categories:
        if cat in user_categories[user_id]:
            markup.add(InlineKeyboardButton(f"{CHECK_EMOJI} {cat}", callback_data=f"toggle_{cat}_{file_record_id}"))
        else:
            markup.add(InlineKeyboardButton(f"{CROSS_EMOJI} {cat}", callback_data=f"toggle_{cat}_{file_record_id}"))

    markup.add(InlineKeyboardButton("Отправить", callback_data=f"send_{file_record_id}"))
    markup.add(InlineKeyboardButton("Добавить комментарий", callback_data=f"comment_{file_record_id}"))

    await bot.edit_message_reply_markup(callback_query.message.chat.id, callback_query.message.message_id, reply_markup=markup)

@dp.callback_query_handler(lambda c: 'empty_' in c.data)
async def handle_empty(callback_query: types.CallbackQuery):
    file_id = callback_query.data.split('_')[1]
    user_id = await get_user_by_file_id(file_id)
    
    if user_id:
        await bot.send_message(user_id, f"Ваш отправленный файл {file_id} пустой.")

@dp.callback_query_handler(lambda c: c.data == "decline_rules")
async def rules_declined(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Вы должны принять правила, чтобы использовать этого бота.")


# Пока что этот обработчик просто выводит информационное сообщение, но вы можете добавить логику пополнения баланса.
@dp.callback_query_handler(lambda c: 'balance_' in c.data)
async def handle_balance(callback_query: types.CallbackQuery):
    file_id = callback_query.data.split('_')[1]
    user_id = callback_query.from_user.id

    # Отправляем клавиатуру администратору для ввода суммы
    msg = await bot.send_message(callback_query.from_user.id, "Введите сумму для начисления:")
    
    # Сохраняем file_id в пользовательской памяти (или в другом месте) для использования в следующем обработчике
    # Используем user_state для хранения временной информации
    user_state[user_id] = {'action': 'add_balance', 'file_id': file_id}

@dp.message_handler(lambda message: message.from_user.id in user_state and user_state[message.from_user.id]['action'] == 'add_balance')
async def input_balance_amount(message: types.Message):
    user_id = message.from_user.id
    amount = int(message.text)  # Преобразуем ввод пользователя в число

    # Получаем file_id из пользовательской памяти (или другого места)
    file_id = user_state[user_id]['file_id']

    # Начисление баланса
    add_balance(user_id, amount)

    del user_state[user_id]  # Удаляем временную информацию

    await bot.send_message(user_id, f"Баланс за файл {file_id} начислен. Вы получили {amount} рублей!")

@dp.callback_query_handler(lambda c: c.data == "upload_file")
async def prompt_for_file(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Пожалуйста, отправьте файл.")

# Обработчик для отправки файла администратору
@dp.callback_query_handler(lambda c: c.data.startswith("send_"))
async def send_to_admin(callback_query: types.CallbackQuery):
    data = callback_query.data.split("_")
    file_record_id = data[1]
    user_id = callback_query.from_user.id
    categories_selected = user_categories.get(user_id, [])

    # Получаем комментарий из user_file_comments
    comment = user_file_comments.get(file_record_id, "Нет комментария")

    # Получите информацию о файле из базы данных
    file_info = await get_file_info_by_record(file_record_id)
    markup = InlineKeyboardMarkup(row_width=2)
    btn_balance = InlineKeyboardButton(text="Начислить баланс", callback_data=f"balance_{file_record_id}")
    btn_empty = InlineKeyboardButton(text="Пустой", callback_data=f"empty_{file_record_id}")
    btn_set_rating = InlineKeyboardButton(text="Выдать рейтинг", callback_data=f"setrating_{user_id}")
    btn_rating = InlineKeyboardButton(text="Показать рейтинг", callback_data=f"rating_{user_id}")

    if file_info:
        file_path = file_info['telegram_file_id']

        # Отправьте файл и комментарий администратору
        await bot.send_document(
        ADMIN_ID, 
        file_path, 
        caption=(
        f"📁 Файл от пользователя: @{callback_query.from_user.username}\n"
        f"🔖 File ID: {file_record_id}\n"
        f"🏷️ Категории: {', '.join(categories_selected)}\n"
        f"📝 Комментарий: {comment}"
    ), 
    reply_markup=markup.add(btn_balance, btn_empty, btn_rating, btn_set_rating)
    )

        # Отправьте подтверждение пользователю
        await bot.send_message(user_id, f"Ваш файл под номером {file_record_id} был отправлен администратору!")
    else:
        await bot.send_message(user_id, f"Извините, произошла ошибка. Файл с номером {file_record_id} не найден.")
def save_user_rating(user_id, rating):
    # Здесь вы можете добавить код для сохранения рейтинга в базе данных
    set_user_rating(user_id, rating)

# Обработчик для ввода рейтинга
@dp.message_handler(lambda message: user_states.get(message.from_user.id) == 'awaiting_rating')
async def handle_rating_input(message: types.Message):
    user_id = message.from_user.id
    rating = message.text  # Получаем текст, введенный пользователем

    # Получаем file_id из пользовательской памяти (или другого места)
    file_id = user_state[user_id]['file_id']

    # Вызываем функцию для сохранения рейтинга
    save_user_rating(user_id, rating)

    # Очищаем состояние пользователя
    del user_states[user_id]

    await bot.send_message(user_id, f"Рейтинг для пользователя установлен: {rating}")
@dp.callback_query_handler(lambda c: c.data.startswith("setrating_"))
async def set_user_rating_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    await bot.answer_callback_query(callback_query.id, "Введите рейтинг для пользователя.", show_alert=True)

    # Устанавливаем состояние для пользователя
    user_states[user_id] = 'awaiting_rating'

    # Сохраняем user_id в пользовательской памяти (или другом месте) для использования в следующем обработчике
    user_state[user_id] = {'action': 'set_user_rating', 'file_id': None}
# Запуск бота
initialize()
if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)