from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from db import initialize
from datetime import datetime
from logic import add_user, check_user_rules_accepted, set_accepted_rules, add_file_info, get_user_by_file_id, add_user, add_file, get_file_info_by_record

TOKEN = 'бла бла бла' #токен бота
ADMIN_ID = '1234567' #ваш телеграм ид

CHECK_EMOJI = "✅"
CROSS_EMOJI = "❌"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

user_categories = {}

@dp.message_handler(commands=['start'])
async def on_start(message: types.Message):
    user_id = message.from_user.id
    await add_user(user_id)
    rules_accepted = await check_user_rules_accepted(user_id)

    if not rules_accepted:
        keyboard = InlineKeyboardMarkup()
        btn_accept = InlineKeyboardButton(text="Принять правила", callback_data="accept_rules")
        btn_decline = InlineKeyboardButton(text="Отклонить правила", callback_data="decline_rules")
        keyboard.add(btn_accept, btn_decline)
        await message.answer("Пожалуйста, примите правила, чтобы продолжить.", reply_markup=keyboard)
    else:
        await show_main_menu(message, user_id)

async def show_main_menu(message, user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    item1 = InlineKeyboardButton("Загрузить файл", callback_data="upload_file")
    # Добавьте другие кнопки для главного меню по аналогии
    markup.add(item1)

    await bot.send_message(
        message.chat.id,
        f"Выберите опцию:",
        reply_markup=markup
    )


@dp.callback_query_handler(lambda c: c.data == "accept_rules")
async def rules_accepted(callback_query: types.CallbackQuery):
    await set_accepted_rules(callback_query.from_user.id)
    await bot.answer_callback_query(callback_query.id)
    await show_main_menu(callback_query.message, callback_query.from_user.id)
    
# Обработчик для получения файла
# Глобальные переменные для хранения выбора пользователя
user_categories = {}

@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def handle_document(message: types.Message):
    # Сохранить file_id в базе данных
    file_id = message.document.file_id
    file_record_id = add_file(message.from_user.id, file_id)

    # Создание клавиатуры с категориями и галочками/крестиками
    markup = InlineKeyboardMarkup(row_width=2)

    categories = ["Steam", "Origin", "Epic Games"]
    user_categories[message.from_user.id] = []

    for category in categories:
        markup.add(InlineKeyboardButton(f"{CROSS_EMOJI} {category}", callback_data=f"toggle_{category}_{file_record_id}"))

    markup.add(InlineKeyboardButton("Отправить администратору", callback_data=f"send_{file_record_id}"))

    await bot.send_message(message.from_user.id, "Выберите категории для файла:", reply_markup=markup)

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

    markup.add(InlineKeyboardButton("Отправить администратору", callback_data=f"send_{file_record_id}"))

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
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, f"Баланс за файл {file_id} начислен.")

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

    # Получите информацию о файле из базы данных
    file_info = await get_file_info_by_record(file_record_id)
    markup = InlineKeyboardMarkup(row_width=2)
    btn_balance = InlineKeyboardButton(text="Начислить баланс", callback_data=f"balance_{file_record_id}")
    btn_empty = InlineKeyboardButton(text="Пустой", callback_data=f"empty_{file_record_id}")

    if file_info:
        file_path = file_info['telegram_file_id']

        # Отправьте файл администратору
        await bot.send_document(ADMIN_ID, file_path, caption=f"Файл от пользователя @{callback_query.from_user.username}, Категории: {', '.join(categories_selected)}. File ID: {file_record_id}", reply_markup=markup.add(btn_balance, btn_empty))

        # Отправьте подтверждение пользователю
        await bot.send_message(user_id, f"Ваш файл под номером {file_record_id} был отправлен администратору!")

        markup = InlineKeyboardMarkup(row_width=2)
        btn_balance = InlineKeyboardButton(text="Начислить баланс", callback_data=f"balance_{file_record_id}")
        markup.add(btn_balance)

    else:
        await bot.send_message(user_id, f"Извините, произошла ошибка. Файл с номером {file_record_id} не найден.")

# Запуск бота
initialize()
if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)