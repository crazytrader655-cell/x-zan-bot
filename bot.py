import os
import threading
import urllib.parse
from flask import Flask
import telebot
from telebot import types
import yt_dlp
import google.generativeai as genai
from PIL import Image

# 1. Dummy Web Server for Render Free Tier
app = Flask(__name__)

@app.route('/')
def home():
    return "X-ZAN Bot is running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# 2. Config & Initialization
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TIKTOK_URL = "https://www.tiktok.com/@sizan_3t1?is_from_webapp=1&sender_device=pc"
SUPPORT_USERNAME = "@Traders_with_Sizan"

bot = telebot.TeleBot(BOT_TOKEN)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Temporary User States & Data Storage
user_states = {}
user_video_links = {}

# 3. Keyboards
def get_join_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_join = types.InlineKeyboardButton("🎵 Join TikTok Account", url=TIKTOK_URL)
    btn_continue = types.InlineKeyboardButton("▶️ Continue to Bot", callback_data="goto_main")
    markup.add(btn_join, btn_continue)
    return markup

def get_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("🎬 Video Downloader", callback_data="menu_video")
    btn2 = types.InlineKeyboardButton("🎨 Generate Image", callback_data="menu_image")
    btn3 = types.InlineKeyboardButton("🔍 Master Prompt Gen", callback_data="menu_prompt")
    btn4 = types.InlineKeyboardButton("🤖 Talk with AI", callback_data="menu_aichat")
    btn5 = types.InlineKeyboardButton("💬 Support", url=f"https://t.me/{SUPPORT_USERNAME.replace('@', '')}")
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5)
    return markup

def get_video_category_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_yt = types.InlineKeyboardButton("▶️ YouTube Video", callback_data="vcat_youtube")
    btn_tt = types.InlineKeyboardButton("🎵 TikTok Video", callback_data="vcat_tiktok")
    btn_fb = types.InlineKeyboardButton("📘 Facebook Video", callback_data="vcat_facebook")
    btn_back = types.InlineKeyboardButton("🔙 Main Menu", callback_data="goto_main")
    markup.add(btn_yt, btn_tt)
    markup.add(btn_fb, btn_back)
    return markup

def get_quality_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_hd = types.InlineKeyboardButton("🎬 HD Video (Best Quality)", callback_data="dl_format_hd")
    btn_sd = types.InlineKeyboardButton("📱 SD Video (Fast Download)", callback_data="dl_format_sd")
    btn_audio = types.InlineKeyboardButton("🎵 Audio Only (MP3)", callback_data="dl_format_audio")
    btn_back = types.InlineKeyboardButton("🔙 Main Menu", callback_data="goto_main")
    markup.add(btn_hd, btn_sd, btn_audio, btn_back)
    return markup

def get_back_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Main Menu", callback_data="goto_main"))
    return markup

