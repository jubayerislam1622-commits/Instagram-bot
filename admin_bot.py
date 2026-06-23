import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import random
import string
import pyotp
import json
from datetime import datetime

# বটের কনফিগারেশন
API_TOKEN = '8848253078:AAHxbEqZFPypogFA6IzO2oeXYxoXMYQvMNk'
ADMIN_CHAT_ID = 7993941422  

bot = telebot.TeleBot(API_TOKEN)

# ডিফল্ট সেটিংস (মেমোরিতে)
settings = {
    'password': 'jubayer@22',
    'work_reward': 3.40,
    'refer_bonus': 2.00,
    'tasks': {
        'instagram_2fa': {
            'name': '⚡ ইনস্টাগ্রাম 2FA',
            'reward': 3.40,
            'active': True
        }
    }
}

# ডাটাবেজ (মেমোরি)
user_balances = {}
user_steps = {}
user_data = {}
withdraw_data = {}
referred_users = {}
admin_sessions = {}  # Admin লগইন সেশন

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

def get_admin_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("⚙️ সেটিংস"), KeyboardButton("💼 কাজ ম্যানেজমেন্ট"))
    markup.add(KeyboardButton("🔐 পাসওয়ার্ড চেঞ্জ"), KeyboardButton("💰 রিওয়ার্ড চেঞ্জ"))
    markup.add(KeyboardButton("👥 রেফারেল বোনাস"), KeyboardButton("📊 স্ট্যাটিস্টিক্স"))
    markup.add(KeyboardButton("🚪 লগআউট"))
    return markup

# ========== ADMIN সিস্টেম শুরু ==========

@bot.message_handler(commands=['admin'])
def admin_login(message):
    chat_id = message.chat.id
    
    if chat_id == ADMIN_CHAT_ID:
        user_steps[chat_id] = 'ADMIN_LOGIN'
        bot.send_message(chat_id, "🔐 Admin পাসওয়ার্ড দিন:")
    else:
        bot.send_message(chat_id, "❌ আপনি Admin নন। এই কমান্ড ব্যবহার করতে পারবেন না।")

@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'ADMIN_LOGIN')
def verify_admin_password(message):
    chat_id = message.chat.id
    password = message.text.strip()
    
    if password == "admin123":  # এডমিন পাসওয়ার্ড
        admin_sessions[chat_id] = True
        user_steps[chat_id] = None
        bot.send_message(chat_id, "✅ Admin লগইন সফল!", reply_markup=get_admin_menu())
    else:
        bot.send_message(chat_id, "❌ ভুল পাসওয়ার্ড। আবার চেষ্টা করুন।")

@bot.message_handler(func=lambda message: message.text == "🚪 লগআউট")
def admin_logout(message):
    chat_id = message.chat.id
    if chat_id in admin_sessions:
        del admin_sessions[chat_id]
    user_steps[chat_id] = None
    bot.send_message(chat_id, "👋 আপনি লগআউট করেছেন।")

# ========== পাসওয়ার্ড চেঞ্জ ==========

@bot.message_handler(func=lambda message: message.text == "🔐 পাসওয়ার্ড চেঞ্জ" and admin_sessions.get(message.chat.id))
def admin_change_password(message):
    chat_id = message.chat.id
    user_steps[chat_id] = 'CHANGE_PASSWORD'
    current_pass = settings['password']
    bot.send_message(chat_id, f"🔐 **বর্তমান পাসওয়ার্ড:** `{current_pass}`\n\n✏️ নতুন পাসওয়ার্ড লিখুন:", parse_mode="Markdown")

@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'CHANGE_PASSWORD')
def process_new_password(message):
    chat_id = message.chat.id
    new_password = message.text.strip()
    
    if len(new_password) < 5:
        bot.send_message(chat_id, "❌ পাসওয়ার্ড কমপক্ষে ৫ ক্যারেক্টার হতে হবে।")
        return
    
    old_password = settings['password']
    settings['password'] = new_password
    user_steps[chat_id] = None
    
    bot.send_message(chat_id, f"✅ পাসওয়ার্ড সফলভাবে পরিবর্তিত হয়েছে!\n\n"
                              f"🔴 **পুরানো:** `{old_password}`\n"
                              f"🟢 **নতুন:** `{new_password}`", parse_mode="Markdown", reply_markup=get_admin_menu())

# ========== রিওয়ার্ড চেঞ্জ ==========

