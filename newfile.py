import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import random
import string
import pyotp  # লাইভ 2FA কোড বের করার জন্য

# বটের কনফিগারেশন
API_TOKEN = '8848253078:AAHxbEqZFPypogFA6IzO2oeXYxoXMYQvMNk'
ADMIN_CHAT_ID = 7993941422  

bot = telebot.TeleBot(API_TOKEN)

# আপনার সেটিংস
FIXED_PASSWORD = "jubayer@22" 
WORK_REWARD = 3.40  
REFER_BONUS = 2.00  

# ডাটাবেজ (মেমোরি)
user_balances = {}
user_steps = {}
user_data = {}
withdraw_data = {}
referred_users = {}

def generate_unique_username():
    prefix = "oeaukodw"
    random_str = ''.join(random.choices(string.ascii_lowercase, k=6))
    return f"{prefix}{random_str}"

def get_main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("💼 কাজ"), KeyboardButton("💰 ব্যালেন্স"))
    markup.add(KeyboardButton("💳 টাকা উত্তোলন"), KeyboardButton("🏆 লিডারবোর্ড"))
    markup.add(KeyboardButton("📞 সাপোর্ট"), KeyboardButton("👥 Invite & Earn"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    text_args = message.text.split()
    
    if chat_id not in user_balances:
        user_balances[chat_id] = 0.00
        
        if len(text_args) > 1:
            referrer_id = text_args[1]
            try:
                referrer_id = int(referrer_id)
                if referrer_id != chat_id:
                    if chat_id not in referred_users:
                        referred_users[chat_id] = referrer_id
                        
                        if referrer_id not in user_balances:
                            user_balances[referrer_id] = 0.00
                        user_balances[referrer_id] += REFER_BONUS
                        
                        try:
                            bot.send_message(referrer_id, f"🎉 আপনার রেফার লিংকে একজন নতুন সদস্য জয়েন করেছে! আপনার অ্যাকাউন্টে সাথে সাথে ৳{REFER_BONUS:.2f} যোগ করা হয়েছে।")
                        except Exception:
                            pass
            except ValueError:
                pass

    bot.send_message(chat_id, "👋 স্বাগতম! অনুগ্রহ করে নিচের মেনু থেকে অপশন নির্বাচন করুন:", reply_markup=get_main_menu())

@bot.message_handler(regexp=r'/add_money_\d+')
def admin_add_money(message):
    if message.chat.id != ADMIN_CHAT_ID:
        return
        
    try:
        target_user_id = int(message.text.split('_')[2])
        if target_user_id not in user_balances:
            user_balances[target_user_id] = 0.00
            
        user_balances[target_user_id] += WORK_REWARD
        bot.reply_to(message, f"✅ ইউজার `{target_user_id}` এর অ্যাকাউন্টে ৳{WORK_REWARD:.2f} সফলভাবে যোগ করা হয়েছে।", parse_mode="Markdown")
        bot.send_message(target_user_id, f"🎉 অভিনন্দন! আপনার জমা দেওয়া কাজটি অ্যাডমিন চেক করে অ্যাপ্রুভ করেছে। আপনার ব্যালেন্সে ৳{WORK_REWARD:.2f} যোগ করা হয়েছে।")
    except Exception as e:
        bot.reply_to(message, f"❌ টাকা অ্যাড করা যায়নি। এরর: {e}")

@bot.message_handler(func=lambda message: message.text == "💼 কাজ")
def handle_kaaj(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton(f"⚡ ইনস্টাগ্রাম 2FA (৳{WORK_REWARD:.2f})"))
    markup.add(KeyboardButton("🔙 মেইন মেনু"))
    bot.reply_to(message, "⚡ যেকোনো একটি কাজ সিলেক্ট করুন ⤵️", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == f"⚡ ইনস্টাগ্রাম 2FA (৳{WORK_REWARD:.2f})")
def handle_instagram(message):
    chat_id = message.chat.id
    new_username = generate_unique_username()
    user_data[chat_id] = {'username': new_username}
    
    response_text = (
        f"👤 Username: `{new_username}`\n"
        f"🔒 Password: `{FIXED_PASSWORD}`\n\n"
        f"2FA Enable করে Secret Key পেলে নিচের বাটনে ক্লিক করুন।"
    )
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("🔐 2FA Secret Key আছে"))
    markup.add(KeyboardButton("🔙 মেইন মেনু"))
    bot.send_message(chat_id, response_text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🔐 2FA Secret Key আছে")
def ask_secret_key(message):
    chat_id = message.chat.id
    user_steps[chat_id] = 'WAITING_SECRET_KEY'
    bot.send_message(chat_id, "🔑 Instagram থেকে পাওয়া **2FA Secret Key** পুরোটা পেস্ট করে পাঠান (কোনো স্পেস ছাড়া):", parse_mode="Markdown")

# Secret Key গ্রহণ, লাইভ কোড জেনারেট এবং অ্যাডমিনকে পাঠানো
@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'WAITING_SECRET_KEY')
def process_secret_key(message):
    chat_id = message.chat.id
    secret_key = message.text.strip().replace(" ", "") # স্পেস থাকলে কেটে দেবে
    username = user_data.get(chat_id, {}).get('username', 'Unknown')
    
    try:
        # Secret Key থেকে বর্তমান লাইভ ৬ ডিজিটের কোড বের করা
        totp = pyotp.TOTP(secret_key)
        live_code = totp.now()
        
        # অ্যাডমিনকে কাজের রিপোর্ট পাঠানো (কোডসহ)
        admin_report = (
            f"📥 **নতুন কাজ জমা এসেছে!**\n\n"
            f"👤 কর্মী আইডি: `{chat_id}`\n"
            f"🏷️ Username: `{username}`\n"
            f"🔑 Password: `{FIXED_PASSWORD}`\n"
            f"🔐 2FA Secret: `{secret_key}`\n"
            f"🔢 **Live 2FA Code:** `{live_code}`\n\n"
            f"⚙️ **টাকা অ্যাড করতে নিচের লিংকে ক্লিক করুন:**\n"
            f"/add_money_{chat_id}"
        )
        try:
            bot.send_message(ADMIN_CHAT_ID, admin_report, parse_mode="Markdown")
        except Exception:
            pass

        # ইউজারকে কোডটি দেখানো
        user_response = (
            f"✅ **আপনার কাজটি সফলভাবে জমা নেওয়া হয়েছে!**\n\n"
            f"🔢 আপনার বর্তমান ২এফএ কোড: `{live_code}`\n\n"
            f"⚠️ কোডটি প্রতি ৩০ সেকেন্ড পর পর পরিবর্তন হয়। অ্যাডমিন অ্যাকাউন্টটি সম্পূর্ণ চেক করে আপনার ব্যালেন্সে টাকা যোগ করে দেবে।"
        )
        bot.send_message(chat_id, user_response, parse_mode="Markdown")
        
    except Exception as e:
        # যদি ইউজার ভুল বা ফেক Secret Key দেয়
        bot.send_message(chat_id, "❌ আপনার দেওয়া Secret Key টি সঠিক নয় বা ভুল ফরম্যাটে আছে। অনুগ্রহ করে আবার চেক করে সঠিক 'Secret Key' পাঠান।")
        print(f"Key Error: {e}")
        return

    user_steps[chat_id] = None
    bot.send_message(chat_id, "🔙 মেইন মেনুতে ফিরে আসা হয়েছে।", reply_markup=get_main_menu())

@bot.message_handler(func=lambda message: message.text == "💰 ব্যালেন্স")
def handle_balance(message):
    chat_id = message.chat.id
    balance = user_balances.get(chat_id, 0.00)
    bot.reply_to(message, f"💰 আপনার বর্তমান ব্যালেন্স: {balance:.2f} টাকা")

@bot.message_handler(func=lambda message: message.text == "💳 টাকা উত্তোলন")
def handle_withdrawal(message):
    chat_id = message.chat.id
    balance = user_balances.get(chat_id, 0.00)
    
    if balance <= 0.00:
        bot.reply_to(message, "❌ আপনার ব্যালেন্স খালি (৳০.০০), উত্তোলনের জন্য কোনো টাকা নেই।")
    else:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("বিকাশ (bKash)"), KeyboardButton("নগদ (Nagad)"))
        markup.add(KeyboardButton("রকেট (Rocket)"), KeyboardButton("🔙 মেইন মেনু"))
        user_steps[chat_id] = 'SELECT_METHOD'
        bot.send_message(chat_id, f"💵 আপনার ব্যালেন্স আছে: ৳{balance:.2f}\n👇 কোন মাধ্যমে পেমেন্ট নিতে চান সিলেক্ট করুন:", reply_markup=markup)

