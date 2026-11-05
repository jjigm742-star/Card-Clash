FROM python:3.12-slim
WORKDIR /game
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && python -m playwright install --with-deps chromium
COPY app ./app
COPY server.py ./server.py
ENV PYTHONUNBUFFERED=1 PORT=8000
EXPOSE 8000
CMD ["sh","-c","exec uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"]
