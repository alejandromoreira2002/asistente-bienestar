# Base: Python 3.10 slim
FROM python:3.10-slim

# Rutas persistentes y configuración
ENV APP_HOME=/home/asistente-energetico \
    APP_STORAGE=/home/asistente-energetico/storage \
    XDG_CACHE_HOME=/home/asistente-energetico/storage/.cache \
    HF_HOME=/home/asistente-energetico/storage/.cache/huggingface \
    PYTORCH_HUB=/home/asistente-energetico/storage/.cache/torch/hub \
    CTRANSLATE2_CACHE_DIR=/home/asistente-energetico/storage/.cache/ctranslate2 \
    TTS_HOME=/home/asistente-energetico/storage/.local/share/tts \
    PM2_HOME=/home/asistente-energetico/storage/.pm2 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

# Instala dependencias del sistema completas para PyTorch
RUN apt-get update && apt-get install -y --no-install-recommends \
    sudo \
    nano \
    curl \
    wget \
    git \
    ca-certificates \
    openssh-server \
    nodejs \
    npm \
    ffmpeg \
    libsndfile1 \
    build-essential \
    gfortran \
    libopenblas-dev \
    libgomp1 \
    libjpeg62-turbo-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Configura pip, npm y SSH
RUN python3 -m ensurepip --upgrade \
 && python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel \
 && npm install -g pm2 --unsafe-perm \
 && npm cache clean --force \
 && mkdir -p /var/run/sshd \
 && echo 'root:root' | chpasswd \
 && sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config \
 && sed -i 's/#PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Establecer directorio de trabajo
WORKDIR ${APP_HOME}

# Copiar requirements.txt primero (para aprovechar caché de Docker)
COPY requirements.txt ./

# Instalar dependencias Python con reintentos para PyTorch
RUN python3 -m pip install --no-cache-dir -r requirements.txt || \
    (echo "Reintentando instalación con index alternativo..." && \
     python3 -m pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch && \
     python3 -m pip install --no-cache-dir -r requirements.txt)

# Verificar instalación de PyTorch
RUN python3 -c "import torch; print(f'PyTorch {torch.__version__} instalado correctamente')" || \
    (echo "ERROR: PyTorch no se instaló correctamente" && exit 1)

# Copiar el resto del proyecto
COPY . .

# Crear directorios necesarios y establecer permisos
RUN mkdir -p ${APP_STORAGE} \
             ${PM2_HOME} \
             ${HF_HOME} \
             ${PYTORCH_HUB} \
             ${CTRANSLATE2_CACHE_DIR} \
             ${TTS_HOME} \
             logs \
 && chmod -R 777 ${APP_STORAGE} ${PM2_HOME}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:3005/ || exit 1

EXPOSE 22 3005

CMD service ssh start && pm2-runtime start ecosystem.config.js
