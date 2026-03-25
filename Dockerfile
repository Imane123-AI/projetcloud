# ── Base image ────────────────────────────────────────────────
FROM python:3.11-slim

# ── Métadonnées ───────────────────────────────────────────────
LABEL maintainer="Master DSBD & IA"
LABEL version="2.0.0"
LABEL description="DevShop — E-Commerce API"

# ── Répertoire de travail ─────────────────────────────────────
WORKDIR /app

# ── Dépendances système ───────────────────────────────────────
#RUN apt-get update && apt-get install -y \
#    gcc \
#    && rm -rf /var/lib/apt/lists/*

# ── Dépendances Python ────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Code source ───────────────────────────────────────────────
COPY . .

# ── Port exposé ───────────────────────────────────────────────
EXPOSE 5000

# ── Healthcheck Docker ────────────────────────────────────────
#HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
#    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"

# ── Lancement ─────────────────────────────────────────────────
CMD ["python", "app.py"]
