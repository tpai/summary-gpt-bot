FROM python:3.8

WORKDIR /app

# Install Node.js 18
RUN curl -sL https://deb.nodesource.com/setup_18.x | bash -
RUN apt-get update && apt-get install -y nodejs

COPY requirements.txt .

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY main.py .

ENV PYTHONUNBUFFERED=1

CMD ["python", "-u", "main.py"]
