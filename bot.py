import telebot
import cv2
import numpy as np
import tensorflow as tf
import random
from telebot import types

# ================== SOZLAMALAR ==================
TOKEN = "8148211584:AAEAvV5xJFbCS5tFRaQIOZscx80-6HASjk0"

model = tf.keras.models.load_model("cat_dog_modell.keras")
print("✅ Model yuklandi!")

class_names = ['mushuk', 'it']

bot = telebot.TeleBot(TOKEN)
user_states = {}

# ================== MENYULAR ==================
def show_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📸 Mushuk & It taniydigan")
    markup.add("🎮 O'yinlar")
    markup.add("ℹ️ Yordam")
    bot.send_message(chat_id, "🏠 Asosiy menyu", reply_markup=markup)

def show_games_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("1️⃣ Men topaman")
    markup.add("2️⃣ Bot topadi")
    markup.add("🔙 Orqaga")
    bot.send_message(chat_id, "🎮 O'yin tanlang:", reply_markup=markup)

# ================== START ==================
@bot.message_handler(commands=['start'])
def start(message):
    user_states[message.chat.id] = {}
    show_main_menu(message.chat.id)

# ================== FOTO ==================
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.chat.id

    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)

        np_arr = np.frombuffer(downloaded, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (224, 224))
        img = img / 255.0
        img = np.expand_dims(img, axis=0)

        prediction = model.predict(img, verbose=0)
        confidence = float(np.max(prediction))

        if confidence < 0.7:
            bot.send_message(user_id, "❌ Tushunarsiz rasm")
        else:
            result = class_names[np.argmax(prediction)]
            bot.send_message(user_id, f"✅ {result.upper()} ({confidence*100:.1f}%)")

    except Exception as e:
        bot.send_message(user_id, f"❌ Xato: {e}")

# ================== TEXT ==================
@bot.message_handler(content_types=['text'])
def handle_text(message):
    text = message.text
    chat_id = message.chat.id

    print("TEXT:", text)

    if text.startswith("/"):
        return

    # ===== MENYU =====
    if "Mushuk & It" in text:
        bot.send_message(chat_id, "📸 Rasm yuboring")
        return

    if "O'yinlar" in text:
        show_games_menu(chat_id)
        return

    if "Yordam" in text:
        bot.send_message(chat_id, "🔙 Orqaga tugmasini bosib qayting")
        return

    if "Orqaga" in text:
        show_main_menu(chat_id)
        return

    # ===== 1️⃣ MEN TOPAMAN =====
    if "Men topaman" in text:
        son = random.randint(1, 10)
        user_states[chat_id] = {"game": "user_guess", "son": son, "urinish": 0}
        bot.send_message(chat_id, "1 dan 10 gacha bolgan sonlardan ixtiyoriy 1 ta son o'yladim ")
        return

    if chat_id in user_states and user_states[chat_id].get("game") == "user_guess":
        try:
            guess = int(text)
            user_states[chat_id]["urinish"] += 1

            if guess == user_states[chat_id]["son"]:
                bot.send_message(chat_id, f"🎉 Topdingiz! ({user_states[chat_id]['urinish']} urinish)")
                del user_states[chat_id]
                show_games_menu(chat_id)
            elif guess < user_states[chat_id]["son"]:
                bot.send_message(chat_id, "📈 Kattaroq")
            else:
                bot.send_message(chat_id, "📉 Kichikroq")
        except:
            bot.send_message(chat_id, "Faqat son yozing")
        return

    # ===== 2️⃣ BOT TOPADI =====
    if "Bot topadi" in text:
        user_states[chat_id] = {
            "game": "bot_guess",
            "bosh": 1,
            "oxir": 10,
            "taxmin": 0
        }
        bot.send_message(chat_id, "1 dan 10 gacha son o'ylang va 'boshladik' deb yozing")
        return

    if chat_id in user_states and user_states[chat_id].get("game") == "bot_guess":
        state = user_states[chat_id]

        if text.lower() == "boshladik":
            tax = random.randint(state["bosh"], state["oxir"])
            state["current"] = tax
            state["taxmin"] += 1

            bot.send_message(chat_id, f"Siz {tax} ni o'yladingizmi?\n\n(t) to'g'ri\n(-) kichikroq\n(+) kattaroq")
            return

        if text.lower() == "t":
            bot.send_message(chat_id, f"🎉 Topdim! {state['taxmin']} urinishda!")
            del user_states[chat_id]
            show_games_menu(chat_id)
            return

        elif text == "-":
            state["oxir"] = state["current"] - 1

        elif text == "+":
            state["bosh"] = state["current"] + 1

        else:
            bot.send_message(chat_id, "Faqat t / - / + yozing")
            return

        if state["bosh"] > state["oxir"]:
            bot.send_message(chat_id, "❗ Xatolik! Siz noto‘g‘ri yo‘l ko‘rsatdingiz")
            del user_states[chat_id]
            show_games_menu(chat_id)
            return

        tax = random.randint(state["bosh"], state["oxir"])
        state["current"] = tax
        state["taxmin"] += 1

        bot.send_message(chat_id, f"Siz {tax} ni o'yladingizmi?\n\n(t) / (-) / (+)")
        return

# ================== RUN ==================
print("🤖 Bot ishga tushdi...")
bot.infinity_polling()