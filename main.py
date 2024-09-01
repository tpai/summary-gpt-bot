import yt_dlp
from pydub import AudioSegment
import subprocess
import json
import os
import re
import trafilatura
import uuid
import requests
from duckduckgo_search import AsyncDDGS
from PyPDF2 import PdfReader
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, filters, ApplicationBuilder


# 從環境變數中取得 OpenAI API Key
openai_api_key = os.environ.get("OPENAI_API_KEY", "YOUR_API_KEY")
telegram_token = os.environ.get("TELEGRAM_TOKEN", "xxx")
model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
lang = os.environ.get("TS_LANG", "繁體中文")
ddg_region = os.environ.get("DDG_REGION", "wt-wt")
chunk_size = int(os.environ.get("CHUNK_SIZE", 2100))
allowed_users = os.environ.get("ALLOWED_USERS", "")
use_audio_fallback = int(os.environ.get("USE_AUDIO_FALLBACK", "0"))
# 添加 GROQ API Key
groq_api_key = os.environ.get("GROQ_API_KEY", "YOUR_GROQ_API_KEY")
base_url = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")

def split_user_input(text):
    paragraphs = text.split('\n')
    paragraphs = [paragraph.strip() for paragraph in paragraphs if paragraph.strip()]
    return paragraphs

def scrape_text_from_url(url):
    try:
        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(downloaded, include_formatting=True)
        if text is None:
            return []
        text_chunks = text.split("\n")
        article_content = [text for text in text_chunks if text]
        return article_content
    except Exception as e:
        print(f"Error: {e}")

async def search_results(keywords):
    print(keywords, ddg_region)
    results = await AsyncDDGS().text(keywords, region=ddg_region, safesearch='off', max_results=6)
    return results

def summarize(text_array):
    def create_chunks(paragraphs):
        chunks = []
        chunk = ''
        for paragraph in paragraphs:
            if len(chunk) + len(paragraph) < chunk_size:
                chunk += paragraph + ' '
            else:
                chunks.append(chunk.strip())
                chunk = paragraph + ' '
        if chunk:
            chunks.append(chunk.strip())
        return chunks

    try:
        text_chunks = create_chunks(text_array)
        text_chunks = [chunk for chunk in text_chunks if chunk]

        summaries = []
        system_messages = [
            {"role": "system", "content": "將以下原文總結為五個部分：1.總結 (Overall Summary)。2.觀點 (Viewpoints)。3.摘要 (Abstract)： 創建6到10個帶有適當表情符號的重點摘要。4.關鍵字 (Key Words)。 5.一個讓十二歲青少年可以看得動懂的段落。請確保每個部分只生成一次，且內容不重複。確保生成的文字都是{lang}為主"}
        ]

        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(call_gpt_api, f"總結 the following text:\n{chunk}", system_messages) for chunk in text_chunks]
            summaries = [future.result() for future in tqdm(futures, total=len(text_chunks), desc="Summarizing")]

        final_summary = {
            "overall_summary": "",
            "viewpoints": "",
            "abstract": "",
            "keywords": ""
        }
        for summary in summaries:
            if '總結 (Overall Summary)' in summary and not final_summary["overall_summary"]:
                final_summary["overall_summary"] = summary.split('觀點 (Viewpoints)')[0].strip()
            if '觀點 (Viewpoints)' in summary and not final_summary["viewpoints"]:
                content = summary.split('摘要 (Abstract)')[0].split('觀點 (Viewpoints)')[1].strip()
                final_summary["viewpoints"] = content
            if '摘要 (Abstract)' in summary and not final_summary["abstract"]:
                content = summary.split('關鍵字 (Key Words)')[0].split('摘要 (Abstract)')[1].strip()
                final_summary["abstract"] = content
            if '關鍵字 (Key Words)' in summary and not final_summary["keywords"]:
                content = summary.split('關鍵字 (Key Words)')[1].strip()
                final_summary["keywords"] = content

        output = "\n\n".join([
            f" ⇣ \n\n{final_summary['overall_summary']}",
            f" 𒐤 觀點 (Viewpoints) 𒐤\n{final_summary['viewpoints']}",
            f" 𒐤 摘要 (Abstract) 𒐤\n{final_summary['abstract']}",
            f" 𒐤 關鍵字 (Key Words) 𒐤\n{final_summary['keywords']}",
            f" ⇡ \n",
            f" ✡ 謝謝使用 Oli 小濃縮 (Summary) ✡ ",
        ])
        return output
    except Exception as e:
        print(f"Error: {e}")
        return "Unknown error! Please contact the owner. ok@vip.david888.com"

