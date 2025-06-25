import os
import json
import logging
from datetime import datetime, timedelta
from random import randint, choice
from pyrogram.client import Client
from pyrogram import filters
from pyrogram.enums import PollType
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
import traceback
import time
import random
import requests
import re

# --- Налаштування ---
api_id = 27300988
api_hash = "c7e02bdf78d426003e728343d05382ec"
bot_token = '7827074083:AAGHQXjB34aam_xbjCe8CnZQLAb5-nhXf3A'
bot_name = 'Кринжик'
channel_id = '@uctovbus'
admin_ids = [1249361958]  # ваш Telegram ID
admin_usernames = ['professional012']  # ваш нікнейм

emojis = list("🌟😢🧂🤑💃👏👋🤭🤪🤔😧🤦😛🤨👍🐍🥰☕😀😍🫐🇺🇦⌨️😎🎩😳😕😱🏃😂✍️🤓☔️😭🙃😷🤤😉🤡🙂")
karmadata_file = "karma_data.json"
active_polls = {}
character_data_file = "character_data.json"
try:
    with open(character_data_file, "r", encoding="utf-8") as f:
        character_data = json.load(f)
except FileNotFoundError:
    character_data = {}

def save_character_data(data):
    with open(character_data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- Логування ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Жартівливі гороскопи ---
horoscope_predictions = [
    "Сьогодні твоя карма зросте на 0.0001%!",
    "Не бери участь у дивних опитуваннях... або бери!",
    "Тебе чекає несподіваний бонус у вигляді гарного настрою!",
    "Зірки радять: зроби добру справу і не забудь про каву!",
    "Твій сміх сьогодні буде особливо заразним.",
    "Уникай людей з поганою кармою, але не надто!",
    "Сьогодні твій день для нових мемів!",
    "Ти отримаєш повідомлення, яке змінить твій настрій на краще.",
    "Зірки кажуть: не забувай про відпочинок!",
    "Твоя удача сьогодні схожа на Wi-Fi — то є, то нема!",
    "Сьогодні ти можеш усе! Або майже усе...",
    "Твоя харизма сьогодні на максимумі!",
    "Не забудь посміхнутись — це твій головний талісман!",
    "Сьогодні ти — головний герой свого чату!",
    "Зірки радять: не забувай про воду і меми!"
]

# --- Жартівливі відповіді для гри Так чи Ні ---
yesno_answers = [
    "Так! І навіть не сумнівайся!",
    "Ні, і краще не перевіряй!",
    "Можливо... але це не точно.",
    "Зірки кажуть: так, але з обережністю!",
    "Ні, але ти можеш спробувати ще раз!",
    "100% так! (або ні)",
    "Спробуй ще раз запитати — може відповідь зміниться!",
    "Так, але тільки якщо ти зробиш селфі з котом!",
    "Ні, сьогодні не твій день для цього.",
    "Можливо, але краще з'їж печиво!",
    "Так, але не розповідай нікому!",
    "Ні, але не засмучуйся!",
    "Можливо... Всесвіт ще не вирішив!",
    "Так, але тільки якщо ти посміхнешся!",
    "Ні, але завтра все зміниться!"
]

# --- Функція перевірки адміністратора ---
def is_admin(user):
    if not user:
        return False
    return (user.id in admin_ids or 
            (user.username and user.username in admin_usernames))

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
session_name = f"Кринжик_{int(time.time())}_{random.randint(1000, 9999)}"
app = Client(session_name, api_id=api_id, api_hash=api_hash, bot_token=bot_token)

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

async def process_show_top_users(reply_func, client=None):
    try:
        sorted_users = sorted(karma_data.items(), key=lambda x: x[1]['score'], reverse=True)
        text = "🏆 Топ 5 гравців:\n"
        
        for i, (uid, data) in enumerate(sorted_users[:5], 1):
            # Спочатку перевіряємо, чи є збережене ім'я
            if "display_name" in data:
                display_name = data["display_name"]
            else:
                try:
                    if client:
                        # Отримуємо інформацію про користувача
                        user = await client.get_users(int(uid))
                        if user.username:
                            display_name = f"@{user.username}"
                        elif user.first_name:
                            display_name = user.first_name
                            if user.last_name:
                                display_name += f" {user.last_name}"
                        else:
                            display_name = f"Користувач {uid}"
                    else:
                        display_name = f"Користувач {uid}"
                except Exception as e:
                    logger.warning(f"Не можу отримати інформацію про користувача {uid}: {e}")
                    # Спробуємо отримати з кешу або використаємо ID
                    try:
                        if client:
                            user = await client.get_chat(int(uid))
                            if hasattr(user, 'username') and user.username:
                                display_name = f"@{user.username}"
                            elif hasattr(user, 'first_name') and user.first_name:
                                display_name = user.first_name
                            else:
                                display_name = f"Користувач {uid}"
                        else:
                            display_name = f"Користувач {uid}"
                    except:
                        display_name = f"Користувач {uid}"
            
            text += f"{i}. {display_name} — {data['score']} очок\n"
        
        await reply_func(text)
    except Exception as e:
        logger.error(f"Помилка в process_show_top_users: {e}")
        await reply_func(f"Помилка при показі топу: {e}")

async def process_show_karma(user_id: str, reply_func, client=None):
    try:
        user_karma = karma_data.get(user_id, {"score": 0, "last_vote_date": None, "streak": 0})
        logger.info(f"Показую карму для {user_id}: {user_karma}")
        
        # Отримуємо ім'я користувача
        display_name = f"Користувач {user_id}"
        if client:
            try:
                user = await client.get_users(int(user_id))
                username = user.username or user.first_name or f"Користувач {user_id}"
                display_name = f"@{username}" if user.username else username
            except Exception as e:
                logger.warning(f"Не можу отримати інформацію про користувача {user_id}: {e}")
        
        await reply_func(
            f"🎯 Карма {display_name}:\n"
            f"Очки: {user_karma['score']}\n"
            f"Стрик: {user_karma.get('streak', 0)}"
        )
    except Exception as e:
        logger.error(f"Помилка в process_show_karma: {e}")
        await reply_func(f"Помилка при показі карми: {e}")

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
    commands = [
        BotCommand("start", "Привітання"),
        BotCommand("karma", "Твоя карма"),
        BotCommand("top", "Топ гравців"),
        BotCommand("wheel", "Колесо удачі (1 раз/день)"),
        BotCommand("setname", "Встановити своє ім'я"),
        BotCommand("setname_reply", "Встановити ім'я через reply"),
        BotCommand("myname", "Переглянути своє ім'я"),
        BotCommand("horoscope", "Міні-гороскоп"),
        BotCommand("yesno", "Гра Так чи Ні"),
        BotCommand("help", "Допомога"),
        BotCommand("character", "Отримати персонажа")
    ]
    await client.set_bot_commands(commands)
    await message.reply_text("Привіт! Я бот для рандомних опитувань 🎯")

@app.on_message(filters.command("go"))
async def luckypoll_command(client, message):
    # Перевіряємо, чи користувач є адміністратором
    if not is_admin(message.from_user):
        await message.reply_text("⛔️ Команда доступна лише для адміністраторів")
        return
    
    await message.delete()
    try:
        await process_luckypoll(client)
    except Exception as err:
        await message.reply_text(f"Помилка: {err}")

@app.on_message(filters.command("karma"))
async def show_karma_command(client, message):
    try:
        if not message.from_user:
            await message.reply_text("❌ Помилка: не вдалося визначити користувача. Спробуйте написати боту в приватному повідомленні.")
            return
            
        user_id = str(message.from_user.id)
        logger.info(f"Команда karma викликана користувачем {user_id}")
        logger.info(f"Дані карми: {karma_data}")
        await process_show_karma(user_id, message.reply_text, client)
    except Exception as e:
        logger.error(f"Помилка в команді karma: {e}")
        await message.reply_text(f"Виникла помилка: {e}")

@app.on_message(filters.command("top"))
async def show_top_users_command(client, message):
    await process_show_top_users(message.reply_text, client)

@app.on_message(filters.command("wheel"))
async def spin_wheel_command(client, message):
    if not message.from_user:
        await message.reply_text("❌ Помилка: не вдалося визначити користувача. Спробуйте написати боту в приватному повідомленні.")
        return
        
    user_id = str(message.from_user.id)
    await process_spin_wheel(user_id, message.reply_text)

@app.on_message(filters.command("help"))
async def show_help(client, message):
    try:
        # Створюємо базову клавіатуру для всіх користувачів
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎡 Колесо", callback_data="wheel")],
            [InlineKeyboardButton("🏆 Топ", callback_data="top")],
            [InlineKeyboardButton("🎯 Карма", callback_data="karma")],
            [InlineKeyboardButton("👤 Персонаж", callback_data="character")],
            [InlineKeyboardButton("🔮 Гороскоп", callback_data="horoscope")],
            [InlineKeyboardButton("❓ Так чи Ні", callback_data="yesno")]
        ])

        help_text = (
            "🤖 Доступні команди:\n"
            "/start – привітання\n"
            "/karma – твоя карма\n"
            "/top – топ гравців\n"
            "/wheel – колесо удачі (1 раз/день)\n"
            "/setname – встановити своє ім'я\n"
            "/setname_reply – встановити ім'я через reply\n"
            "/myname – переглянути своє ім'я\n"
            "/horoscope – міні-гороскоп\n"
            "/yesno – гра Так чи Ні\n"
            "/help – допомога\n"
            "/character – отримати персонажа"
        )
        
        # Перевіряємо, чи є користувач і чи він адміністратор
        if is_admin(message.from_user):
            pass
        
        await message.reply_text(help_text, reply_markup=keyboard)
    except Exception as e:
        await message.reply_text(f"Виникла помилка: {e}")
        print(traceback.format_exc())

