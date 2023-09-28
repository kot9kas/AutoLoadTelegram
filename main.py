import logging
from telethon import TelegramClient, events, Button

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.WARNING)

api_id = '****' # Тут api с сайта https://my.telegram.org/apps
api_hash = '***' # тут хеш с того же сайта
bot_token = '***' # Тут ваш токен бота
admin_user_id = ****  # Замените на ваш user ID

client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# Хранение данных о сессиях и пользователях
sessions = {}
users = {}
awaiting_comment = False


@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    try:
        await event.respond('Выберите действие:', buttons=[
            [Button.text('Поддержка')],
            [Button.text('Загрузить файлы')],
            [Button.text('Личный кабинет')]
        ])
    except Exception as e:
        logging.error(f"Error in start: {e}")


@client.on(events.NewMessage(pattern='Поддержка'))
async def support(event):
    try:
        await event.respond('За поддержкой писать сюда: @kot9k.')
    except Exception as e:
        logging.error(f"Error in support: {e}")


@client.on(events.NewMessage(pattern='Загрузить файлы'))
async def upload_files(event):
    try:
        await event.respond('Пожалуйста, отправьте файлы.')
    except Exception as e:
        logging.error(f"Error in upload_files: {e}")


@client.on(events.NewMessage(pattern='Личный кабинет'))
async def personal_cabinet(event):
    user_id = event.sender_id
    if user_id not in users:
        users[user_id] = {
            'files_uploaded': 0,
            'balance': 0,
            'registration_date': event.date.strftime('%Y-%m-%d')
        }
    user_info = users[user_id]
    response = f"📁 Загруженные файлы: {user_info['files_uploaded']}\n" \
               f"💰 Баланс: {user_info['balance']} руб.\n" \
               f"📅 Дата регистрации: {user_info['registration_date']}"
    await event.respond(response)


@client.on(events.NewMessage())
async def handle_files(event):
    try:
        if event.message.media:
            user_id = event.sender_id
            if user_id not in users:
                users[user_id] = {
                    'files_uploaded': 0,
                    'balance': 0,
                    'registration_date': event.date.strftime('%Y-%m-%d')
                }
            users[user_id]['files_uploaded'] += 1

            sessions[event.message.id] = {
                'user_id': event.sender_id,
                'file': event.message.media,
                'status': 'open'
            }
            # Пересылаем файл администратору
            await client.forward_messages(admin_user_id, event.message)
            await client.send_message(admin_user_id, 'Новый файл получен!', buttons=[
                [Button.text('Принять')],
                [Button.text('Отклонить')],
                [Button.text('Написать комментарий')],
                [Button.text('Закрыть')]
            ])
    except Exception as e:
        logging.error(f"Error in handle_files: {e}")

@client.on(events.NewMessage(pattern='Принять'))
async def accept_file(event):
    try:
        session = list(sessions.values())[-1]
        await client.send_message(session['user_id'], 'Ваши файлы были приняты!')
        session['status'] = 'accepted'
    except Exception as e:
        logging.error(f"Error in accept_file: {e}")

@client.on(events.NewMessage(pattern='Отклонить'))
async def reject_file(event):
    try:
        session = list(sessions.values())[-1]
        await client.send_message(session['user_id'], 'Ваши файлы были отклонены.')
        session['status'] = 'rejected'
    except Exception as e:
        logging.error(f"Error in reject_file: {e}")

@client.on(events.NewMessage(pattern='Написать комментарий'))
async def comment_file(event):
    global awaiting_comment
    try:
        if event.sender_id == admin_user_id:
            awaiting_comment = True
            await event.respond('Пожалуйста, введите ваш комментарий.')
    except Exception as e:
        logging.error(f"Error in comment_file: {e}")

@client.on(events.NewMessage())
async def handle_comment(event):
    global awaiting_comment
    try:
        if awaiting_comment and event.sender_id == admin_user_id and sessions:
            session = list(sessions.values())[-1]
            await client.send_message(session['user_id'], f'Комментарий к вашим файлам: {event.message.text}')
            session['status'] = 'commented'
            awaiting_comment = False
    except Exception as e:
        logging.error(f"Error in handle_comment: {e}")

@client.on(events.NewMessage(pattern='Закрыть'))
async def close_session(event):
    try:
        if sessions:
            session = list(sessions.values())[-1]
            session['status'] = 'closed'
    except Exception as e:
        logging.error(f"Error in close_session: {e}")

@client.on(events.NewMessage(pattern='/admin'))
async def admin_panel(event):
    try:
        if event.sender_id == admin_user_id:
            total_users = len(set([session['user_id'] for session in sessions.values()]))
            open_sessions = sum(1 for session in sessions.values() if session['status'] == 'open')
            closed_sessions = sum(1 for session in sessions.values() if session['status'] == 'closed')
            await event.respond(f'Общее количество пользователей: {total_users}\nОткрытые сессии: {open_sessions}\nЗакрытые сессии: {closed_sessions}')
    except Exception as e:
        logging.error(f"Error in admin_panel: {e}")

client.run_until_disconnected()