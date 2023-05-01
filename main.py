import openai
import os
import re
import requests
from concurrent.futures import ThreadPoolExecutor
from readabilipy import simple_json_from_html_string
from tqdm import tqdm
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, filters, ApplicationBuilder
from youtube_transcript_api import YouTubeTranscriptApi

telegram_token = os.environ.get("TELEGRAM_TOKEN", "xxx")
apikey = os.environ.get("OPENAI_API_KEY", "xxx")
model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
lang = os.environ.get("TS_LANG", "Traditional Chinese")

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
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    req = requests.get(url, headers=headers)

    article = simple_json_from_html_string(req.text, use_readability=True)
    return article['title'], article['plain_text']

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

    text_chunks = create_chunks(text_array)
    text_chunks = [chunk for chunk in text_chunks if chunk] # Remove empty chunks

    # Call the GPT API in parallel to summarize the text chunks
    summaries = []
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(call_gpt_api, f"Summarize the following text using half the number of words: {chunk}") for chunk in text_chunks]
        for future in tqdm(futures, total=len(text_chunks), desc="Summarizing"):
            while not future.done():
                continue
            summaries.append(future.result())

    if len(summaries) <= 5:
        summary = ' '.join(summaries)
        final_summary = call_gpt_api(f"Summarize the following text with 10 list items in markdown style in {lang}: {summary}")
        return final_summary
    else:
        return summarize(summaries)

def extract_youtube_transcript(youtube_url):
    video_id = youtube_url.split("watch?v=")[-1]
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript(['en', 'ja', 'ko', 'de', 'fr', 'ru', 'zh-Hant', 'zh-Hans'])
        transcript_text = ' '.join([item['text'] for item in transcript.fetch()])
        return transcript_text
    except Exception as e:
        print(f"Error: {e}")
        return ""

def retrieve_yt_transcript_from_url(youtube_url):
    output = extract_youtube_transcript(youtube_url)
    # Split output into an array based on the end of the sentence (like a dot),
    # but each chunk should be smaller than chunk_size
    output_sentences = output.split('.')
    output_chunks = []
    current_chunk = ""

    for sentence in output_sentences:
        if len(current_chunk) + len(sentence) + 1 <= chunk_size:
            current_chunk += sentence + '.'
        else:
            output_chunks.append(current_chunk.strip())
            current_chunk = sentence + '.'

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
        await context.bot.send_message(chat_id=update.effective_chat.id, text="我會為你輸入的文字、YouTube 影片連結和網址條列出十個重點。")
    except Exception as e:
        print(f"Error: {e}")

async def handle_summarize(update, context):
    try:
        user_input = update.message.text
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="TYPING")

        youtube_pattern = re.compile(r"https?://(www\.)?(youtube\.com|youtu\.be)/")
        url_pattern = re.compile(r"https?://")

        if youtube_pattern.match(user_input):
            text_array = retrieve_yt_transcript_from_url(user_input)
        elif url_pattern.match(user_input):
            title, text_array = scrape_text_from_url(user_input)
            text_array = [obj['text'] for obj in text_array]
        else:
            text_array = split_user_input(user_input)
        
        print(text_array)

        summary = summarize(text_array)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{summary}")
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))

def main():
    try:
        application = ApplicationBuilder().token(telegram_token).build()
        start_handler = CommandHandler('start', start)
        summarize_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_summarize)
        application.add_handler(start_handler)
        application.add_handler(summarize_handler)
        application.run_polling()
    except Exception as e:
        print(e)

if 'OPENAI_API_KEY' not in os.environ:
    print('⚠️ OPENAI_API_KEY environment variable is not defined')
else:
    if __name__ == '__main__':
        main()