@app.on_message(filters.command("test"))
async def test_command(client, message):
    try:
        if not message.from_user:
            await message.reply_text("❌ Помилка: не вдалося визначити користувача. Спробуйте написати боту в приватному повідомленні.")
            return
            
        user_id = str(message.from_user.id)
        await message.reply_text(
            f"🧪 Тест бота:\n"
            f"Ваш ID: {user_id}\n"
            f"Кількість користувачів у базі: {len(karma_data)}\n"
            f"Ваші дані: {karma_data.get(user_id, 'Не знайдено')}\n"
            f"Бот працює: ✅"
        )
    except Exception as e:
        await message.reply_text(f"Помилка тесту: {e}")

@app.on_message(filters.command("reload"))
async def reload_karma_command(client, message):
    try:
        global karma_data
        karma_data = load_karma()
        await message.reply_text(f"✅ Дані карми перезавантажено! Користувачів: {len(karma_data)}")
    except Exception as e:
        await message.reply_text(f"Помилка перезавантаження: {e}")

@app.on_message(filters.command("myid"))
async def get_my_id(client, message):
    if not message.from_user:
        await message.reply_text("❌ Помилка: не вдалося визначити користувача. Спробуйте написати боту в приватному повідомленні.")
        return
        
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    await message.reply_text(f"🆔 Ваш Telegram ID: {user_id}\nІм'я: {username}")

