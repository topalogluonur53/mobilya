FROM python:3.11-slim

# Python çıktılarının terminale doğrudan düşmesi için
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Çalışma dizinini ayarla
WORKDIR /app

# Gerekli sistem paketlerini kur (SQLite vs. için gerekli olabilir)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# İhtiyaçları kopyala ve yükle
# requirements.txt içinde gunicorn olmadığı için burada ekliyoruz (Production sunucusu için şarttır)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Projenin kalan kodlarını kopyala
COPY . .

# Port aç
EXPOSE 8000

# Veritabanını güncelle ve Gunicorn sunucusu ile ayağa kalk
CMD python manage.py migrate && gunicorn --bind 0.0.0.0:8000 config.wsgi:application