@bot.message_handler(func=lambda message: message.text == "💰 রিওয়ার্ড চেঞ্জ" and admin_sessions.get(message.chat.id))
def admin_change_reward(message):
    chat_id = message.chat.id
    current_reward = settings['work_reward']
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(f"কাজের রেট (বর্তমান: ৳{current_reward})", callback_data="reward_work"))
    markup.add(InlineKeyboardButton(f"রেফারেল বোনাস (বর্তমান: ৳{settings['refer_bonus']})", callback_data="reward_refer"))
    
    bot.send_message(chat_id, "💰 কোনটির রেট চেঞ্জ করতে চান?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "reward_work")
def change_work_reward(call):
    chat_id = call.message.chat.id
    user_steps[chat_id] = 'CHANGE_WORK_REWARD'
    bot.send_message(chat_id, f"💰 বর্তমান কাজের রেট: ৳{settings['work_reward']}\n\n✏️ নতুন রেট লিখুন (শুধু সংখ্যা):")

@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'CHANGE_WORK_REWARD')
def process_work_reward(message):
    chat_id = message.chat.id
    try:
        new_reward = float(message.text.strip())
        if new_reward <= 0:
            bot.send_message(chat_id, "❌ রেট ০ এর চেয়ে বেশি হতে হবে।")
            return
        
        old_reward = settings['work_reward']
        settings['work_reward'] = new_reward
        settings['tasks']['instagram_2fa']['reward'] = new_reward
        user_steps[chat_id] = None
        
        bot.send_message(chat_id, f"✅ কাজের রেট আপডেট হয়েছে!\n\n"
                                  f"🔴 পুরানো: ৳{old_reward}\n"
                                  f"🟢 নতুন: ৳{new_reward}", reply_markup=get_admin_menu())
    except:
        bot.send_message(chat_id, "❌ সংখ্যা লিখুন (যেমন: 5.50)")

@bot.callback_query_handler(func=lambda call: call.data == "reward_refer")
def change_refer_reward(call):
    chat_id = call.message.chat.id
    user_steps[chat_id] = 'CHANGE_REFER_REWARD'
    bot.send_message(chat_id, f"👥 বর্তমান রেফারেল বোনাস: ৳{settings['refer_bonus']}\n\n✏️ নতুন বোনাস লিখুন:")

@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'CHANGE_REFER_REWARD')
def process_refer_reward(message):
    chat_id = message.chat.id
    try:
        new_bonus = float(message.text.strip())
        if new_bonus <= 0:
            bot.send_message(chat_id, "❌ বোনাস ০ এর চেয়ে বেশি হতে হবে।")
            return
        
        old_bonus = settings['refer_bonus']
        settings['refer_bonus'] = new_bonus
        user_steps[chat_id] = None
        
        bot.send_message(chat_id, f"✅ রেফারেল বোনাস আপডেট হয়েছে!\n\n"
                                  f"🔴 পুরানো: ৳{old_bonus}\n"
                                  f"🟢 নতুন: ৳{new_bonus}", reply_markup=get_admin_menu())
    except:
        bot.send_message(chat_id, "❌ সংখ্যা লিখুন (যেমন: 2.50)")

# ========== কাজ ম্যানেজমেন্ট ==========

@bot.message_handler(func=lambda message: message.text == "💼 কাজ ম্যানেজমেন্ট" and admin_sessions.get(message.chat.id))
def admin_task_management(message):
    chat_id = message.chat.id
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("➕ নতুন কাজ যোগ করুন", callback_data="add_task"))
    markup.add(InlineKeyboardButton("✏️ কাজ এডিট করুন", callback_data="edit_task"))
    markup.add(InlineKeyboardButton("🗑️ কাজ ডিলিট করুন", callback_data="delete_task"))
    markup.add(InlineKeyboardButton("📋 সব কাজ দেখুন", callback_data="list_tasks"))
    
    bot.send_message(chat_id, "💼 **কাজ ম্যানেজমেন্ট মেনু:**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "list_tasks")
def admin_list_tasks(call):
    chat_id = call.message.chat.id
    task_list = "📋 **সকল কাজের তালিকা:**\n\n"
    
    for key, task in settings['tasks'].items():
        status = "✅ চালু" if task['active'] else "❌ বন্ধ"
        task_list += f"• {task['name']} - ৳{task['reward']} [{status}]\n"
    
    bot.send_message(chat_id, task_list, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "add_task")
def admin_add_task(call):
    chat_id = call.message.chat.id
    user_steps[chat_id] = 'ADD_TASK_NAME'
    bot.send_message(chat_id, "✏️ নতুন কাজের নাম লিখুন (যেমন: ⭐ ফেসবুক লাইক):")

@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'ADD_TASK_NAME')
def process_add_task_name(message):
    chat_id = message.chat.id
    task_name = message.text.strip()
    user_data[chat_id] = {'task_name': task_name}
    user_steps[chat_id] = 'ADD_TASK_REWARD'
    bot.send_message(chat_id, f"💰 '{task_name}' এর রেট কত টাকা? (শুধু সংখ্যা):")