def extract_youtube_transcript(youtube_url):
    ydl_opts = {
        'writesubtitles': True,
        'writeautomaticsub': True,
        'skip_download': True,
        'subtitleslangs': ['zh-Hant', 'zh-Hans', 'zh-TW' , 'zh', 'en'],  # 優先順序：繁體中文，簡體中文，中文，英文
        'outtmpl': '/tmp/%(id)s.%(ext)s',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            if 'subtitles' in info or 'automatic_captions' in info:
                ydl.download([youtube_url])
                video_id = info['id']
                
                subtitle_content = None
                for lang in ['zh-Hant', 'zh-Hans', 'zh', 'en']:
                    subtitle_file = f"/tmp/{video_id}.{lang}.vtt"
                    if os.path.exists(subtitle_file):
                        with open(subtitle_file, 'r', encoding='utf-8') as file:
                            subtitle_content = file.read()
                        os.remove(subtitle_file)
                        print(f"Found and using {lang} subtitle.")
                        break  # 找到第一個可用的字幕就停止

                # 刪除所有剩餘的字幕文件
                for file in os.listdir('/tmp'):
                    if file.startswith(video_id) and file.endswith('.vtt'):
                        os.remove(f"/tmp/{file}")
                        print(f"Removed unused subtitle file: {file}")

                if subtitle_content:
                    return subtitle_content
                else:
                    print("No suitable subtitles found in specified languages.")
                    return "no transcript"
            else:
                print("No subtitles or automatic captions available for this video.")
                return "no transcript"
    except Exception as e:
        print(f"Error in extract_youtube_transcript: {e}")
        return "no transcript"



def retrieve_yt_transcript_from_url(youtube_url):
    try:
        subtitle_content = extract_youtube_transcript(youtube_url)
        if subtitle_content == "no transcript":
            if use_audio_fallback:
                print("No usable subtitles found. Falling back to audio transcription.")
                return audio_transcription(youtube_url)
            else:
                return ["該影片沒有可用的字幕，且音頻轉換功能未啟用。"]

        # 清理字幕內容
        cleaned_content = re.sub(r'WEBVTT\n\n', '', subtitle_content)
        cleaned_content = re.sub(r'\d+:\d+:\d+\.\d+ --> \d+:\d+:\d+\.\d+\n', '', cleaned_content)
        cleaned_content = re.sub(r'\n\n', ' ', cleaned_content)

        # 將清理後的內容分割成chunks
        output_chunks = []
        current_chunk = ""
        for word in cleaned_content.split():
            if len(current_chunk) + len(word) + 1 <= chunk_size:
                current_chunk += word + ' '
            else:
                output_chunks.append(current_chunk.strip())
                current_chunk = word + ' '

        if current_chunk:
            output_chunks.append(current_chunk.strip())

        return output_chunks

    except Exception as e:
        print(f"Error in retrieve_yt_transcript_from_url: {e}")
        return ["無法獲取字幕或進行音頻轉換。"]
    
def audio_transcription(youtube_url):
    try:
        # 使用 yt-dlp 下載音頻
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'/tmp/{str(uuid.uuid4())}.%(ext)s',
            'ffmpeg_location': '/usr/bin/ffmpeg',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'ffprobe_location': '/usr/bin/ffprobe'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            output_path = ydl.prepare_filename(info)

        output_path = output_path.replace(os.path.splitext(output_path)[1], ".mp3")
        audio_file = AudioSegment.from_file(output_path)

        chunk_size = 100 * 1000  # 100 秒
        chunks = [audio_file[i:i+chunk_size] for i in range(0, len(audio_file), chunk_size)]

        transcript = ""
        for i, chunk in enumerate(chunks):
            temp_file_path = f"/tmp/{str(uuid.uuid4())}.wav"
            chunk.export(temp_file_path, format="wav")

            curl_command = [
                "curl",
                "https://api.groq.com/openai/v1/audio/transcriptions",
                "-H", f"Authorization: Bearer {os.environ.get('GROQ_API_KEY', 'YOUR_GROQ_API_KEY')}",
                "-H", "Content-Type: multipart/form-data",
                "-F", f"file=@{temp_file_path}",
                "-F", "model=whisper-large-v3"
            ]

            result = subprocess.run(curl_command, capture_output=True, text=True)

            try:
                response_json = json.loads(result.stdout)
                transcript += response_json["text"]
            except KeyError as e:
                print("KeyError:", e)
                print("Response JSON:", response_json)
            except json.JSONDecodeError:
                print("Failed to decode JSON:", result.stdout)

            os.remove(temp_file_path)  # 删除临时音频文件

        os.remove(output_path)  # 删除下载的 mp3 文件

        # 将转录文本分割成 chunks
        output_sentences = transcript.split()
        output_chunks = []
        current_chunk = ""

        for word in output_sentences:
            if len(current_chunk) + len(word) + 1 <= chunk_size:
                current_chunk += word + ' '
            else:
                output_chunks.append(current_chunk.strip())
                current_chunk = word + ' '

        if current_chunk:
            output_chunks.append(current_chunk.strip())

        return output_chunks

    except Exception as e:
        print(f"Error in audio_transcription: {e}")
        return ["音頻轉錄失敗。"]    


def call_gpt_api(prompt, additional_messages=[]):
    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": model,
        "messages": additional_messages + [
            {"role": "user", "content": prompt}
        ],
    }

    try:
        response = requests.post(f"{base_url}/chat/completions", headers=headers, json=data)
        response.raise_for_status()  # 如果返回非 200 的狀態碼會拋出異常
        message = response.json()["choices"][0]["message"]["content"].strip()
        return message
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return ""


