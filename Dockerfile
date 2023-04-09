FROM python:3.8

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY main.py .

CMD ["python", "main.py"]