@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'SELECT_METHOD')
def process_method(message):
    chat_id = message.chat.id
    method = message.text
    
    if method in ["বিকাশ (bKash)", "নগদ (Nagad)", "রকেট (Rocket)"]:
        withdraw_data[chat_id] = {'method': method}
        user_steps[chat_id] = 'WAITING_NUMBER'
        bot.send_message(chat_id, f"📱 আপনার {method} নম্বরটি লিখে পাঠান:")
    elif method == "🔙 মেইন মেনু":
        user_steps[chat_id] = None
        bot.send_message(chat_id, "মেইন মেনু", reply_markup=get_main_menu())

@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'WAITING_NUMBER')
def process_number(message):
    chat_id = message.chat.id
    number = message.text.strip()
    
    method = withdraw_data[chat_id]['method']
    balance = user_balances.get(chat_id, 0.00)
    user_balances[chat_id] = 0.00
    
    payment_request = (
        f"💳 **নতুন পেমেন্ট রিকোয়েস্ট এসেছে!**\n\n"
        f"👤 ইউজার আইডি: `{chat_id}`\n"
        f"🛠️ পেমেন্ট মাধ্যম: **{method}**\n"
        f"📱 নম্বর: `{number}`\n"
        f"💰 টাকার পরিমাণ: **৳{balance:.2f}**\n\n"
        f"📌 এই নম্বরে টাকা পাঠিয়ে ইউজারকে ইনফর্ম করুন।"
    )
    try:
        bot.send_message(ADMIN_CHAT_ID, payment_request, parse_mode="Markdown")
    except Exception:
        pass
        
    bot.send_message(chat_id, f"✅ আপনার ৳{balance:.2f} উত্তোলনের রিকোয়েস্ট সফলভাবে অ্যাডমিনের কাছে পাঠানো হয়েছে। খুব দ্রুত আপনার `{number}` নম্বরে ({method}) পেমেন্ট করে দেওয়া হবে।", reply_markup=get_main_menu())
    user_steps[chat_id] = None

