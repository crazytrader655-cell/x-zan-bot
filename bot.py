import os
import urllib.parse
import telebot
from telebot import types
import yt_dlp
import google.generativeai as genai
from PIL import Image

# Config Constraints
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TIKTOK_URL = "https://www.tiktok.com/@sizan_3t1?is_from_webapp=1&sender_device=pc"
SUPPORT_USERNAME = "@Traders_with_Sizan"

bot = telebot.TeleBot(BOT_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)

# User state handling
user_states = {}

# Keyboard Generators
def get_join_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎵 TikTok-এ জয়েন করুন", url=TIKTOK_URL))
    markup.add(types.InlineKeyboardButton("✅ I Have Joined", callback_data="check_joined"))
    return markup

def get_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("🎬 Video Downloader", callback_data="mode_video")
    btn2 = types.InlineKeyboardButton("🎨 Generate Image", callback_data="mode_image")
    btn3 = types.InlineKeyboardButton("🔍 Master Prompt Gen", callback_data="mode_prompt")
    btn4 = types.InlineKeyboardButton("💬 Support", url=f"https://t.me/{SUPPORT_USERNAME.replace('@', '')}")
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    return markup

# Handlers
@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(
        message.chat.id,
        "🔥 **X-ZAN BOT**-এ আপনাকে স্বাগতম!\n\nবটটি ব্যবহার করতে প্রথমে আমাদের টিকটক অ্যাকাউন্টটি ফলো/জয়েন করুন।",
        parse_mode="Markdown",
        reply_markup=get_join_keyboard()
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    
    if call.data == "check_joined":
        bot.delete_message(chat_id, call.message.message_id)
        bot.send_message(
            chat_id,
            "🎉 **ধন্যবাদ!** আপনার এক্সেস আনলক করা হয়েছে। নিচের মেনু থেকে অপশন বেছে নিন:",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
    elif call.data == "mode_video":
        user_states[chat_id] = "video"
        bot.send_message(chat_id, "📥 যেকোনো TikTok, YouTube বা Facebook ভিডিওর লিংক পাঠিয়ে দিন:")
    elif call.data == "mode_image":
        user_states[chat_id] = "image"
        bot.send_message(chat_id, "🎨 আপনি যে ছবি জেনারেট করতে চান তার টেক্সট প্রম্পট লিখে দিন:")
    elif call.data == "mode_prompt":
        user_states[chat_id] = "prompt"
        bot.send_message(chat_id, "🖼️ আপনার ছবিটি এখানে আপলোড করুন। এআই এনালাইজ করে সেম মাস্টার প্রম্পট তৈরি করে দেবে:")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    if user_states.get(chat_id) == "prompt":
        msg = bot.send_message(chat_id, "🔍 এআই দিয়ে ছবি এনালাইজ করা হচ্ছে, অনুগ্রহ করে অপেক্ষা করুন...")
        try:
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            with open("temp.jpg", "wb") as new_file:
                new_file.write(downloaded_file)
                
            img = Image.open("temp.jpg")
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            system_prompt = (
                "Analyze this photo in extreme detail. Provide a comprehensive, professional SDXL/Midjourney text-to-image prompt "
                "to recreate a photorealistic version of this exact subject. Include detail on subject structure, outfit, pose, background, "
                "camera framing, color grading, lighting, and textures. Keep output as pure prompt text."
            )
            
            response = model.generate_content([system_prompt, img])
            bot.delete_message(chat_id, msg.message_id)
            bot.send_message(chat_id, f"🎯 **Master Prompt:**\n\n`{response.text}`", parse_mode="Markdown", reply_markup=get_main_menu())
            if os.path.exists("temp.jpg"):
                os.remove("temp.jpg")
        except Exception as e:
            bot.send_message(chat_id, "❌ সমস্যা হয়েছে! আবার চেষ্টা করুন।", reply_markup=get_main_menu())

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)
    text = message.text

    if state == "video":
        msg = bot.send_message(chat_id, "⏳ ভিডিও প্রসেস ও ডাউনলোড করা হচ্ছে...")
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'downloaded_video.%(ext)s',
            'quiet': True
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=True)
                filename = ydl.prepare_filename(info)
                
            with open(filename, 'rb') as video:
                bot.send_video(chat_id, video, caption="✅ **X-ZAN** দিয়ে ডিরেক্ট হাই-কোয়ালিটিতে ডাউনলোড করা হয়েছে!")
            bot.delete_message(chat_id, msg.message_id)
            if os.path.exists(filename):
                os.remove(filename)
        except Exception as e:
            bot.send_message(chat_id, "❌ ডাউনলোড ব্যর্থ হয়েছে। সঠিক লিংক দিয়েছেন কিনা চেক করুন।")
            
    elif state == "image":
        msg = bot.send_message(chat_id, "🎨 ছবি জেনারেট হচ্ছে...")
        encoded_prompt = urllib.parse.quote(text)
        img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
        try:
            bot.send_photo(chat_id, img_url, caption=f"✨ **Prompt:** {text}")
            bot.delete_message(chat_id, msg.message_id)
        except Exception as e:
            bot.send_message(chat_id, "❌ ছবি তৈরিতে সমস্যা হয়েছে। আবার চেষ্টা করুন।")
    else:
        bot.send_message(chat_id, "মেনু অপশন সিলেক্ট করতে /start চাপুন।", reply_markup=get_join_keyboard())

if __name__ == "__main__":
    bot.infinity_polling()
