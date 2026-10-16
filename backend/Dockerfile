FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY scripts ./scripts
COPY seed ./seed
COPY requirements.txt .
RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/media/audio \
    && chown -R appuser:appuser /app
USER appuser
CMD ["sh", "-c", "python scripts/init_db.py && if [ \"$SEED_DEMO\" = \"true\" ]; then python seed/seed_demo.py; fi && uvicorn app.main:app --host 0.0.0.0 --port 8000"]