@app.on_message(filters.command("setname"))
async def set_user_name(client, message):
    if not message.from_user:
        await message.reply_text("❌ Помилка: не вдалося визначити користувача. Спробуйте написати боту в приватному повідомленні.")
        return
        
    try:
        # Отримуємо ім'я з повідомлення
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.reply_text("❌ Використання: /setname <ваше ім'я>\nНаприклад: /setname Іван")
            return
            
        new_name = args[1].strip()
        if len(new_name) > 50:
            await message.reply_text("❌ Ім'я занадто довге. Максимум 50 символів.")
            return
            
        user_id = str(message.from_user.id)
        
        # Отримуємо або створюємо дані користувача
        if user_id not in karma_data:
            karma_data[user_id] = {"score": 0, "last_vote_date": None, "streak": 0}
        
        # Зберігаємо ім'я користувача
        karma_data[user_id]["display_name"] = new_name
        save_karma(karma_data)
        
        await message.reply_text(f"✅ Ваше ім'я встановлено: {new_name}")
        
    except Exception as e:
        logger.error(f"Помилка в команді setname: {e}")
        await message.reply_text(f"Виникла помилка: {e}")

@app.on_message(filters.command("setname_simple"))
async def set_user_name_simple(client, message):
    logger.info(f"Команда setname_simple викликана користувачем {message.from_user.id if message.from_user else 'None'}")
    
    if not message.from_user:
        await message.reply_text("❌ Помилка: не вдалося визначити користувача.")
        return
        
    try:
        # Отримуємо ім'я з повідомлення
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.reply_text("❌ Використання: /setname_simple <ваше ім'я>\nНаприклад: /setname_simple Іван")
            return
            
        new_name = args[1].strip()
        logger.info(f"Отримано ім'я: '{new_name}'")
        
        if len(new_name) > 50:
            await message.reply_text("❌ Ім'я занадто довге. Максимум 50 символів.")
            return
            
        user_id = str(message.from_user.id)
        logger.info(f"Встановлюю ім'я '{new_name}' для користувача {user_id}")
        
        # Отримуємо або створюємо дані користувача
        if user_id not in karma_data:
            karma_data[user_id] = {"score": 0, "last_vote_date": None, "streak": 0}
        
        # Зберігаємо ім'я користувача
        karma_data[user_id]["display_name"] = new_name
        save_karma(karma_data)
        
        logger.info(f"Ім'я успішно збережено для користувача {user_id}")
        await message.reply_text(f"✅ Ваше ім'я встановлено: {new_name}")
        
    except Exception as e:
        logger.error(f"Помилка в команді setname_simple: {e}")
        await message.reply_text(f"Виникла помилка: {e}")