# 4. Command Handlers
@bot.message_handler(commands=['start', 'menu'])
def start_cmd(message):
    bot.send_message(
        message.chat.id,
        "🔥 **X-ZAN BOT**-এ আপনাকে স্বাগতম!\n\nবটটি ব্যবহার করতে প্রথমে আমাদের টিকটক অ্যাকাউন্টটিতে জয়েন করুন, তারপর **Continue** বাটনে চাপ দিন।",
        parse_mode="Markdown",
        reply_markup=get_join_keyboard()
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    
    if call.data == "goto_main":
        user_states[chat_id] = None
        bot.send_message(
            chat_id,
            "🎉 **X-ZAN Main Menu**\nনিচের অপশন থেকে আপনার প্রয়োজনীয় সার্ভিস বেছে নিন:",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
    elif call.data == "menu_video":
        bot.send_message(
            chat_id,
            "📂 **ভিডিও ডাউনলোড ক্যাটাগরি বেছে নিন:**",
            parse_mode="Markdown",
            reply_markup=get_video_category_menu()
        )
    elif call.data in ["vcat_youtube", "vcat_tiktok", "vcat_facebook"]:
        platform = call.data.split("_")[1].capitalize()
        user_states[chat_id] = "awaiting_video_link"
        bot.send_message(
            chat_id,
            f"📥 আপনার **{platform}** ভিডিওর লিংকটি এখানে পেস্ট করে দিন:",
            parse_mode="Markdown",
            reply_markup=get_back_menu()
        )
    elif call.data == "menu_image":
        user_states[chat_id] = "awaiting_image_prompt"
        bot.send_message(
            chat_id,
            "🎨 আপনি যে ছবিটি জেনারেট করতে চান তার টেক্সট প্রম্পটটি লিখে দিন (English-এ লিখলে রেজাল্ট ভালো আসবে):",
            reply_markup=get_back_menu()
        )
    elif call.data == "menu_prompt":
        user_states[chat_id] = "awaiting_prompt_photo"
        bot.send_message(
            chat_id,
            "🖼️ আপনি যে ধরণের ছবি বানাতে চান তার একটি ফটো এখানে আপলোড করুন। এআই ছবিটি এনালাইজ করে সেম মাস্টার প্রম্পট তৈরি করে দেবে:",
            reply_markup=get_back_menu()
        )
    elif call.data == "menu_aichat":
        user_states[chat_id] = "ai_chat"
        bot.send_message(
            chat_id,
            "🤖 **X-ZAN AI Chat Active!**\nবাংলা বা ইংরেজি যেকোনো ভাষায় আমাকে যেকোনো প্রশ্ন করুন:",
            reply_markup=get_back_menu()
        )
    elif call.data in ["dl_format_hd", "dl_format_sd", "dl_format_audio"]:
        link = user_video_links.get(chat_id)
        if not link:
            bot.send_message(chat_id, "❌ কোনো লিংক পাওয়া যায়নি! আবার লিংক দিন।", reply_markup=get_main_menu())
            return
        
        fmt_choice = call.data
        msg = bot.send_message(chat_id, "⏳ ভিডিও প্রসেস ও ডাউনলোড করা হচ্ছে...")
        
        # Determine yt-dlp format options
        if fmt_choice == "dl_format_hd":
            format_str = 'best[filesize<48M]/bestvideo[filesize<40M]+bestaudio/best'
        elif fmt_choice == "dl_format_sd":
            format_str = 'worst[filesize<48M]/worstvideo+worstaudio/worst'
        else:
            format_str = 'bestaudio[filesize<48M]/best'

        ydl_opts = {
            'format': format_str,
            'outtmpl': f'downloads/{chat_id}_%(id)s.%(ext)s',
            'quiet': True,
            'nocheckcertificate': True,
            'geo_bypass': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        try:
            os.makedirs("downloads", exist_ok=True)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=True)
                filename = ydl.prepare_filename(info)

            with open(filename, 'rb') as media_file:
                if fmt_choice == "dl_format_audio":
                    bot.send_audio(chat_id, media_file, caption="✅ **X-ZAN Audio Download Complete!**")
                else:
                    bot.send_video(chat_id, media_file, caption="✅ **X-ZAN Video Download Complete!**")
                    
            bot.delete_message(chat_id, msg.message_id)
            if os.path.exists(filename):
                os.remove(filename)
            user_states[chat_id] = None
            bot.send_message(chat_id, "✨ আর কোনো সেবা নিতে চাইলে মেনু সিলেক্ট করুন:", reply_markup=get_main_menu())
        except Exception as e:
            bot.delete_message(chat_id, msg.message_id)
            bot.send_message(
                chat_id,
                "❌ **ডাউনলোড ব্যর্থ হয়েছে!**\nভিডিওটি অতি বড় (৫০MB-এর উপরে) হতে পারে অথবা প্রাইভেট লিংক। অন্য কোনো লিংক দিয়ে চেষ্টা করুন।",
                reply_markup=get_main_menu()
            )

# 5. Photo Handlers (Master Prompt Generator)
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    if user_states.get(chat_id) == "awaiting_prompt_photo":
        msg = bot.send_message(chat_id, "🔍 এআই দিয়ে ছবি এনালাইজ করা হচ্ছে, অনুগ্রহ করে অপেক্ষা করুন...")
        temp_filename = f"temp_{chat_id}.jpg"
        try:
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            with open(temp_filename, "wb") as new_file:
                new_file.write(downloaded_file)
                
            img = Image.open(temp_filename).convert('RGB')
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            system_prompt = (
                "Analyze this photo in extreme detail. Provide a comprehensive, highly photorealistic Midjourney/SDXL prompt "
                "to recreate this exact subject. Include detail on subject face structure, outfit, pose, lighting, background, "
                "and visual style. Provide ONLY the final prompt text."
            )
            
            response = model.generate_content([system_prompt, img])
            bot.delete_message(chat_id, msg.message_id)
            bot.send_message(
                chat_id,
                f"🎯 **Master Prompt Generated:**\n\n`{response.text}`",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )
        except Exception as e:
            bot.delete_message(chat_id, msg.message_id)
            bot.send_message(chat_id, "❌ ছবি এনালাইজ করতে সমস্যা হয়েছে। আবার চেষ্টা করুন।", reply_markup=get_main_menu())
        finally:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

# 6. Text Handlers (Link, Prompt, AI Chat)
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)
    text = message.text

    if state == "awaiting_video_link":
        if text.startswith("http://") or text.startswith("https://"):
            user_video_links[chat_id] = text
            bot.send_message(
                chat_id,
                "🎬 **ভিডিও কোয়ালিটি এবং ফরমেট বেছে নিন:**",
                parse_mode="Markdown",
                reply_markup=get_quality_menu()
            )
        else:
            bot.send_message(chat_id, "❌ দয়া করে সঠিক কোনো ভিডিও লিংক প্রদান করুন।")

    elif state == "awaiting_image_prompt":
        msg = bot.send_message(chat_id, "🎨 ছবি জেনারেট হচ্ছে...")
        encoded_prompt = urllib.parse.quote(text)
        img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
        try:
            bot.send_photo(chat_id, img_url, caption=f"✨ **Prompt:** {text}", reply_markup=get_main_menu())
            bot.delete_message(chat_id, msg.message_id)
            user_states[chat_id] = None
        except Exception as e:
            bot.delete_message(chat_id, msg.message_id)
            bot.send_message(chat_id, "❌ ছবি তৈরিতে সমস্যা হয়েছে। আবার চেষ্টা করুন।", reply_markup=get_main_menu())

    elif state == "ai_chat":
        msg = bot.send_message(chat_id, "🤖 চিন্তা করা হচ্ছে...")
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(text)
            bot.delete_message(chat_id, msg.message_id)
            bot.send_message(chat_id, f"🤖 **X-ZAN AI:**\n\n{response.text}", reply_markup=get_back_menu())
        except Exception as e:
            bot.delete_message(chat_id, msg.message_id)
            bot.send_message(chat_id, "❌ উত্তর তৈরিতে সমস্যা হয়েছে। আবার লিখুন।", reply_markup=get_back_menu())

    else:
        bot.send_message(chat_id, "মেনু অপশন সিলেক্ট করতে /start চাপুন।", reply_markup=get_join_keyboard())

# 7. Execution Start
if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    bot.infinity_polling()
