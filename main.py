import asyncio
import openai
import os
import re
import requests
from PyPDF2 import PdfReader
from newspaper import Article
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor
from readabilipy import simple_json_from_html_string
from tqdm import tqdm
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, filters, ApplicationBuilder
from youtube_transcript_api import YouTubeTranscriptApi

telegram_token = os.environ.get("TELEGRAM_TOKEN", "xxx")
apikey = os.environ.get("OPENAI_API_KEY", "xxx")
model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
lang = os.environ.get("TS_LANG", "Taiwanese Mandarin")

chunk_size= 1500

def split_user_input(text):
    # Split the input text into paragraphs
    paragraphs = text.split('\n')

    # Remove empty paragraphs and trim whitespace
    paragraphs = [paragraph.strip() for paragraph in paragraphs if paragraph.strip()]

    return paragraphs

def scrape_text_from_url(url):
    """
    Scrape the content from the URL
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL' # Set default ciphers for urllib3
        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5) # Fix max retries error
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        req = session.get(url, headers=headers)
        req.encoding = 'utf-8' # Fix text encoding error
        article = simple_json_from_html_string(req.text, use_readability=True)
        text_array = [obj['text'] for obj in article['plain_text']]
        article_content = list(dict.fromkeys(text_array)) # Remove duplicated items from the array
    except Exception as e:
        print(f"Error: {e}")
        # fallback to newspaper library
        article = Article(url)
        article.download()
        article.parse()
        article_content = [text for text in article.text.split("\n\n") if text]

    return article_content

def summarize(text_array):
    """
    Summarize the text using GPT API
    """

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
        text_chunks = [chunk for chunk in text_chunks if chunk] # Remove empty chunks

        # Call the GPT API in parallel to summarize the text chunks
        summaries = []
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(call_gpt_api, f"Summarize the following text using half the number of words:\n{chunk}") for chunk in text_chunks]
            for future in tqdm(futures, total=len(text_chunks), desc="Summarizing"):
                summaries.append(future.result())

        if len(summaries) <= 5:
            summary = ' '.join(summaries)
            with tqdm(total=1, desc="Final summarization") as progress_bar:
                final_summary = call_gpt_api(f"Please summarize the following text as a markdown list in {lang}, ensuring the terminology remains untranslated:\n{summary}")
                progress_bar.update(1)
            return final_summary
        else:
            return summarize(summaries)
    except Exception as e:
        print(f"Error: {e}")
        return "Unknown error! Please contact the developer."

def extract_youtube_transcript(youtube_url):
    try:
        video_id = youtube_url.split('v=')[1].split('&')[0]
        if video_id is None:
            return "no transcript"
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript(['en', 'ja', 'ko', 'de', 'fr', 'ru', 'zh-TW', 'zh-CN'])
        transcript_text = ' '.join([item['text'] for item in transcript.fetch()])
        return transcript_text
    except Exception as e:
        print(f"Error: {e}")
        return "no transcript"

def retrieve_yt_transcript_from_url(youtube_url):
    output = extract_youtube_transcript(youtube_url)
    if output == 'no transcript':
        raise ValueError("There's no valid transcript in this video.")
    # Split output into an array based on the end of the sentence (like a dot),
    # but each chunk should be smaller than chunk_size
    output_sentences = output.split(' ')
    output_chunks = []
    current_chunk = ""

    for sentence in output_sentences:
        if len(current_chunk) + len(sentence) + 1 <= chunk_size:
            current_chunk += sentence + ' '
        else:
            output_chunks.append(current_chunk.strip())
            current_chunk = sentence + ' '

    if current_chunk:
        output_chunks.append(current_chunk.strip())
    return output_chunks

def call_gpt_api(prompt):
    """
    Call GPT API to summarize the text or provide key takeaways
    """
    try:
        openai.api_key = apikey
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        message = response.choices[0].message.content.strip()
        return message
    except Exception as e:
        print(f"Error: {e}")
        return ""

async def start(update, context):
    try:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="I will summarize the text, URL, PDF and YouTube video for you.")
    except Exception as e:
        print(f"Error: {e}")

async def help(update, context):
    try:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Please report bugs here. 👉 https://github.com/tpai/summary-gpt-bot")
    except Exception as e:
        print(f"Error: {e}")

async def handle_summarize(update, context):
    try:
        user_input = update.message.text
        
        print(user_input)
        
        youtube_pattern = re.compile(r"https?://(www\.|m\.)?(youtube\.com|youtu\.be)/")
        url_pattern = re.compile(r"https?://")

        if youtube_pattern.match(user_input):
            text_array = retrieve_yt_transcript_from_url(user_input)
        elif url_pattern.match(user_input):
            text_array = scrape_text_from_url(user_input)
        else:
            text_array = split_user_input(user_input)
        
        print(text_array)
        
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="TYPING")
        summary = summarize(text_array)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{summary}")
    except Exception as e:
        print(f"Error: {e}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))

async def handle_file(update, context):
    
    file_path = f"{update.message.document.file_unique_id}.pdf"
    
    try:
        file = await context.bot.get_file(update.message.document)
        await file.download_to_drive(file_path)

        text_array = []
        reader = PdfReader(file_path)
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text = page.extract_text()                    
            text_array.append(text)

        print(file_path)

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="TYPING")
        summary = summarize(text_array)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{summary}")
    except Exception as e:
        print(f"Error: {e}")

    try:
        os.remove(file_path)
    except Exception as e:
        print(f"Error: {e}")

def main():
    try:
        application = ApplicationBuilder().token(telegram_token).build()
        start_handler = CommandHandler('start', start)
        help_handler = CommandHandler('help', help)
        summarize_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_summarize)
        file_handler = MessageHandler(filters.Document.PDF, handle_file)
        application.add_handler(file_handler)
        application.add_handler(start_handler)
        application.add_handler(help_handler)
        application.add_handler(summarize_handler)
        application.run_polling()
    except Exception as e:
        print(e)

if 'OPENAI_API_KEY' not in os.environ:
    print('⚠️ OPENAI_API_KEY environment variable is not defined')
else:
    if __name__ == '__main__':
        main()