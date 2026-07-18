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

# Atualizar as ferramentas de pacotes Python
RUN python -m pip install --upgrade pip setuptools wheel

# Copiar todos os ficheiros do repositório para o container
COPY . /workspace/

# 1. Instala primeiro o seu pacote local
RUN pip install -e .

# 2. Instala as dependências oficiais por cima para resolver conflitos de nomes (Crucial)
RUN pip install --force-reinstall runpod
RUN pip install boto3 requests pillow torch

# Dar permissão explícita de execução ao script do Handler
RUN chmod +x handler.py

ENV PYTHONPATH=/workspace
ENV PYTHONUNBUFFERED=1

CMD ["python", "-u", "handler.py"]
