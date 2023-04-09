import requests
import openai
import os
from bs4 import BeautifulSoup
from tqdm import tqdm
from readabilipy import simple_json_from_html_string
import streamlit as st

apikey = os.environ.get("OPENAI_API_KEY", "xxx")
model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
lang = os.environ.get("TS_LANG", "en_us")
total_tokens=0
chunk_size=500

def scrape(url):
    """
    Scrape the content from the URL
    """
    req = requests.get(url)
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

    return article['title'], text

def summarize(text):
    """
    Summarize the text using GPT API
    """
    from concurrent.futures import ThreadPoolExecutor

    # Split the text into chunks
    import re
    text_chunks = re.findall(r'\b.{1,' + str(chunk_size) + r'}\b(?:\s+|$)', text)
    
    # Call the GPT API in parallel to summarize the text chunks
    summaries = []
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(call_gpt_api, chunk, False) for chunk in text_chunks]
        for future in tqdm(futures, total=len(text_chunks), desc="Summarizing"):
            while not future.done():
                continue
            summaries.append(future.result())

    summary = ' '.join(summaries)
    if len(summaries) <= 5:
        final_summary = call_gpt_api(summary, True)
        return final_summary
    else:
        return summarize(summary)

def call_gpt_api(text, is_key_takeaway):
    """
    Call GPT API to summarize the text or provide key takeaways
    """
    openai.api_key = apikey
    if is_key_takeaway:
        prompt = f"Provide a key takeaway list for the following text in {lang}: {text}"
    else:
        prompt = f"Summarize the following text using half the number of words in {lang}: {text}"
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    message = response.choices[0].message.content.strip()
    global total_tokens
    total_tokens += response.usage.total_tokens
    return message

if 'OPENAI_API_KEY' not in os.environ:
    st.warning('OPENAI_API_KEY environment variable is not defined', icon="⚠️")
else:
    st.title("Text Summarizer")
    url_input=st.empty()
    url=url_input.text_input("Enter URL", key="url")
    if url:
        total_tokens=0
        pg_bar=st.progress(0)
        with st.spinner("Loading..."):
            title, text = scrape(url)
            pg_bar.progress(30)
            summary = summarize(text)
            pg_bar.progress(100)
            if model == "gpt-3.5-turbo":
                cost = round(total_tokens/1000*0.02, 2)
            elif model == "gpt-4-32k":
                cost = round(total_tokens/1000*0.12, 2)
            elif model == "gpt-4":
                cost = round(total_tokens/1000*0.06, 2)

        st.text(f"Total tokens: {total_tokens}\nEstimated cost: ${cost}")
        st.markdown(f"#### {title}\n{summary}")