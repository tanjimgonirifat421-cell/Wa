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

# ================= CONFIGURATION =================
TOKEN = "8783194900:AAH__MsqIgqwKn_-Pzg2NdxQsIJ1OjvAVY8"
ADMIN_ID = 8783194900
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
app = Flask('')

# Default Configuration
config = {
    "rates": {"IG 2FA": 0.025, "IG Cookies": 0.034, "FB 30F": 0.033},
    "sheets": {"save": "Not Set", "source": "Not Set"}
}

# ================= HELPERS =================

# ৭ অক্ষরের নাম + তারিখ দিয়ে র্যান্ডম পাসওয়ার্ড
def generate_random_pass():
    letters = string.ascii_lowercase
    random_name = ''.join(random.choice(letters) for i in range(7)).capitalize()
    day = datetime.now().strftime("%d")
    return f"{random_name}{day}"

# ওটিপি জেনারেটর (Internal Algorithm)
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

# ================= KEYBOARDS (Reply ✅) =================

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📋 Tasks", "💰 Balance")
    markup.add("🏦 Withdraw", "🏆 Leaderboard")
    markup.add("👥 Refer", "📞 Support")
    return markup

def task_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add("📸 Instagram 2FA", "🍪 Instagram Cookies", "📘 FB 30 Friend (Hotmail)", "🔙 Back to Menu")
    return markup

def admin_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("✅ Send Success Report", "❌ Send Reject Report")
    markup.add("⚙️ Settings & URL", "📊 Check Status", "🔙 Back to Menu")
    return markup

# ================= BOT HANDLERS =================

@bot.message_handler(commands=['start'])
def welcome(message):
    user_name = message.from_user.first_name
    bot.send_message(message.chat.id, f"Welcome, <b>{user_name}</b>! Start your work from the menu below.", reply_markup=main_menu())

# --- Task Sub-Menu Logic ---
@bot.message_handler(func=lambda m: m.text == "📋 Tasks")
def show_tasks(message):
    bot.send_message(message.chat.id, "Select your task category:", reply_markup=task_menu())

@bot.message_handler(func=lambda m: m.text == "🔙 Back to Menu")
def back_to_main(message):
    bot.send_message(message.chat.id, "Returning to main menu...", reply_markup=main_menu())

# --- Instagram 2FA Logic ---
@bot.message_handler(func=lambda m: m.text == "📸 Instagram 2FA")
def ig_2fa_task(message):
    new_pass = generate_random_pass()
    text = (f"🔐 <b>Instagram 2FA Task</b>\n\n"
            f"🔑 <b>Today's Password:</b> <code>{new_pass}</code>\n\n"
            f"To get your OTP, click the button below or send your 2FA Secret Key.")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔐 Get 2FA OTP", callback_data="get_otp_flow"))
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "get_otp_flow")
def ask_secret(call):
    msg = bot.send_message(call.message.chat.id, "📩 Please send your <b>2FA Secret Key</b>:")
    bot.register_next_step_handler(msg, process_otp)

def process_otp(message):
    secret = message.text.strip()
    otp_code = get_totp_code(secret)
    bot.send_message(message.chat.id, f"✅ <b>Your OTP Code:</b> <code>{otp_code}</code>\nNow login and submit your username.")

# --- FB 30 Friend (Hotmail Source) ---
@bot.message_handler(func=lambda m: m.text == "📘 FB 30 Friend (Hotmail)")
def fb_task(message):
    # এখানে আপনার সোর্স শিট থেকে মেইল তুলে দেওয়ার লজিক থাকবে
    bot.send_message(message.chat.id, "📦 Fetching a fresh Hotmail for you...\n\n(Feature linked to Source Sheet)")

# ================= ADMIN PANEL =================

@bot.message_handler(commands=['admin'])
def admin_start(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "👑 <b>Admin Control Panel</b>", reply_markup=admin_menu())

@bot.message_handler(func=lambda m: m.text == "✅ Send Success Report")
def bulk_report(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "📝 Send me the list of <b>Usernames</b> (One per line):")
        bot.register_next_step_handler(msg, process_bulk_success)

def process_bulk_success(message):
    user_list = message.text.split('\n')
    for username in user_list:
        username = username.strip()
        if username:
            # সাকসেস মেসেজ ফাটানোর ফরম্যাট
            bot.send_message(message.chat.id, f"✅ <b>Report approved, +$0.034</b>\n🆔 <b>Username:</b> <code>{username}</code>\n✉ <b>Comment:</b> Your work has been successfully accepted.")
    bot.send_message(message.chat.id, "🏁 Bulk reporting completed!")

# ================= WEB SERVER =================
@app.route('/')
def home(): return "Bot is Online!"
def run(): app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    bot.infinity_polling()
    
