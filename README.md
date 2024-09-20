# Summary GPT Bot / An AI-powered text summarization Telegram bot that generates concise summaries of text, URLs, PDFs and YouTube videos.
- 新增 whisper 功能，調用 groq whisper api  (目前 groq api 免費！)
- 若字幕沒有找到，會轉向用聽力辨識方式產生字幕
- USE_AUDIO_FALLBACK=1  //要不要開放無Youtube字幕的處理？ whisper 1是; 0不要
- GROQ_API_KEY 先準備 groq api key
- mongoDB 紀錄處理紀錄
  
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
## 快速開始

使用以下 Docker 命令來運行機器人：

```bash
docker run -d \
    --name telegram-bot-summary \
    --restart unless-stopped \
    -e chunk_size=6000 \
    -e LLM_MODEL=gpt-4o \
    -e USE_AUDIO_FALLBACK=1 \
    -e OPENAI_API_KEY=your_openai_api_key \
    -e GROQ_API_KEY=your_groq_api_key \
    -e TELEGRAM_TOKEN=your_telegram_bot_token \
    -e ALLOWED_USERS=user_id1,user_id2,group_id1 \
    -e MONGO_URI="your_mongodb_uri" \
    -e SHOW_PROCESSING=0 \
    tbdavid2019/telegram-bot-summary
```

## 環境變量說明

- `chunk_size`: 設置處理文本的塊大小（默認：6000）
- `LLM_MODEL`: 指定使用的語言模型（例如：gpt-4o）
- `USE_AUDIO_FALLBACK`: 如果找不到有效字幕，是否回退到音頻轉錄。設置為 `1` 以啟用，設置為 `0` 以禁用。
- `OPENAI_API_KEY`: 您的 OpenAI API 密鑰
- `GROQ_API_KEY`: 您的 Groq API 密鑰
- `TELEGRAM_TOKEN`: 您的 Telegram 機器人令牌
- `ALLOWED_USERS`: 允許使用機器人的用戶 ID 和群組 ID，用逗號分隔
- `MONGO_URI`: MongoDB 連接 URI
- `SHOW_PROCESSING`: 是否顯示處理中的消息（1 為顯示，0 為不顯示）

## 注意事項

- 請確保將 `your_openai_api_key`, `your_groq_api_key`, `your_telegram_bot_token`, 和 `your_mongodb_uri` 替換為您自己的實際值。
- `ALLOWED_USERS` 中可以包含個人用戶 ID 和群組 ID。
- 為了安全起見，建議不要直接在命令行中輸入敏感信息，而是使用環境變量文件或密鑰管理系統。




#### 3. **After Running the Docker Container**
#### 3. **運行 Docker 容器後**

Once the container is running, the Telegram bot will be online and ready to handle user requests. You can test it by sending the `/start` command to your Telegram bot.
容器運行後，Telegram 機器人將在線並準備好處理用戶的請求。你可以通過向 Telegram 機器人發送 `/start` 命令來測試它是否正常工作。

#### 4. **Stop and Remove the Docker Container**
#### 4. **停止並刪除 Docker 容器**

If you need to stop or remove the running container, you can use the following commands:
如果你需要停止或刪除正在運行的容器，可以使用以下命令：

- Stop the container:
  - 停止容器：
  ```bash
  docker stop telegram-bot-summary
  ```

- Remove the container:
  - 刪除容器：
  ```bash
  docker rm telegram-bot-summary
  ```