@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'ADD_TASK_REWARD')
def process_add_task_reward(message):
    chat_id = message.chat.id
    try:
        reward = float(message.text.strip())
        task_name = user_data[chat_id]['task_name']
        
        # নতুন কাজ যোগ করুন
        task_id = f"task_{len(settings['tasks']) + 1}"
        settings['tasks'][task_id] = {
            'name': task_name,
            'reward': reward,
            'active': True
        }
        
        user_steps[chat_id] = None
        user_data[chat_id] = {}
        
        bot.send_message(chat_id, f"✅ নতুন কাজ যোগ হয়েছে!\n\n📝 {task_name}\n💰 ৳{reward}", 
                        reply_markup=get_admin_menu())
    except:
        bot.send_message(chat_id, "❌ সঠিক সংখ্যা লিখুন।")

# ========== ইউজার সাইড ==========

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
                if referrer_id != chat_id and referrer_id != ADMIN_CHAT_ID:
                    if chat_id not in referred_users:
                        referred_users[chat_id] = referrer_id
                        
                        if referrer_id not in user_balances:
                            user_balances[referrer_id] = 0.00
                        user_balances[referrer_id] += settings['refer_bonus']
                        
                        try:
                            bot.send_message(referrer_id, f"🎉 আপনার রেফার লিংকে একজন নতুন সদস্য জয়েন করেছে! আপনার অ্যাকাউন্টে ৳{settings['refer_bonus']:.2f} যোগ হয়েছে।")
                        except Exception:
                            pass
            except ValueError:
                pass

    bot.send_message(chat_id, "👋 স্বাগতম! অনুগ্রহ করে নিচের মেনু থেকে অপশন নির্বাচন করুন:", reply_markup=get_main_menu())

@bot.message_handler(func=lambda message: message.text == "💼 কাজ")
def handle_kaaj(message):
    chat_id = message.chat.id
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    
    # সব সক্রিয় কাজ যোগ করুন
    for key, task in settings['tasks'].items():
        if task['active']:
            markup.add(KeyboardButton(f"{task['name']} (৳{task['reward']:.2f})"))
    
    markup.add(KeyboardButton("🔙 মেইন মেনু"))
    bot.reply_to(message, "⚡ যেকোনো একটি কাজ সিলেক্ট করুন ⤵️", reply_markup=markup)

@bot.message_handler(func=lambda message: any(task['name'] in message.text for task in settings['tasks'].values()))
def handle_task_selection(message):
    chat_id = message.chat.id
    message_text = message.text
    
    # কোন কাজ নির্বাচিত তা খুঁজে বের করুন
    selected_task = None
    for key, task in settings['tasks'].items():
        if task['name'] in message_text:
            selected_task = key
            break
    
    if selected_task and selected_task == 'instagram_2fa':
        handle_instagram(message)

def handle_instagram(message):
    chat_id = message.chat.id
    new_username = generate_unique_username()
    user_data[chat_id] = {'username': new_username}
    
    response_text = (
        f"👤 Username: `{new_username}`\n"
        f"🔒 Password: `{settings['password']}`\n\n"
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
    bot.send_message(chat_id, "🔑 Instagram থেকে পাওয়া **2FA Secret Key** পুরোটা পেস্ট করে পাঠান (কোনো স্পেস ছাড়া):", parse_mode="Markdown")

@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'WAITING_SECRET_KEY')
def process_secret_key(message):
    chat_id = message.chat.id
    secret_key = message.text.strip().replace(" ", "")
    username = user_data.get(chat_id, {}).get('username', 'Unknown')
    
    try:
        totp = pyotp.TOTP(secret_key)
        live_code = totp.now()
        
        admin_report = (
            f"📥 **নতুন কাজ জমা এসেছে!**\n\n"
            f"👤 কর্মী আইডি: `{chat_id}`\n"
            f"🏷️ Username: `{username}`\n"
            f"🔑 Password: `{settings['password']}`\n"
            f"🔐 2FA Secret: `{secret_key}`\n"
            f"🔢 **Live 2FA Code:** `{live_code}`\n\n"
            f"⚙️ **টাকা অ্যাড করতে নিচের কমান্ড ব্যবহার করুন:**\n"
            f"/add_money_{chat_id}_{settings['work_reward']}"
        )
        try:
            bot.send_message(ADMIN_CHAT_ID, admin_report, parse_mode="Markdown")
        except Exception:
            pass

        user_response = (
            f"✅ **আপনার কাজটি সফলভাবে জমা নেওয়া হয়েছে!**\n\n"
            f"🔢 আপনার বর্তমান ২এফএ কোড: `{live_code}`\n\n"
            f"⚠️ কোডটি প্রতি ৩০ সেকেন্ড পর পর পরিবর্তন হয়। অ্যাডমিন অ্যাকাউন্টটি সফলভাবে সেটআপ না করা পর্যন্ত অপেক্ষা করুন।"
        )
        bot.send_message(chat_id, user_response, parse_mode="Markdown")
        
    except Exception as e:
        bot.send_message(chat_id, "❌ আপনার দেওয়া Secret Key টি সঠিক নয়। অনুগ্রহ করে আবার চেষ্টা করুন।")
        print(f"Key Error: {e}")
        return

    user_steps[chat_id] = None
    bot.send_message(chat_id, "🔙 মেইন মেনুতে ফিরে আসা হয়েছে।", reply_markup=get_main_menu())

