FROM pytorch/pytorch:2.8.0-cuda12.8-cudnn9-runtime

WORKDIR /workspace

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libxcb1 \
    libx11-6 \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip setuptools wheel

# Copiar os ficheiros do repositório para o diretório de trabalho
COPY . .

# Instalar o pacote local e as bibliotecas do RunPod
RUN pip install -e .
RUN pip install runpod boto3 requests

# Forçar permissão de leitura no handler caso o Git tenha alterado os privilégios
RUN chmod +x handler.py

# Garante que o Python procura módulos no diretório atual
ENV PYTHONPATH=/workspace

CMD ["python", "-u", "-X", "faulthandler", "handler.py"]

