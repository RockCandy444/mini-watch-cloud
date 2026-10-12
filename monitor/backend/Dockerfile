FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY monitor/backend/requirements.txt /app/monitor/backend/requirements.txt
RUN pip install --no-cache-dir -r monitor/backend/requirements.txt
COPY common /app/common
COPY monitor/__init__.py /app/monitor/__init__.py
COPY monitor/backend /app/monitor/backend
WORKDIR /app/monitor/backend
ENV PYTHONPATH=/app
EXPOSE 5000
CMD ["flask", "--app", "app", "run", "--host=0.0.0.0", "--port=5000"]
