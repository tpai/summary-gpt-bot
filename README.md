# Summary GPT Bot

An AI-powered text summarization Telegram bot that generates concise summaries of text, URLs, PDFs and YouTube videos.

- EN Bot: https://t.me/summarygptenbot
- 繁中 Bot: https://t.me/summarygptzhtwbot

## Features

- Supports text
- Supports URLs
- Supports PDFs
- Supports YouTube videos (no support for YouTube Shorts)

## Usage

Launch your own GPT-4 summary bot with 32k token context in one line command 🚀

```sh
docker run -d -e TELEGRAM_TOKEN=$YOUR_TG_TOKEN -e OPENAI_API_KEY=$YOUR_API_KEY -e OPENAI_MODEL=gpt-4-32k -e CHUNK_SIZE=20000 -e TS_LANG=$YOUR_LANGUAGE tonypai/summary-gpt-bot:latest
```

| Environment Variable | Description |
|----------------------|-------------|
| TELEGRAM_TOKEN       | Token for Telegram API (required) |
| OPENAI_API_KEY       | API key for OpenAI GPT API (required) |
| OPENAI_MODEL         | Model to use for text summarization (default: gpt-3.5-turbo-16k) |
| CHUNK_SIZE           | The maximum token of a chunk when receiving a large input (default: 10000) |
| TS_LANG              | Language of the text to be summarized (default: Taiwanese Mandarin) |
