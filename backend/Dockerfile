FROM python:3.11-slim

# System deps needed by OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ml_models package lives one level up in the repo; mounted via docker-compose
# for local dev. In production, COPY it into the image instead:
# COPY ../ml_models /ml_models

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
