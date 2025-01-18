import telebot
import sqlite3
import random
import string
from flask import Flask, request
import os

# تنظیمات اولیه
TOKEN = '7702294081:AAHhFAmPq3BAr_ICbTDHM0f3zVAQ64jH3mM'  # توکن ربات
bot = telebot.TeleBot(TOKEN)
BOT_USERNAME = 'nodeirrbot'  # نام کاربری ربات (بدون @)

# لیست ادمین‌ها
admin_ids = [7439083383, 7124196933, 7014136530]

# شناسه کانال‌ها
CHANNELS = ['@filmir19', '@nodeirrr', '@javayyez']

# بررسی اینکه آیا کاربر ادمین هست یا نه
def is_admin(user_id):
    return user_id in admin_ids

# شناسه ادمین
admin_id = 7439083383

# اتصال به دیتابیس
conn = sqlite3.connect('files.db', check_same_thread=False)
cursor = conn.cursor()

# ایجاد جدول دیتابیس
cursor.execute("""
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id TEXT,
    file_type TEXT,
    unique_id TEXT UNIQUE
)
""")
conn.commit()

# تابع تولید شناسه یکتا
def generate_unique_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

# تابع بررسی عضویت کاربر در کانال‌ها
def is_user_in_channels(user_id):
    for channel in CHANNELS:
        try:
            # بررسی وضعیت عضویت کاربر
            status = bot.get_chat_member(channel, user_id).status
            if status not in ['member', 'administrator', 'creator']:
                return False
        except Exception as e:
            print(f"Error checking channel {channel}: {e}")
            return False
    return True

# ذخیره فایل‌های ارسال شده توسط ادمین
@bot.message_handler(content_types=['video', 'photo', 'document', 'audio', 'voice', 'live_video'])
def save_file(message):
    if message.chat.type == 'private' and is_admin(message.from_user.id):  # بررسی ادمین بودن
        # تشخیص نوع فایل و گرفتن شناسه آن
        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
            file_type = 'photo'
        elif message.content_type == 'video':
            file_id = message.video.file_id
            file_type = 'video'
        elif message.content_type == 'document':
            file_id = message.document.file_id
            file_type = 'document'
        elif message.content_type == 'audio':
            file_id = message.audio.file_id
            file_type = 'audio'
        elif message.content_type == 'voice':
            file_id = message.voice.file_id
            file_type = 'voice'
        elif message.content_type == 'live_video':
            file_id = message.live_video.file_id
            file_type = 'live_video'
        else:
            bot.reply_to(message, "نوع فایل پشتیبانی نمی‌شود!")
            return

        # تولید شناسه یکتا و ذخیره در دیتابیس
        unique_id = generate_unique_id()
        try:
            cursor.execute("INSERT INTO files (file_id, file_type, unique_id) VALUES (?, ?, ?)", (file_id, file_type, unique_id))
            conn.commit()

            # تولید لینک یکتا
            link = f"https://t.me/{BOT_USERNAME}?start={unique_id}"
            bot.send_message(admin_id, f"فایل ذخیره شد!\nلینک فایل: {link}")
        except sqlite3.IntegrityError:
            bot.send_message(admin_id, "خطا: مشکلی در ذخیره فایل رخ داده است. لطفاً دوباره تلاش کنید.")
    else:
        bot.reply_to(message, "شما اجازه ارسال فایل ندارید!")

# ارسال فایل به کاربران از طریق لینک
@bot.message_handler(commands=['start'])
def send_file_by_link(message):
    args = message.text.split()
    if len(args) > 1:  # بررسی وجود شناسه یکتا در لینک
        unique_id = args[1]
        cursor.execute("SELECT file_id, file_type FROM files WHERE unique_id = ?", (unique_id,))
        file_data = cursor.fetchone()
        if file_data:
            file_id, file_type = file_data
            if is_user_in_channels(message.from_user.id):  # بررسی عضویت در کانال‌ها
                # ارسال فایل به کاربر
                if file_type == 'photo':
                    bot.send_photo(message.chat.id, file_id, caption="این فایل برای شما ارسال شد!")
                elif file_type == 'video':
                    bot.send_video(message.chat.id, file_id, caption="این فایل برای شما ارسال شد!")
                elif file_type == 'document':
                    bot.send_document(message.chat.id, file_id, caption="این فایل برای شما ارسال شد!")
                elif file_type == 'audio':
                    bot.send_audio(message.chat.id, file_id, caption="این فایل برای شما ارسال شد!")
                elif file_type == 'voice':
                    bot.send_voice(message.chat.id, file_id, caption="این فایل برای شما ارسال شد!")
                elif file_type == 'live_video':
                    bot.send_video(message.chat.id, file_id, caption="این راند ویدیو برای شما ارسال شد!")
            else:
                # ارسال پیام عضویت در کانال‌ها
                channels_list = "\n".join([f"{channel}" for channel in CHANNELS])
                bot.reply_to(message, f"برای مشاهده فایل، ابتدا در کانال‌های زیر عضو شوید:\n{channels_list}")
        else:
            bot.reply_to(message, "متأسفم، فایلی با این لینک وجود ندارد.")
    else:
        bot.reply_to(message, "سلام! برای استفاده از ربات، لینک‌های فایل را دریافت کنید.")

# دستورات ادمین برای اضافه و حذف کانال
@bot.message_handler(commands=['add_channel', 'remove_channel'])
def manage_channels(message):
    if is_admin(message.from_user.id):
        command, *args = message.text.split()
        if command == '/add_channel' and args:
            new_channel = args[0]
            if new_channel not in CHANNELS:
                CHANNELS.append(new_channel)
                bot.reply_to(message, f"کانال {new_channel} با موفقیت به لیست اضافه شد.")
            else:
                bot.reply_to(message, "این کانال قبلاً اضافه شده است.")
        elif command == '/remove_channel' and args:
            channel_to_remove = args[0]
            if channel_to_remove in CHANNELS:
                CHANNELS.remove(channel_to_remove)
                bot.reply_to(message, f"کانال {channel_to_remove} با موفقیت از لیست حذف شد.")
            else:
                bot.reply_to(message, "این کانال در لیست وجود ندارد.")
        else:
            bot.reply_to(message, "لطفاً نام کانال را به درستی وارد کنید.")

# راه‌اندازی سرور Flask برای اطمینان از فعالیت ربات
app = Flask('')

@app.route('/')
def home():
    return "ربات فعال است!"

# تنظیم Webhook در Render
@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '!', 200

# تنظیم Webhook
@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    webhook_url = f'https://your-app-name.onrender.com/{TOKEN}'
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    return 'Webhook set successfully!', 200

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

if __name__ == "__main__":
    run_flask()
