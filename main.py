import openai
import os
import re
import trafilatura
from PyPDF2 import PdfReader
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from telegram.ext import CommandHandler, MessageHandler, filters, ApplicationBuilder
from youtube_transcript_api import YouTubeTranscriptApi

telegram_token = os.environ.get("TELEGRAM_TOKEN", "xxx")
apikey = os.environ.get("OPENAI_API_KEY", "xxx")
model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo-16k")
lang = os.environ.get("TS_LANG", "Taiwanese Mandarin")
chunk_size= os.environ.get("CHUNK_SIZE", 10000)

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
        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(downloaded, include_formatting=True)
        if text is None:
            return []
        text_chunks = text.split("\n")
        article_content = [text for text in text_chunks if text]
    except Exception as e:
        print(f"Error: {e}")

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
        video_id_match = re.search(r"(?<=v=)[^&]+|(?<=youtu.be/)[^?|\n]+", youtube_url)
        video_id = video_id_match.group(0) if video_id_match else None
        if video_id is None:
            return "no transcript"
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript(['en', 'ja', 'ko', 'de', 'fr', 'ru', 'zh-TW', 'zh-CN', 'zh-Hant', 'zh-Hans'])
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
        await context.bot.send_message(chat_id=update.effective_chat.id, text="I can summarize the text, URL, PDF and YouTube video for you.")
    except Exception as e:
        print(f"Error: {e}")

async def help(update, context):
    try:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Please report bugs here. 👉 https://github.com/tpai/summary-gpt-bot")
    except Exception as e:
        print(f"Error: {e}")

async def handle_summarize(update, context):

    chat_id = update.effective_chat.id
    message_id = update.message.message_id

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

        if not text_array:
            raise ValueError("No content found to summarize.")
        
        await context.bot.send_chat_action(chat_id=chat_id, action="TYPING")
        summary = summarize(text_array)
        await context.bot.send_message(chat_id=chat_id, text=f"{summary}", reply_to_message_id=message_id)
    except Exception as e:
        print(f"Error: {e}")
        await context.bot.send_message(chat_id=chat_id, text=str(e))

async def handle_file(update, context):
    
    chat_id = update.effective_chat.id
    message_id = update.message.message_id
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

        await context.bot.send_chat_action(chat_id=chat_id, action="TYPING")
        summary = summarize(text_array)
        await context.bot.send_message(chat_id=chat_id, text=f"{summary}", reply_to_message_id=message_id)
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