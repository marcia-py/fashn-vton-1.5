FROM pytorch/pytorch:2.4.0-cuda12.1-cudnn9-runtime

WORKDIR /workspace

# Instalar dependências essenciais do Linux
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libxcb1 \
    libx11-6 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Atualizar o gestor de pacotes do Python
RUN python -m pip install --upgrade pip setuptools wheel

# Copiar todos os ficheiros do repositório para o container
COPY . /workspace/

# Instalar as bibliotecas obrigatórias diretamente (sem usar o "pip install -e .")
RUN pip install runpod boto3 requests pillow

# Configurar o caminho do Python para garantir que ele encontra os ficheiros locais
ENV PYTHONPATH=/workspace
ENV PYTHONUNBUFFERED=1

# Comando de arranque direto em formato de String (Shell Form) para estabilidade
CMD python -u handler.py