@app.on_message(filters.command("setname_reply"))
async def set_user_name_reply(client, message):
    logger.info(f"Команда setname_reply викликана користувачем {message.from_user.id if message.from_user else 'None'}")
    
    if not message.from_user:
        await message.reply_text("❌ Помилка: не вдалося визначити користувача.")
        return
        
    try:
        # Перевіряємо, чи є reply на повідомлення
        if not message.reply_to_message:
            logger.info("Немає reply повідомлення")
            await message.reply_text(
                "❌ Використання: /setname_reply\n"
                "1. Напишіть своє ім'я в повідомленні\n"
                "2. Відповідайте на це повідомлення командою /setname_reply\n"
                "Наприклад:\n"
                "Користувач: Іван\n"
                "Користувач: /setname_reply (відповідь на повідомлення 'Іван')"
            )
            return
            
        # Отримуємо ім'я з повідомлення, на яке відповідаємо
        new_name = message.reply_to_message.text.strip()
        logger.info(f"Отримано ім'я: '{new_name}'")
        
        if len(new_name) > 50:
            await message.reply_text("❌ Ім'я занадто довге. Максимум 50 символів.")
            return
            
        user_id = str(message.from_user.id)
        logger.info(f"Встановлюю ім'я '{new_name}' для користувача {user_id}")
        
        # Отримуємо або створюємо дані користувача
        if user_id not in karma_data:
            karma_data[user_id] = {"score": 0, "last_vote_date": None, "streak": 0}
        
        # Зберігаємо ім'я користувача
        karma_data[user_id]["display_name"] = new_name
        save_karma(karma_data)
        
        logger.info(f"Ім'я успішно збережено для користувача {user_id}")
        await message.reply_text(f"✅ Ваше ім'я встановлено: {new_name}")
        
    except Exception as e:
        logger.error(f"Помилка в команді setname_reply: {e}")
        await message.reply_text(f"Виникла помилка: {e}")

@app.on_message(filters.command("update_users"))
async def update_users_info(client, message):
    if not is_admin(message.from_user):
        await message.reply_text("⛔️ Команда доступна лише для адміністраторів")
        return
        
    try:
        updated_count = 0
        for uid in karma_data.keys():
            try:
                user = await client.get_users(int(uid))
                logger.info(f"Оновлено інформацію про користувача {uid}: {user.first_name} (@{user.username})")
                updated_count += 1
            except Exception as e:
                logger.warning(f"Не вдалося оновити інформацію про користувача {uid}: {e}")
        
        await message.reply_text(f"✅ Оновлено інформацію про {updated_count} користувачів")
    except Exception as e:
        await message.reply_text(f"Помилка оновлення: {e}")

@app.on_message(filters.command("myname"))
async def show_user_name(client, message):
    if not message.from_user:
        await message.reply_text("❌ Помилка: не вдалося визначити користувача.")
        return
        
    try:
        user_id = str(message.from_user.id)
        user_data = karma_data.get(user_id, {})
        
        if "display_name" in user_data:
            await message.reply_text(f"👤 Ваше ім'я в топі: {user_data['display_name']}")
        else:
            # Показуємо Telegram ім'я
            username = message.from_user.username or message.from_user.first_name
            display_name = f"@{username}" if message.from_user.username else username
            await message.reply_text(
                f"👤 У вас не встановлено власне ім'я.\n"
                f"Telegram ім'я: {display_name}\n"
                f"Використайте /setname_reply щоб встановити своє ім'я для топу."
            )
        
    except Exception as e:
        logger.error(f"Помилка в команді myname: {e}")
        await message.reply_text(f"Виникла помилка: {e}")

PIXABAY_API_KEY = "51035584-230539422b9389684289707a5"

