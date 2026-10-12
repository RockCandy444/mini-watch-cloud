FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY general/requirements.txt /app/general/requirements.txt
RUN pip install --no-cache-dir -r general/requirements.txt
COPY common /app/common
COPY general /app/general
COPY monitor/__init__.py /app/monitor/__init__.py
COPY monitor/backend /app/monitor/backend
WORKDIR /app/general
EXPOSE 5000
CMD ["flask", "--app", "app", "run", "--host=0.0.0.0", "--port=5000"]