async def handle_start(update, context):
    return await handle('start', update, context)

async def handle_help(update, context):
    return await handle('help', update, context)

async def handle_summarize(update, context):
    return await handle('summarize', update, context)

async def handle_file(update, context):
    return await handle('file', update, context)

async def handle_button_click(update, context):
    return await handle('button_click', update, context)


async def handle_yt2audio(update, context):
    chat_id = update.effective_chat.id
    user_input = update.message.text.split()

    if len(user_input) < 2:  # 檢查是否有提供 URL
        await context.bot.send_message(chat_id=chat_id, text="請提供一個 YouTube 影片的 URL。例如：/yt2audio Youtube的URL")
        return

    url = user_input[1]  # 取得 YouTube URL

    try:
        # 使用 yt-dlp 下載音頻
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'/tmp/{str(uuid.uuid4())}.%(ext)s',  # 直接使用這個模板來生成文件名
            'ffmpeg_location': '/usr/bin/ffmpeg',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'ffprobe_location': '/usr/bin/ffprobe'
        }


        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # 不再使用 replace，直接使用下載後的文件
        output_path = ydl_opts['outtmpl']  # 這裡是帶有 "%(ext)s" 的模板

        # 如果你確定已經下載為 .mp3，可以直接用文件路徑
        output_path = output_path.replace("%(ext)s", "mp3")  # 如果你想保留這行也可以，確保文件是 mp3 格式

        audio_file = AudioSegment.from_file(output_path)        
 


            
        # 傳送音頻檔案給 Telegram user
        with open(output_path, 'rb') as audio:
            await context.bot.send_audio(chat_id=chat_id, audio=audio)

        os.remove(output_path)  # 刪除臨時檔案       
  

    except Exception as e:
        print(f"Error: {e}")
        await context.bot.send_message(chat_id=chat_id, text="下載或傳送音頻失敗。請檢查輸入的 YouTube URL 是否正確。")
        


async def handle_yt2text(update, context):
    chat_id = update.effective_chat.id
    user_input = update.message.text.split()

    if len(user_input) < 2:
        await context.bot.send_message(chat_id=chat_id, text="請提供一個 YouTube 影片的 URL。例如：/yt2text Youtube的URL")
        return

    url = user_input[1]

    try:
        output_chunks = retrieve_yt_transcript_from_url(url)

        if len(output_chunks) == 1 and (output_chunks[0] == "該影片沒有可用的字幕。" or output_chunks[0] == "無法獲取字幕，且音頻轉換功能未啟用。"):
            await context.bot.send_message(chat_id=chat_id, text=output_chunks[0])
            return

        # 處理正常情況的代碼
        temp_file_path = f"/tmp/{str(uuid.uuid4())}.txt"
        with open(temp_file_path, 'w', encoding='utf-8') as file:
            for chunk in output_chunks:
                file.write(chunk + "\n")

        with open(temp_file_path, 'rb') as txt_file:
            await context.bot.send_document(chat_id=chat_id, document=txt_file, filename="transcript.txt")

        os.remove(temp_file_path)  # 刪除臨時檔案

    except Exception as e:
        print(f"Error: {e}")
        await context.bot.send_message(chat_id=chat_id, text="下載或轉換文本失敗。請檢查輸入的 YouTube URL 是否正確。")

        
def process_user_input(user_input):
    youtube_pattern = re.compile(r"https?://(www\.|m\.)?(youtube\.com|youtu\.be)/")
    url_pattern = re.compile(r"https?://")

    if youtube_pattern.match(user_input):
        text_array = retrieve_yt_transcript_from_url(user_input)
    elif url_pattern.match(user_input):
        text_array = scrape_text_from_url(user_input)
    else:
        text_array = split_user_input(user_input)

    return text_array

def get_inline_keyboard_buttons():
    keyboard = [
        [InlineKeyboardButton("Explore Similar", callback_data="explore_similar")],
        [InlineKeyboardButton("Why It Matters", callback_data="why_it_matters")],
    ]
    return InlineKeyboardMarkup(keyboard)