@bot.message_handler(regexp=r'/add_money_\d+_[\d.]+')
def admin_add_money(message):
    if message.chat.id != ADMIN_CHAT_ID:
        return
        
    try:
        parts = message.text.split('_')
        target_user_id = int(parts[2])
        amount = float(parts[3])
        
        if target_user_id not in user_balances:
            user_balances[target_user_id] = 0.00
            
        user_balances[target_user_id] += amount
        bot.reply_to(message, f"✅ ইউজার `{target_user_id}` এর অ্যাকাউন্টে ৳{amount:.2f} সফলভাবে যোগ করা হয়েছে।", parse_mode="Markdown")
        bot.send_message(target_user_id, f"🎉 অভিনন্দন! আপনার জমা দেওয়া কাজটি অ্যাডমিন চেক করে অনুমোদন করেছেন। আপনার ব্যালেন্সে ৳{amount:.2f} যোগ হয়েছে!")
    except Exception as e:
        bot.reply_to(message, f"❌ টাকা অ্যাড করা যায়নি। এরর: {e}")

@bot.message_handler(func=lambda message: message.text == "💰 ব্যালেন্স")
def handle_balance(message):
    chat_id = message.chat.id
    balance = user_balances.get(chat_id, 0.00)
    bot.reply_to(message, f"💰 আপনার বর্তমান ব্যালেন্স: ৳{balance:.2f}")

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
        bot.send_message(chat_id, f"💵 আপনার ব্যালেন্স: ৳{balance:.2f}\n👇 কোন মাধ্যমে পেমেন্ট নিতে চান:", reply_markup=markup)

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
        f"💳 **নতুন পেমেন্ট রিকোয়েস্ট এসেছে!**\n\n"
        f"👤 ইউজার আইডি: `{chat_id}`\n"
        f"🛠️ পেমেন্ট মাধ্যম: **{method}**\n"
        f"📱 নম্বর: `{number}`\n"
        f"💰 টাকার পরিমাণ: **৳{balance:.2f}**\n\n"
        f"📌 এই নম্বরে টাকা পাঠিয়ে ইউজারকে ইনফর্ম করুন।"
    )
    try:
        bot.send_message(ADMIN_CHAT_ID, payment_request, parse_mode="Markdown")
    except Exception:
        pass
        
    bot.send_message(chat_id, f"✅ আপনার ৳{balance:.2f} উত্তোলনের রিকোয়েস্ট সফলভাবে অ্যাডমিনের কাছে পাঠানো হয়েছে।\n\n⏳ শীঘ্রই আপনি পেমেন্ট পাবেন।")
    user_steps[chat_id] = None

@bot.message_handler(func=lambda message: message.text in ["🔙 মেইন মেনু", "🔙 মেইন মেনুতে ফিরে গেলাম।"])
def back_to_main(message):
    user_steps[message.chat.id] = None
    bot.send_message(message.chat.id, "আপনি মেইন মেনুতে আছেন।", reply_markup=get_main_menu())

@bot.message_handler(func=lambda message: message.text == "🏆 লিডারবোর্ড")
def handle_leaderboard(message):
    leaderboard_text = "🏆 **টপ ১০ লিডারবোর্ড**\n\n"
    sorted_users = sorted(user_balances.items(), key=lambda x: x[1], reverse=True)[:10]
    
    for i, (user_id, balance) in enumerate(sorted_users, 1):
        if balance > 0:
            leaderboard_text += f"{i}. `{user_id}` - ৳{balance:.2f}\n"
    
    if not sorted_users or all(b <= 0 for _, b in sorted_users):
        leaderboard_text = "📊 এখনো কোনো ডাটা নেই।"
    
    bot.send_message(message.chat.id, leaderboard_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "📞 সাপোর্ট")
