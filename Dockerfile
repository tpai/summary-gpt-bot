FROM debian:11-slim

# 安裝必要的工具和依賴，包括 Python 3、ffmpeg 和 curl
RUN apt-get update && \
    apt-get install --no-install-suggests --no-install-recommends --yes \
    python3 python3-pip python3-dev gcc libpython3-dev ffmpeg curl

# 升級 pip 並安裝 Python 依賴
RUN python3 -m pip install --upgrade pip setuptools wheel

# 複製 requirements.txt 到容器中
COPY requirements.txt /app/requirements.txt

# 安裝 Python 依賴
RUN pip3 install --disable-pip-version-check -r /app/requirements.txt

WORKDIR /app

# 複製應用程式碼到容器
COPY main.py .

# 設置環境變量以明確指定 ffmpeg 的位置
ENV PATH="/usr/bin:${PATH}"

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python3", "-u", "main.py"]