def clear_old_commands(telegram_token):
    url = f"https://api.telegram.org/bot{telegram_token}/deleteMyCommands"
    
    scopes = ["default", "all_private_chats", "all_group_chats", "all_chat_administrators"]
    
    for scope in scopes:
        data = {"scope": {"type": scope}}
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            print(f"Old commands cleared successfully for scope: {scope}")
        else:
            print(f"Failed to clear old commands for scope {scope}: {response.text}")

def set_my_commands(telegram_token):
    clear_old_commands(telegram_token)  # 清除舊的命令
    url = f"https://api.telegram.org/bot{telegram_token}/setMyCommands"
    commands = [
        {"command": "start", "description": "確認機器人是否在線"},
        {"command": "help", "description": "顯示此幫助訊息"},
        {"command": "yt2audio", "description": "下載 YouTube 音頻"},
        {"command": "yt2text", "description": "將 YouTube 影片轉成文字"},
    ]
    data = {"commands": commands}
    response = requests.post(url, json=data)

    if response.status_code == 200:
        print("Commands set successfully.")
    else:
        print(f"Failed to set commands: {response.text}")
        
async def handle(action, update, context):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if allowed_users and str(user_id) not in allowed_users.split(','):
        await context.bot.send_message(chat_id=chat_id, text="Sorry, you are not authorized to use this bot.")
        return

    if action == 'start':
        await context.bot.send_message(chat_id=chat_id, text="我是江家機器人之一。版本20240828。 請直接輸入 URL 或想要總結的文字或PDF，無論是何種語言，我都會幫你自動總結為中文的內容。目前 URL 僅支援公開文章與 YouTube 等網址，尚未支援 Facebook 與 Twitter 貼文，YouTube 的直播影片、私人影片與會員專屬影片也無法總結喔。如要總結 YouTube 影片，請務必一次輸入一個網址，也不要寫字，傳網址就好。提醒：我無法聊天，所以不要問我問題，我只能總結文章或影片字幕。 I'm here to help you summarize text and YouTube videos.")
    elif action == 'help':
        help_text = """
        I can summarize text, URLs, PDFs and YouTube video for you.請直接輸入 URL 或想要總結的文字或PDF，無論是何種語言，我都會幫你自動總結為中文的內容。目前 URL 僅支援公開文章與 YouTube 等網址，尚未支援 Facebook 與 Twitter 貼文，YouTube 的直播影片、私人影片與會員專屬影片也無法總結喔。如要總結 YouTube 影片，請務必一次輸入一個網址，也不要寫字，傳網址就好。提醒：我無法聊天，所以不要問我問題，我只能總結文章或影片字幕。        
        Here are the available commands:
        /start - Start the bot
        /help - Show this help message
        /yt2audio <YouTube URL> - Download YouTube audio
        /yt2text <YouTube URL> - Convert YouTube video to text
        
        You can also send me any text or URL to summarize.
        """
        await context.bot.send_message(chat_id=chat_id, text=help_text)
    elif action == 'summarize':
        user_input = update.message.text
        text_array = process_user_input(user_input)
        if text_array:
            summary = summarize(text_array)
            await context.bot.send_message(chat_id=chat_id, text=summary, reply_markup=get_inline_keyboard_buttons())
        else:
            await context.bot.send_message(chat_id=chat_id, text="Sorry, I couldn't process your input. Please try again.")
    elif action == 'file':
        file = await update.message.document.get_file()
        file_path = f"/tmp/{file.file_id}.pdf"
        await file.download_to_drive(file_path)
        
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        os.remove(file_path)
        
        text_array = text.split("\n")
        summary = summarize(text_array)
        await context.bot.send_message(chat_id=chat_id, text=summary, reply_markup=get_inline_keyboard_buttons())
    elif action == 'button_click':
        query = update.callback_query
        await query.answer()
        
        if query.data == 'explore_similar':
            await context.bot.send_message(chat_id=chat_id, text="Here are some similar topics...")
        elif query.data == 'why_it_matters':
            await context.bot.send_message(chat_id=chat_id, text="This topic matters because...")



def main():
    try:
        application = ApplicationBuilder().token(telegram_token).build()
        start_handler = CommandHandler('start', handle_start)
        help_handler = CommandHandler('help', handle_help)
        yt2audio_handler = CommandHandler('yt2audio', handle_yt2audio)
        yt2text_handler = CommandHandler('yt2text', handle_yt2text)
        set_my_commands(telegram_token)
        summarize_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_summarize)
        file_handler = MessageHandler(filters.Document.PDF, handle_file)
        button_click_handler = CallbackQueryHandler(handle_button_click)
        application.add_handler(file_handler)
        application.add_handler(start_handler)
        application.add_handler(help_handler)
        application.add_handler(yt2audio_handler)
        application.add_handler(yt2text_handler)
        application.add_handler(summarize_handler)
        application.add_handler(button_click_handler)
        application.run_polling()
    except Exception as e:
        print(e)

if __name__ == '__main__':
    main()

