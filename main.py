import openai
import os
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from readabilipy import simple_json_from_html_string
from tqdm import tqdm
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, filters, ApplicationBuilder
import validators

telegram_token = os.environ.get("TELEGRAM_TOKEN", "xxx")
apikey = os.environ.get("OPENAI_API_KEY", "xxx")
model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
lang = os.environ.get("TS_LANG", "English")
total_tokens=0

SUMMARIZE = range(1)

chunk_size=500

def scrape(url):
    """
    Scrape the content from the URL
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    req = requests.get(url, headers=headers)

    article = simple_json_from_html_string(req.text, use_readability=True)
    soup = BeautifulSoup(article['plain_content'], 'html.parser')
    # Use CSS selectors to find the main content
    main_content = soup.select_one('article, main, [role="main"], .content, .post')
    if main_content:
        text = main_content.get_text()
    else:
        # Strip unwanted tags if main content not found
        for tag in soup(['script', 'style', 'noscript', 'nav', 'header', 'footer', '.sidebar', '.widget', '.ad']):
            tag.decompose()
        text = soup.get_text()
    
    text = text.strip()

    return article['title'], text

def summarize(text):
    """
    Summarize the text using GPT API
    """

    def split_text(text):
        paragraphs = text.split('\n\n')  # split text into paragraphs
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

    text_chunks = split_text(text)
    text_chunks = [chunk for chunk in text_chunks if chunk] # Remove empty chunks

    print(text_chunks)

    # Call the GPT API in parallel to summarize the text chunks
    summaries = []
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(call_gpt_api, f"Summarize the following text using half the number of words: {chunk}") for chunk in text_chunks]
        for future in tqdm(futures, total=len(text_chunks), desc="Summarizing"):
            while not future.done():
                continue
            summaries.append(future.result())

    summary = ' '.join(summaries)
    if len(summaries) <= 5:
        final_summary = call_gpt_api(f"Provide a key takeaway list(at least 10 list items) for the following text: {summary}")
        return final_summary
    else:
        return summarize(summary)

def call_gpt_api(prompt):
    """
    Call GPT API to summarize the text or provide key takeaways
    """
    openai.api_key = apikey
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    message = response.choices[0].message.content.strip()
    global total_tokens
    total_tokens += response.usage.total_tokens
    return message

async def start(update, context):
    try:
        translated_text=call_gpt_api(f"Translate 'I will make your life easier, please click the menu on the bottom left to see what I can help.' to {lang}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=translated_text)
    except Exception as e:
        print(e)

async def wait_for_summarize(update, context):
    translated_text=call_gpt_api(f"Translate 'Please provide an URL.' to {lang}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=translated_text)
    return SUMMARIZE

async def handle_summarize(update, context):
    try:
        user_input = update.message.text
        if not validators.url(user_input):
            translated_text=call_gpt_api(f"Translate 'It's not a valid URL.' to {lang}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text=translated_text)
            return SUMMARIZE
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="TYPING")
        title, text = scrape(user_input)
        summary = summarize(text)
        if model == "gpt-3.5-turbo":
            cost = round(total_tokens/1000*0.02, 2)
        elif model == "gpt-4-32k":
            cost = round(total_tokens/1000*0.12, 2)
        elif model == "gpt-4":
            cost = round(total_tokens/1000*0.06, 2)
        translated_title=call_gpt_api(f"Translate '{title}' to {lang}")
        translated_summary=call_gpt_api(f"Translate '{summary}' to {lang}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{translated_title}\n\n{translated_summary}")
        print(f"Total tokens: {total_tokens}\nEstimated cost: ${cost}")
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))
    return ConversationHandler.END

async def done(update, context):
    await update.message.reply_text('👍')
    return ConversationHandler.END

def main():
    try:
        application = ApplicationBuilder().token(telegram_token).build()
        start_handler = CommandHandler('start', start)
        summarize_handler = ConversationHandler(
            entry_points=[CommandHandler('summarize', wait_for_summarize)],
            states={
                SUMMARIZE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_summarize)]
            },
            fallbacks=[CommandHandler('done', done)],
        )
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
