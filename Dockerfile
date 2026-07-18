# Utiliza uma imagem estável com suporte completo a GPUs modernas (RTX 3090, L4)
FROM pytorch/pytorch:2.4.0-cuda12.1-cudnn9-runtime

WORKDIR /workspace

# Instalar dependências essenciais do Linux para processamento de imagem (OpenCV/PIL)
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libxcb1 \
    libx11-6 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Atualizar ferramentas de pacotes Python
RUN python -m pip install --upgrade pip setuptools wheel

# Copiar os ficheiros do repositório antes de instalar as dependências
COPY . .

# Instalar as bibliotecas Python necessárias
RUN pip install -e .
RUN pip install runpod boto3 requests pillow

# Dar permissão explícita de execução ao script do Handler
RUN chmod +x handler.py

ENV PYTHONPATH=/workspace

# Comando de inicialização simplificado para evitar conflito de parsing no RunPod
CMD ["python", "-u", "handler.py"]

