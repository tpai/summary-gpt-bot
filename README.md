# Summary GPT Bot / An AI-powered text summarization Telegram bot that generates concise summaries of text, URLs, PDFs and YouTube videos.
- 新增 whisper 功能，調用 groq whisper api  (目前 groq api 免費！)
- 若字幕沒有找到，會轉向用聽力辨識方式產生字幕
- USE_AUDIO_FALLBACK=1  //要不要開放無Youtube字幕的處理？ whisper 1是; 0不要
- GROQ_API_KEY 先準備 groq api key
  
<img width="575" alt="image" src="https://github.com/user-attachments/assets/7465b142-7fa1-4889-9f98-d74194ca72e3">
<img width="600" alt="image" src="https://github.com/user-attachments/assets/c69253fc-24ff-4378-9df0-eb14821cabdd">


## 示範帳號

https://t.me/quantaar_bot


## Features

- Supports text
- Supports URLs
- Supports PDFs
- Supports YouTube videos (no support for YouTube Shorts)

## Usage
以下是包含英文和繁體中文的說明，針對使用 Docker 來運行你的 Telegram 機器人進行指導。

---

### Telegram Bot Docker Setup Guide
### Telegram 機器人 Docker 設置指南

#### 1. **Pull the Docker Image**
#### 1. **拉取 Docker 映像**

To pull the Docker image from Docker Hub, use the following command:
從 Docker Hub 拉取映像，請使用以下命令：

```bash
docker pull tbdavid2019/telegram-bot-summary:latest
```

#### 2. **Run the Docker Container**
#### 2. **運行 Docker 容器**

After pulling the image, you can run the Docker container using the following command. This command includes some required environment variables:
拉取映像後，你可以使用以下命令運行 Docker 容器。此命令包括一些必須配置的環境變數：

```bash
docker run -d \
    --name summary-gpt-bot \
    --restart unless-stopped \
    -e chunk_size=6000 \
    -e LLM_BASE_URL=https://api.groq.com/openai/v1<也可以換成 openai 的 baseURL> \
    -e LLM_MODEL=llama-3.1-70b-versatile<也可以換成gpt-4o等其他模型>  \ 
    -e OPENAI_API_KEY=<your-openai-api-key 或 你的groq key> \
    -e USE_AUDIO_FALLBACK=1<要不要啟動無字幕Youtube影片處理耗用token 這裡改成免費的groq Whisper API）> \
    -e GROQ_API_KEY=<你的Groq API KEY> \
    -e TELEGRAM_TOKEN=<your-telegram-bot-token> \
    -e ALLOWED_USERS=<telegram-user-id-1>,<telegram-user-id-2>,... \
    tbdavid2019/telegram-bot-summary:latest
```

Replace `<your-openai-api-key>` with your OpenAI API key, `<your-telegram-bot-token>` with your Telegram bot token, and `<telegram-user-id-1>,<telegram-user-id-2>,...` with the Telegram user or group IDs that are allowed to use the bot.
將 `<your-openai-api-key>` 替換為你的 OpenAI API 密鑰，將 `<your-telegram-bot-token>` 替換為你的 Telegram 機器人令牌，並將 `<telegram-user-id-1>,<telegram-user-id-2>,...` 替換為允許使用機器人的 Telegram 用戶或羣組 ID。

#### 3. **Environment Variables Explanation**
#### 3. **環境變數說明**

