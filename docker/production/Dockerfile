FROM python:3.12-alpine

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PIP_NO_CACHE_DIR 1

WORKDIR /app

COPY ../../ /app
COPY ./script/gunicorn/gunicorn.conf.py /etc/gunicorn/gunicorn.conf.py
COPY ./script/start-prod.sh /app/script/start.sh

RUN chmod +x /app/script/start.sh && \
    pip install --upgrade pip && \
    pip install --no-cache-dir --upgrade -r requirements.txt

ENTRYPOINT ["sh", "-c", "./script/start.sh"]