@app.on_message(filters.command("character"))
async def character_command(client, message):
    if not message.from_user:
        await message.reply_text("❌ Помилка: не вдалося визначити користувача.")
        return
    user_id = str(message.from_user.id)
    today = datetime.now().date().isoformat()
    user_info = character_data.get(user_id, {})
    if user_info.get("last_character_date") == today:
        await message.reply_text("🔁 Ви вже отримували персонажа сьогодні! Спробуйте завтра.")
        return
    try:
        url = f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q=cartoon+character&image_type=photo&orientation=horizontal&safesearch=true&per_page=50"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            hits = data.get("hits", [])
            if hits:
                img_url = random.choice(hits)["webformatURL"]
                user_info["last_character_date"] = today
                character_data[user_id] = user_info
                save_character_data(character_data)
                await message.reply_photo(img_url, caption="сьогодні ви")
                return
            else:
                await message.reply_text("Не знайдено жодної картинки персонажа на Pixabay.")
                return
        else:
            await message.reply_text(f"Pixabay API error: {resp.status_code}")
    except Exception as e:
        await message.reply_text(f"Помилка пошуку картинки: {e}")

@app.on_message(filters.command("horoscope"))
async def horoscope_command(client, message):
    if not message.from_user:
        await message.reply_text("❌ Помилка: не вдалося визначити користувача.")
        return
    user_id = str(message.from_user.id)
    today = datetime.now().date().isoformat()
    user_info = character_data.get(user_id, {})
    if user_info.get("last_horoscope_date") == today:
        await message.reply_text("🔁 Ви вже отримували гороскоп сьогодні! Спробуйте завтра.")
        return
    prediction = random.choice(horoscope_predictions)
    # Оновлюємо дату останнього гороскопу
    user_info["last_horoscope_date"] = today
    character_data[user_id] = user_info
    save_character_data(character_data)
    await message.reply_text(f"🌟 Твій міні-гороскоп:\n{prediction}")

@app.on_message(filters.command("yesno"))
async def yesno_command(client, message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply_text("❓ Напиши питання після команди! Наприклад: /yesno Чи буде дощ?")
        return
    question = args[1].strip()
    answer = random.choice(yesno_answers)
    await message.reply_text(f"❓ {question}\n💡 {answer}")

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
            # Видаляємо повідомлення з кнопками, щоб не дублювати топ
            try:
                await msg.delete()
            except Exception as e:
                logger.warning(f"Не вдалося видалити повідомлення з кнопками: {e}")
            await process_show_top_users(msg.reply_text, client)
        elif data == "karma":
            await process_show_karma(user_id, msg.reply_text, client)
        elif data == "go":
            # Перевіряємо, чи користувач є адміністратором
            if not is_admin(callback_query.from_user):
                await msg.reply_text("⛔️ Команда доступна лише для адміністраторів")
                await callback_query.answer()
                return
            
            # Видаляємо повідомлення користувача, якщо потрібно
            await callback_query.message.delete()
            await process_luckypoll(client)
        elif data == "character":
            # Використовуємо ту ж логіку, що й у команді, для обмеження раз на день
            class DummyMessage:
                def __init__(self, from_user, reply_photo, reply_text):
                    self.from_user = from_user
                    self.reply_photo = reply_photo
                    self.reply_text = reply_text
            dummy_msg = DummyMessage(callback_query.from_user, msg.reply_photo, msg.reply_text)
            await character_command(client, dummy_msg)
        elif data == "horoscope":
            await horoscope_command(client, msg)
        elif data == "yesno":
            await msg.reply_text("Використай /yesno та своє питання! Наприклад: /yesno Чи буде щастя?")
        else:
            await msg.reply_text("Невідома команда з кнопки.")
    except Exception as e:
        logger.error(f"Помилка в callback: {e}")
        await msg.reply_text(f"Виникла помилка: {e}")

    await callback_query.answer()

@app.on_message(filters.command("admin"))
async def admin_panel(client, message):
    if not message.from_user:
        await message.reply_text("❌ Помилка: не вдалося визначити користувача. Спробуйте написати боту в приватному повідомленні.")
        return
        
    if not is_admin(message.from_user):
        await message.reply_text("⛔️ Доступ лише для адміністраторів")
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

    # Якщо файл з персонажами не існує, створити пустий
    if not os.path.exists(character_data_file):
        with open(character_data_file, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=4)

    print(f"{bot_name} запущено...")
    try:
        app.run()
    except Exception as e:
        if "FLOOD_WAIT" in str(e):
            print("⚠️ Telegram заблокував бота через занадто часті спроби.")
            print("⏳ Зачекайте 30-40 хвилин перед наступною спробою.")
            print(f"📝 Помилка: {e}")
        else:
            print(f"❌ Помилка запуску: {e}")
