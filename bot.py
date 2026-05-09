import telebot
import random
import string
import time
import hashlib
import hmac
import base64
import struct
from telebot import types
from datetime import datetime
from flask import Flask
from threading import Thread

# ================= CONFIG =================
TOKEN = "8783194900:AAH__MsqIgqwKn_-Pzg2NdxQsIJ1OjvAVY8"
ADMIN_ID = 8783194900
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
app = Flask('')

# ডাটাবেজ এবং সেটিংস
config = {
    "rates": {"IG 2FA": 0.025, "IG Cookies": 0.034, "FB 30F": 0.033},
    "ref_bonus": 0.020,
    "status": {"ig": True, "fb": True, "cook": True},
    "sheets": {"save": "Not Set", "source": "Not Set"}
}

# ================= HELPERS (আপনার লজিক) =================
def generate_random_pass():
    letters = string.ascii_lowercase
    random_name = ''.join(random.choice(letters) for i in range(7)).capitalize()
    day = datetime.now().strftime("%d")
    return f"{random_name}{day}"

def get_totp_code(secret):
    try:
        clean_sec = ''.join(c for c in secret if c.isalnum()).upper()
        key = base64.b32decode(clean_sec + '=' * ((8 - len(clean_sec) % 8) % 8))
        counter = struct.pack('>Q', int(time.time() // 30))
        hmac_hash = hmac.new(key, counter, hashlib.sha1).digest()
        offset = hmac_hash[-1] & 0x0F
        code = (struct.unpack('>I', hmac_hash[offset:offset+4])[0] & 0x7FFFFFFF) % 1000000
        return f"{code:06d}"
    except:
        return "❌ Invalid Secret Key"

# ================= MENUS (✅ Reply & Inline) =================
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📋 কাজ", "💰 ব্যালেন্স")
    markup.add("🏦 টাকা উত্তোলন", "🏆 লিডারবোর্ড")
    markup.add("👥 রেফার", "📞 সাপোর্ট")
    return markup

def admin_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("✅ সাকসেস রিপোর্ট সেন্ড", "❌ রিজেক্ট রিপোর্ট সেন্ড")
    markup.add("⚙️ সেটিংস ও শিট লিঙ্ক", "📊 চেক স্ট্যাটাস")
    markup.add("🔙 মেইন মেনু")
    return markup

# ================= START & WORK =================
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, f"👋 স্বাগতম!\nআজকের র্যান্ডম পাসওয়ার্ড: <b>{generate_random_pass()}</b>", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "📋 কাজ")
def task_list(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(f"📸 Instagram 2FA (${config['rates']['IG 2FA']})", callback_data="t_ig"),
        types.InlineKeyboardButton(f"🍪 Instagram Cookies (${config['rates']['IG Cookies']})", callback_data="t_cook"),
        types.InlineKeyboardButton(f"📘 FB 30 Friend (Hotmail) (${config['rates']['FB 30F']})", callback_data="t_fb")
    )
    bot.send_message(message.chat.id, "⚡️ কাজ সিলেক্ট করুন:", reply_markup=markup)

# ২এফএ ওটিপি জেনারেটর লজিক
@bot.callback_query_handler(func=lambda call: call.data == "t_ig")
def ig_start(call):
    p = generate_random_pass()
    msg = bot.send_message(call.message.chat.id, f"🔐 **Instagram 2FA**\nপাসওয়ার্ড: `{p}`\n\nকোড পেতে আপনার **2FA Secret Key** টি পাঠান:")
    bot.register_next_step_handler(msg, show_otp)

def show_otp(message):
    code = get_totp_code(message.text)
    bot.send_message(message.chat.id, f"✅ আপনার ওটিপি কোড: <code>{code}</code>\nআইডি রেডি করে জমা দিন।")

# ================= ADMIN ACTIONS =================
@bot.message_handler(commands=['admin'])
def admin_start(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "👑 অ্যাডমিন প্যানেলে স্বাগতম", reply_markup=admin_menu())

@bot.message_handler(func=lambda m: m.text == "✅ সাকসেস রিপোর্ট সেন্ড")
def success_report(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "📝 সাকসেস ইউজারনেম লিস্ট দিন (এক লাইনে একটি):")
        bot.register_next_step_handler(msg, send_bulk_success)

def send_bulk_success(message):
    unames = message.text.split('\n')
    for u in unames:
        u = u.strip()
        if u:
            # সাকসেস মেসেজ ফরম্যাট
            bot.send_message(message.chat.id, f"✅ <b>Report approved, +$0.034</b>\n🆔 <b>Username:</b> <code>{u}</code>\n✉ <b>Comment:</b> আপনার কাজ সফলভাবে গ্রহণ করা হয়েছে।")
    bot.send_message(message.chat.id, "🏁 রিপোর্ট পাঠানোর কাজ সম্পন্ন হয়েছে!")

@bot.message_handler(func=lambda m: m.text == "⚙️ সেটিংস ও শিট লিঙ্ক")
def settings_panel(message):
    if message.from_user.id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔗 Edit Save Sheet URL", callback_data="edit_save"))
        markup.add(types.InlineKeyboardButton("💰 Edit Rates", callback_data="edit_rates"))
        bot.send_message(message.chat.id, "⚙️ কনফিগারেশন পরিবর্তন করুন:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "edit_save")
def edit_url(call):
    msg = bot.send_message(call.message.chat.id, "📩 নতুন Save Sheet URL টি পাঠান:")
    bot.register_next_step_handler(msg, update_url)

def update_url(message):
    config["sheets"]["save"] = message.text
    bot.send_message(message.chat.id, "✅ গুগল শিট URL আপডেট হয়েছে!")

# ================= SERVER & RUN =================
@app.route('/')
def home(): return "Bot is Online!"

def run(): app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    print("বট সচল হয়েছে...")
    bot.infinity_polling()
        
