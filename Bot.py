import os
import json
import logging
from datetime import datetime, timedelta
from random import randint, choice
from pyrogram import Client, filters
from pyrogram.enums import PollType
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import traceback

# --- Налаштування ---
api_id = 27300988
api_hash = "c7e02bdf78d426003e728343d05382ec"
bot_token = '7827074083:AAGHQXjB34aam_xbjCe8CnZQLAb5-nhXf3A'
bot_name = 'Кринжик'
channel_id = '@uctovbus'
admin_ids = [123456789]  # заміни на свій Telegram ID

emojis = list("🌟😢🧂🤑💃👏👋🤭🤪🤔😧🤦😛🤨👍🐍🥰☕😀😍🫐🇺🇦⌨️😎🎩😳😕😱🏃😂✍️🤓☔️😭🙃😷🤤😉🤡🙂")
karmadata_file = "karma_data.json"
active_polls = {}

# --- Логування ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Завантаження / збереження карми ---
def load_karma():
    try:
        with open(karmadata_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_karma(data):
    with open(karmadata_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

karma_data = load_karma()

# --- Ініціалізація ---
app = Client(bot_name, api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# --- Логіка команд (для повторного використання у команди та callback) ---

async def process_spin_wheel(user_id: str, reply_func):
    today = datetime.now().date()
    user_karma = karma_data.get(user_id, {"score": 0, "last_spin_date": None})
    if user_karma.get("last_spin_date") == today.isoformat():
        await reply_func("🕐 Колесо доступне лише раз на день.")
        return

    reward = randint(1, 5)
    user_karma["score"] += reward
    user_karma["last_spin_date"] = today.isoformat()
    karma_data[user_id] = user_karma
    save_karma(karma_data)

    await reply_func(f"🎡 Колесо обернулось!\n+{reward} очок!\nЗагальна карма: {user_karma['score']}")

async def process_show_top_users(reply_func):
    sorted_users = sorted(karma_data.items(), key=lambda x: x[1]['score'], reverse=True)
    text = "🏆 Топ 5 гравців:\n"
    for i, (uid, data) in enumerate(sorted_users[:5], 1):
        text += f"{i}. {uid} — {data['score']} очок\n"
    await reply_func(text)

async def process_show_karma(user_id: str, reply_func):
    user_karma = karma_data.get(user_id, {"score": 0, "last_vote_date": None, "streak": 0})
    await reply_func(
        f"🎯 Твоя карма:\n"
        f"Очки: {user_karma['score']}\n"
        f"Стрик: {user_karma.get('streak', 0)}\n"
        f"Останнє голосування: {user_karma['last_vote_date'] or 'ще не голосував'}"
    )

async def process_luckypoll(client):
    options = [choice(emojis) for _ in range(randint(2, 10))]
    correct_option_id = randint(0, len(options) - 1)
    poll = await client.send_poll(
        chat_id=channel_id,
        question=f'На Удачу {datetime.now().strftime("%d.%m.%y")}',
        options=options,
        is_anonymous=True,
        type=PollType.QUIZ,
        correct_option_id=correct_option_id,
        explanation='Maybe next time...'
    )
    active_polls[poll.poll.id] = {
        "correct_option_id": correct_option_id,
        "created_at": datetime.now()
    }

# --- Обробники команд ---

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("Привіт! Я бот для рандомних опитувань 🎯")

@app.on_message(filters.command("go"))
async def luckypoll_command(client, message):
    await message.delete()
    try:
        await process_luckypoll(client)
    except Exception as err:
        await message.reply_text(f"Помилка: {err}")

@app.on_message(filters.command("karma"))
async def show_karma_command(client, message):
    user_id = str(message.from_user.id)
    await process_show_karma(user_id, message.reply_text)

@app.on_message(filters.command("top"))
async def show_top_users_command(client, message):
    await process_show_top_users(message.reply_text)

@app.on_message(filters.command("wheel"))
async def spin_wheel_command(client, message):
    user_id = str(message.from_user.id)
    await process_spin_wheel(user_id, message.reply_text)

@app.on_message(filters.command("help"))
async def show_help(client, message):
    try:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎡 Колесо", callback_data="wheel")],
            [InlineKeyboardButton("🏆 Топ", callback_data="top")],
            [InlineKeyboardButton("🎯 Карма", callback_data="karma")],
            [InlineKeyboardButton("🎲 Опитування", callback_data="go")]
        ])

        help_text = (
            "🤖 Доступні команди:\n"
            "/start – привітання\n"
            "/go – створити опитування\n"
            "/karma – твоя карма\n"
            "/top – топ гравців\n"
            "/wheel – колесо удачі (1 раз/день)\n"
            "/help – допомога"
        )
        await message.reply_text(help_text, reply_markup=keyboard)
    except Exception as e:
        await message.reply_text(f"Виникла помилка: {e}")
        print(traceback.format_exc())

# --- Обробники callback-кнопок ---

@app.on_callback_query()
async def handle_callbacks(client, callback_query):
    data = callback_query.data
    user_id = str(callback_query.from_user.id)
    msg = callback_query.message

    try:
        if data == "wheel":
            await process_spin_wheel(user_id, msg.reply_text)
        elif data == "top":
            await process_show_top_users(msg.reply_text)
        elif data == "karma":
            await process_show_karma(user_id, msg.reply_text)
        elif data == "go":
            # Видаляємо повідомлення користувача, якщо потрібно
            await callback_query.message.delete()
            await process_luckypoll(client)
        else:
            await msg.reply_text("Невідома команда з кнопки.")
    except Exception as e:
        logger.error(f"Помилка в callback: {e}")
        await msg.reply_text(f"Виникла помилка: {e}")

    await callback_query.answer()

@app.on_message(filters.command("admin"))
async def admin_panel(client, message):
    if message.from_user.id not in admin_ids:
        await message.reply_text("⛔️ Доступ лише для адмінів")
        return
    await message.reply_text(f"👑 Панель адміністратора\nЗареєстровано користувачів: {len(karma_data)}")

# --- Обробник голосувань (PollAnswer) ---

@app.on_raw_update()
async def handle_poll_answer_raw(client, update, users, chats):
    if update.__class__.__name__ != "UpdatePollAnswer":
        return

    user_id = str(update.user_id)
    poll_id = update.poll_id
    selected_option = update.option_ids[0]
    today = datetime.now().date()
    correct_option = active_polls.get(poll_id, {}).get("correct_option_id")

    if correct_option is None:
        return

    user_karma = karma_data.get(user_id, {"score": 0, "last_vote_date": None, "streak": 0})
    user_karma["score"] += 1  # участь

    last_vote_str = user_karma.get("last_vote_date")
    if last_vote_str:
        last_vote_date = datetime.strptime(last_vote_str, '%Y-%m-%d').date()
        if last_vote_date == today - timedelta(days=1):
            user_karma["streak"] = user_karma.get("streak", 0) + 1
        elif last_vote_date < today - timedelta(days=1):
            user_karma["streak"] = 1
    else:
        user_karma["streak"] = 1

    if user_karma["streak"] >= 3:
        user_karma["score"] += 2 + (user_karma["streak"] - 3)

    if selected_option == correct_option:
        user_karma["score"] += 2

    user_karma["last_vote_date"] = today.isoformat()
    karma_data[user_id] = user_karma
    save_karma(karma_data)

    try:
        await client.send_message(int(user_id), f"🎉 Отримано очки!\nЗагальна карма: {user_karma['score']}")
    except Exception as e:
        logger.warning(f"Не можу написати користувачу {user_id}: {e}")

# --- Запуск ---

if __name__ == "__main__":
    # Якщо файл з кармою не існує, створити пустий
    if not os.path.exists(karmadata_file):
        with open(karmadata_file, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=4)

    print(f"{bot_name} запущено...")
    app.run()
