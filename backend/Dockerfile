FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get -o Acquire::Retries=2 -o Acquire::https::Timeout=30 update \
    && apt-get -o Acquire::Retries=2 -o Acquire::https::Timeout=30 install -y --no-install-recommends postgresql-client \
    && rm -rf /var/lib/apt/lists/*
COPY app ./app
COPY migrations /migrations
COPY scripts/migrate.sh /app/scripts/migrate.sh
RUN useradd --create-home campus
USER campus
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn app.main:app --host ${BIND_HOST:-0.0.0.0} --port ${PORT:-8000}"]
