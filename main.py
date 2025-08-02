from keep_alive import keep_alive
import telebot
import pandas as pd
import datetime
import os

# إعدادات البوت
TOKEN = os.getenv('TOKEN')
ADMIN_ID = 615135746  # رقمك كمسؤول
FILE_PATH = 'data.xlsx'
LOG_FILE = 'log.txt'

bot = telebot.TeleBot(TOKEN)

# تحميل بيانات العائلة من ملف Excel (محلي)
def load_data():
    for i in range(5):  # نجرب أول 5 صفوف كـ header
        df = pd.read_excel(FILE_PATH, header=i)
        if 'رقم الهوية' in df.columns:
            print(f"✅ تم العثور على الأعمدة في الصف رقم {i}")
            return df
    print("❌ لم يتم العثور على الأعمدة المطلوبة في الملف.")
    return None

df = load_data()
if df is None:
    print("إيقاف البرنامج بسبب خطأ في تحميل البيانات.")
    exit()

# رسالة الطلب للمتابعة
follow_msg = (
    "📢 قبل الاستعلام، يرجى متابعة صفحات مجلس عائلة الكحلوت الرسمية:\n\n"
    "🔵 فيسبوك: https://www.facebook.com/share/1VkzmzQ1oC/\n"
    "🟣 إنستغرام: https://www.instagram.com/kahlout.family\n"
    "🟢 واتساب: https://chat.whatsapp.com/BBSd4bcFqKe0tqbjA281Az\n"
    "📣 تيليجرام: https://t.me/Kahlout_family\n\n"
    "بعد المتابعة، أرسل رقم الهوية للاستعلام:"
)

# بدء المحادثة
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = message.from_user
    bot.reply_to(message, f"مرحبًا {user.first_name} 👋\n\n{follow_msg}")

# تسجيل الدخول البسيط (admin فقط)
logged_in_users = set()

@bot.message_handler(commands=['login'])
def login(message):
    try:
        user_id = message.from_user.id
        args = message.text.split()
        if len(args) != 3:
            bot.reply_to(message, "يرجى إرسال الأمر بالصيغ التالية:\n/login username password")
            return
        username, password = args[1], args[2]
        if username == "lamish" and password == "lamish75":
            logged_in_users.add(user_id)
            bot.reply_to(message, "✅ تم تسجيل دخول المسؤول بنجاح!")
        else:
            bot.reply_to(message, "❌ بيانات الدخول غير صحيحة.")
    except Exception as e:
        bot.reply_to(message, f"حدث خطأ: {e}")

@bot.message_handler(commands=['logout'])
def logout(message):
    user_id = message.from_user.id
    if user_id in logged_in_users:
        logged_in_users.remove(user_id)
        bot.reply_to(message, "✅ تم تسجيل الخروج.")
    else:
        bot.reply_to(message, "أنت لست مسجلاً الدخول.")

# البحث عن رقم الهوية
@bot.message_handler(func=lambda message: True)
def handle_id_search(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    text = message.text.strip()

    # تجاهل أوامر خاصة
    if text.startswith('/'):
        return

    if not text.isdigit():
        bot.reply_to(message, "❌ يرجى إدخال رقم الهوية فقط (أرقام فقط).")
        return

    match = df[df['رقم الهوية'].astype(str) == text]

    if not match.empty:
        row = match.iloc[0]
        response = (
            f"✅ تم العثور على البيانات:\n\n"
            f"👤 الاسم: {row.get('اسم رب الاسرة', 'غير متوفر')}\n"
            f"🆔 رقم الهوية: {row.get('رقم الهوية', 'غير متوفر')}\n"
            f"📞 رقم التواصل: {row.get('رقم التواصل', 'غير متوفر')}\n"
            f"👪 عدد أفراد الأسرة: {row.get('عدد افراد الاسرة', 'غير متوفر')}\n"
            f"📍 العنوان: {row.get('العنوان', 'غير متوفر')}\n"
            f"📝 ملاحظات: {row.get('ملاحظات', 'لا توجد')}"
        )
        bot.reply_to(message, response)
    else:
        bot.reply_to(message, (
            "❌ لم يتم العثور على رقم الهوية.\n"
            "🗂 تواصل مع ممثل فرعك لإضافة رب الأسرة إلى كشف عائلة الكحلوت في قطاع غزة."
        ))

    # تسجيل الاستعلام في ملف اللوق
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{now}] {user_name} ({user_id}) بحث عن: {text}\n")

    # تنبيه المسؤول (لو سجل دخول)
    if user_id in logged_in_users:
        alert = f"📥 تم استعلام جديد من @{user_name} (ID: {user_id}): {text}"
        bot.send_message(ADMIN_ID, alert)

import threading

# تشغيل الخادم في خيط منفصل
server_thread = threading.Thread(target=keep_alive)
server_thread.daemon = True
server_thread.start()

print("✅ البوت يعمل الآن... اضغط Ctrl+C للإيقاف.")
bot.infinity_polling()
