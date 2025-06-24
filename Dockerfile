# Railway強制リセット - Flask専用
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY app.py ./
EXPOSE 8000

# Flask強制実行
CMD ["python", "app.py"]