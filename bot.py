import telebot
from telebot import types
import random
import time
from datetime import datetime
from flask import Flask
from threading import Thread

# --- কনফিগারেশন ও টোকেন ---
BOT_TOKEN = '8783194900:AAH__MsqIgqwKn_-Pzg2NdxQsIJ1OjvAVY8'
ADMIN_ID = 8783194900 
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

# --- ডাইনামিক ডাটাবেজ ---
config = {
    "rates": {
        "ig_2fa": 0.025,
        "ig_2fa_email": 0.024,
        "ig_cookies": 0.034,
        "fb_30f": 0.033
    },
    "ref_bonus": 0.020,
    "status": {"ig_2fa": True, "ig_cookies": True, "fb": True},
    "sheets": {"source": "Not Set", "save": "Not Set"},
    "submit_link": "https://submitwork.org"
}

users = {} # {user_id: {'balance': 0.0, 'done': 0, 'ref_by': None}}
daily_logs = [] # [ {'user': name, 'task': type, 'data': info} ]

# --- পাসওয়ার্ড লজিক (৭ অক্ষর + তারিখ) ---
def get_dynamic_pass():
    names = ["Tanjimz", "Saidurz", "Rifatxx", "Siampro", "Mimlove", "Rohanzx", "Anikpro"]
    day = datetime.now().strftime("%d")
    return f"{random.choice(names)}{day}"

# --- মেইন মেনু (Reply Keyboard ✅) ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add('✅ কাজ', '👥 রেফার', '💰 ব্যালেন্স', '🏆 লিডারবোর্ড', '👤 প্রোফাইল')
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    if uid not in users:
        args = message.text.split()
        ref_by = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
        users[uid] = {'balance': 0.0, 'done': 0, 'ref_by': ref_by}
    
    bot.send_message(message.chat.id, f"👋 স্বাগতম!\nআজকের পাসওয়ার্ড: **{get_dynamic_pass()}**", 
                     parse_mode="Markdown", reply_markup=main_menu())

# --- কাজের মেনু ---
@bot.message_handler(func=lambda m: m.text == '✅ কাজ')
def work_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(f"🔐 Instagram 2FA (${config['rates']['ig_2fa']})", callback_data="t_2fa"),
        types.InlineKeyboardButton(f"📧 Instagram 2FA (Email) (${config['rates']['ig_2fa_email']})", callback_data="t_2fa_e"),
        types.InlineKeyboardButton(f"🍪 Instagram Cookies (${config['rates']['ig_cookies']})", callback_data="t_cook"),
        types.InlineKeyboardButton(f"📘 Facebook 30 Friend (${config['rates']['fb_30f']})", callback_data="t_fb")
    )
    bot.send_message(message.chat.id, "👇 আপনার টাস্ক বেছে নিন:", reply_markup=markup)

# --- ইনলাইন বাটন হ্যান্ডলার (Fast Response) ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('t_'))
def handle_tasks(call):
    bot.answer_callback_query(call.id)
    task_map = {"t_2fa": "Instagram 2FA", "t_cook": "Instagram Cookies", "t_fb": "FB 30 Friend"}
    bot.send_message(call.message.chat.id, f"আপনি **{task_map.get(call.data, 'Task')}** শুরু করেছেন। কাজ জমা দিন।")

# --- অ্যাডমিন প্যানেল (Categorized) ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🚫 Task Control", callback_data="adm_ctrl"),
            types.InlineKeyboardButton("✅ Approve Report", callback_data="adm_apprv"),
            types.InlineKeyboardButton("📊 Daily Logs", callback_data="adm_logs"),
            types.InlineKeyboardButton("⚙️ Settings & URL", callback_data="adm_sets")
        )
        bot.send_message(message.chat.id, "👑 **Admin Control Center**", reply_markup=markup)

# --- সেটিংস ও শিট ইউআরএল এডিট ---
@bot.callback_query_handler(func=lambda call: call.data == "adm_sets")
def admin_settings(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔗 Edit Save Sheet URL", callback_data="set_save_url"))
    markup.add(types.InlineKeyboardButton("💰 Edit Rates", callback_data="set_rates"))
    bot.edit_message_text("⚙️ **Settings & URL Control**", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "set_save_url")
def set_url(call):
    msg = bot.send_message(call.message.chat.id, "📩 নতুন Save Sheet URL টি দিন:")
    bot.register_next_step_handler(msg, update_url)

def update_url(message):
    config["sheets"]["save"] = message.text
    bot.send_message(message.chat.id, "✅ Google Sheet URL আপডেট হয়েছে।")

# --- রিপোর্ট এপ্রুভাল (সাকসেস মেসেজ লজিক) ---
@bot.callback_query_handler(func=lambda call: call.data == "adm_apprv")
def approve_init(call):
    msg = bot.send_message(call.message.chat.id, "📝 সাকসেস ইউজারনেম লিস্ট দিন (এক লাইনে একটি):")
    bot.register_next_step_handler(msg, approve_process)

def approve_process(message):
    names = message.text.split('\n')
    for name in names:
        # ইউজারের কাছে সাকসেস মেসেজ
        msg_text = f"✅ **Report approved, +$0.034**\n🆔 **Username:** `{name.strip()}`\n✉ **Comment:** আপনার কাজ সফলভাবে গ্রহণ করা হয়েছে।"
        bot.send_message(message.chat.id, msg_text, parse_mode="Markdown")
        # এখানে ডাটাবেজ আপডেট ও রেফারেল বোনাস লজিক কাজ করবে
    bot.send_message(message.chat.id, "🏁 রিপোর্ট প্রসেস সম্পন্ন!")

# --- ২৪ ঘণ্টা লাইভ রাখার সার্ভার ---
@app.route('/')
def home(): return "Bot is Active!"

def run(): app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    print("বট সচল হয়েছে...")
    bot.infinity_polling()
      