@bot.message_handler(func=lambda message: message.text in ["🔙 মেইন মেনু", "🔙 মেইন মেনুতে ফিরে গেলাম।"])
def back_to_main(message):
    user_steps[message.chat.id] = None
    bot.send_message(message.chat.id, "আপনি মেইন মেনুতে আছেন।", reply_markup=get_main_menu())

@bot.message_handler(func=lambda message: message.text == "🏆 লিডারবোর্ড")
def handle_leaderboard(message):
    bot.reply_to(message, "📊 আজকের টপ ১০ লিডারবোর্ড খুব শীঘ্রই আপডেট করা হবে।")

@bot.message_handler(func=lambda message: message.text == "📞 সাপোর্ট")
def handle_support(message):
    support_text = (
        f"📞 **আমাদের সাপোর্ট সার্ভিস:**\n\n"
        f"💬 যেকোনো সমস্যা বা পেমেন্ট সংক্রান্ত সাহায্যের জন্য অ্যাডমিনের সাথে সরাসরি যোগাযোগ করুন:\n"
        f"👤 **পার্সোনাল আইডি:** @jubayer1622\n\n"
        f"📢 **আমাদের অফিসিয়াল চ্যানেল (নতুন আপডেটের জন্য জয়েন থাকুন):**\n"
        f"🔗 https://t.me/smartearningdigitalplatform"
    )
    bot.send_message(message.chat.id, support_text, disable_web_page_preview=True)

@bot.message_handler(func=lambda message: message.text == "👥 Invite & Earn")
def handle_invite(message):
    chat_id = message.chat.id
    bot_username = "inst_sell_1622_bot"  
    refer_link = f"https://t.me/{bot_username}?start={chat_id}"
    
    bot.reply_to(message, f"👥 **Invite & Earn System**\n\n"
                          f"🔗 আপনার রেফারাল লিংক:\n{refer_link}\n\n"
                          f"🎁 আপনার লিংক ব্যবহার করে কেউ বটের কাজ শুরু করলেই আপনি সাথে সাথে আপনার ব্যালেন্সে পাবেন **৳{REFER_BONUS:.2f}** বোনাস!")

bot.polling(none_stop=True)