- `chunk_size`: The size of each text chunk for processing. Default is `6000`.
- `chunk_size`: 每個處理文本塊的大小。默認值為 `6000`。
- `LLM_MODEL`: The language model to use. Default is `gpt-4o-mini`.
- `LLM_MODEL`: 要使用的語言模型。默認值為 `gpt-4o-mini`。
- `USE_AUDIO_FALLBACK`: Whether to fall back to audio transcription if no valid subtitles are found. Set to `1` to enable, `0` to disable.
- `USE_AUDIO_FALLBACK`: 如果找不到有效字幕，是否回退到音頻轉錄。設置為 `1` 以啟用，設置為 `0` 以禁用。
- `OPENAI_API_KEY`: Your OpenAI API key for accessing the GPT model.
- `OPENAI_API_KEY`: 用於訪問 GPT 模型的 OpenAI API 密鑰。
- `TELEGRAM_TOKEN`: Your Telegram Bot API token for accessing the Telegram bot.
- `TELEGRAM_TOKEN`: 用於訪問 Telegram 機器人的 Telegram Bot API 令牌。
- `ALLOWED_USERS`: Comma-separated list of Telegram user or group IDs that are allowed to use the bot.
- `ALLOWED_USERS`: 允許使用機器人的 Telegram 用戶或羣組 ID 列表，用逗號分隔。

#### 4. **After Running the Docker Container**
#### 4. **運行 Docker 容器後**

Once the container is running, the Telegram bot will be online and ready to handle user requests. You can test it by sending the `/start` command to your Telegram bot.
容器運行後，Telegram 機器人將在線並準備好處理用戶的請求。你可以通過向 Telegram 機器人發送 `/start` 命令來測試它是否正常工作。

#### 5. **Stop and Remove the Docker Container**
#### 5. **停止並刪除 Docker 容器**

If you need to stop or remove the running container, you can use the following commands:
如果你需要停止或刪除正在運行的容器，可以使用以下命令：

- Stop the container:
  - 停止容器：
  ```bash
  docker stop summary-gpt-bot
  ```

- Remove the container:
  - 刪除容器：
  ```bash
  docker rm summary-gpt-bot
  ```

#### 6. **Update the Docker Image**
#### 6. **更新 Docker 映像**

When the image has a new update, you can update the container with the following commands:
當映像有新更新時，你可以使用以下命令更新容器：

```bash
docker pull tbdavid2019/telegram-bot-summary:latest
docker stop summary-gpt-bot
docker rm summary-gpt-bot
docker run -d \
    --name summary-gpt-bot \
    --restart unless-stopped \
    -e chunk_size=6000 \
    -e LLM_BASE_URL=https://api.groq.com/openai/v1<也可以換成 openai 的 baseURL> \
    -e LLM_MODEL=llama-3.1-70b-versatile<也可以換成gpt-4o等其他模型>  \ 
    -e OPENAI_API_KEY=<your-openai-api-key 或 你的groq key> \
    -e USE_AUDIO_FALLBACK=1<要不要啟動無字幕Youtube影片處理耗用token 這裡改成免費的groq Whisper API）> \
    -e GROQ_API_KEY=<你的Groq API KEY> \
    -e TELEGRAM_TOKEN=<your-telegram-bot-token> \
    -e ALLOWED_USERS=<telegram-user-id-1>,<telegram-user-id-2>,... \
    tbdavid2019/telegram-bot-summary:latest
```



LLM Variables

| Environment Variable | Description |
|----------------------|-------------|
| LLM_BASE_URL       | LLM BASEURL |
| OPENAI_API_KEY       | API key for OpenAI API |
| GROQ_API_KEY       | API key for GROQ API |


Bot Variables

| Environment Variable | Description |
|----------------------|-------------|
| CHUNK_SIZE           | The maximum token of a chunk when receiving a large input (default: 2100) |
| LLM_MODEL            | LLM Model to use for text summarization (default: chatgpt-4o-latest) |
| TELEGRAM_TOKEN       | Token for Telegram API (required) |
| TS_LANG              | Language of the text to be summarized (default: Taiwanese Mandarin) |
| DDG_REGION           | The region of the duckduckgo search (default: wt-wt) 👉[Regions](https://github.com/deedy5/duckduckgo_search#regions) |
| ALLOWED_USERS        | A list of user IDs allowed to use. Asking @myidbot for Telegram ID (optional) |
| USE_AUDIO_FALLBACK | 啟用Youtube無字幕影片聽寫處理 |

