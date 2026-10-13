FROM python:3.12-slim
WORKDIR /app/monitor/backend
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=5000
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONPATH=/app
EXPOSE 5000
CMD ["sh", "-c", "exec waitress-serve --host=0.0.0.0 --port=$PORT app:app"]
