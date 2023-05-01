# Summary GPT Bot

AI-powered text summarization Telegram bot that generates concise summaries of text, YouTube videos, and URLs.

## Features

- Generate summary for text
- Generate summary for YT video
- Generate summary for any URL

## Usage

| Environment Variable | Description |
|----------------------|-------------|
| OPENAI_API_KEY       | API key for OpenAI GPT API (required) |
| OPENAI_MODEL         | Model to use for text summarization (default: gpt-3.5-turbo) |
| TELEGRAM_TOKEN       | Token for Telegram API (required) |
| TS_LANG              | Language of the text to be summarized (default: English) |


```sh
docker run -d -e OPENAI_API_KEY=$YOUR_API_KEY -e TELEGRAM_TOKEN=$YOUR_TOKEN -e TS_LANG=$YOUR_LANGUAGE tonypai/ai-for-life
```