# Multi-stage build pour optimiser la taille de l'image
FROM python:3.11-slim as builder

# Variables d'environnement pour Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Installer les dépendances système nécessaires pour la compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Créer un répertoire de travail
WORKDIR /app

# Copier uniquement requirements.txt pour profiter du cache Docker
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --user --no-warn-script-location -r requirements.txt

# ============================================
# Stage final - Image de production minimale
# ============================================
FROM python:3.11-slim

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/root/.local/bin:$PATH

# Créer un utilisateur non-root pour la sécurité
RUN useradd -m -u 1000 freeda && \
    mkdir -p /app/data && \
    chown -R freeda:freeda /app

# Copier les dépendances depuis le builder
COPY --from=builder --chown=freeda:freeda /root/.local /home/freeda/.local

# Définir le répertoire de travail
WORKDIR /app

# Copier le code de l'application
COPY --chown=freeda:freeda ./app ./app
COPY --chown=freeda:freeda ./main.py .

# Passer à l'utilisateur non-root
USER freeda

# Exposer le port
EXPOSE 8000

# Health check pour AWS ECS/ELB
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"

# Commande de démarrage
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