def handle_support(message):
    support_text = (
        f"📞 **আমাদের সাপোর্ট সার্ভিস:**\n\n"
        f"💬 যেকোনো সমস্যা বা পেমেন্ট সংক্রান্ত সাহায্যের জন্য অ্যাডমিনের সাথে যোগাযোগ করুন।\n\n"
        f"👤 **পার্সোনাল আইডি:** @jubayer1622\n\n"
        f"📢 **আমাদের অফিসিয়াল চ্যানেল (নতুন আপডেটের জন্য জয়েন থাকুন):**\n"
        f"🔗 https://t.me/smartearningdigitalplatform"
    )
    bot.send_message(message.chat.id, support_text, disable_web_page_preview=True)

@bot.message_handler(func=lambda message: message.text == "👥 Invite & Earn")
def handle_invite(message):
    chat_id = message.chat.id
    bot_username = "inst_sell_1622_bot"  
    refer_link = f"https://t.me/{bot_username}?start={chat_id}"
    
    bot.send_message(chat_id, f"👥 **Invite & Earn System**\n\n"
                              f"🔗 আপনার রেফারাল লিংক:\n`{refer_link}`\n\n"
                              f"🎁 আপনার লিংক ব্যবহার করে কেউ বটে জয়েন করলেই আপনি ৳{settings['refer_bonus']:.2f} বোনাস পাবেন!",
                    parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "⚙️ সেটিংস" and admin_sessions.get(message.chat.id))
def admin_settings(message):
    chat_id = message.chat.id
    settings_info = (
        f"⚙️ **বর্তমান সেটিংস:**\n\n"
        f"🔐 **পাসওয়ার্ড:** `{settings['password']}`\n"
        f"💰 **কাজের রেট:** ৳{settings['work_reward']:.2f}\n"
        f"👥 **রেফারেল বোনাস:** ৳{settings['refer_bonus']:.2f}\n"
        f"📝 **মোট কাজ:** {len(settings['tasks'])}\n"
        f"👥 **মোট ইউজার:** {len(user_balances)}\n"
        f"💾 **টোটাল ব্যালেন্স:** ৳{sum(user_balances.values()):.2f}"
    )
    bot.send_message(chat_id, settings_info, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "📊 স্ট্যাটিস্টিক্স" and admin_sessions.get(message.chat.id))
def admin_statistics(message):
    chat_id = message.chat.id
    
    total_users = len(user_balances)
    total_balance = sum(user_balances.values())
    total_referred = len(referred_users)
    
    stats = (
        f"📊 **সিস্টেম স্ট্যাটিস্টিক্স:**\n\n"
        f"👥 **মোট ইউজার:** {total_users}\n"
        f"💰 **মোট ব্যালেন্স:** ৳{total_balance:.2f}\n"
        f"🎁 **মোট রেফারেল:** {total_referred}\n"
        f"📝 **সক্রিয় কাজ:** {sum(1 for t in settings['tasks'].values() if t['active'])}"
    )
    bot.send_message(chat_id, stats, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "👥 রেফারেল বোনাস" and admin_sessions.get(message.chat.id))
def admin_refer_bonus(message):
    chat_id = message.chat.id
    user_steps[chat_id] = 'CHANGE_REFER_BONUS'
    bot.send_message(chat_id, f"👥 বর্তমান রেফারেল বোনাস: ৳{settings['refer_bonus']}\n\n✏️ নতুন বোনাস লিখুন:")

@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == 'CHANGE_REFER_BONUS')
def process_refer_bonus(message):
    chat_id = message.chat.id
    try:
        new_bonus = float(message.text.strip())
        if new_bonus <= 0:
            bot.send_message(chat_id, "❌ বোনাস ০ এর চেয়ে বেশি হতে হবে।")
            return
        
        old_bonus = settings['refer_bonus']
        settings['refer_bonus'] = new_bonus
        user_steps[chat_id] = None
        
        bot.send_message(chat_id, f"✅ রেফারেল বোনাস আপডেট হয়েছে!\n\n"
                                  f"🔴 পুরানো: ৳{old_bonus}\n"
                                  f"🟢 নতুন: ৳{new_bonus}", reply_markup=get_admin_menu())
    except:
        bot.send_message(chat_id, "❌ সংখ্যা লিখুন।")

bot.polling(none_stop=True)
