FROM pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime

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

# Instala primeiro o seu pacote local
RUN pip install -e .

# Remove qualquer versão errada ou residual do OpenCV e força a versão HEADLESS
RUN pip uninstall -y opencv-python opencv-python-headless
RUN pip install opencv-python-headless

# Remove versões incompatíveis do ONNX e força a instalação correta para CUDA 12.x
RUN pip uninstall -y onnxruntime onnxruntime-gpu
RUN pip install onnxruntime-gpu --extra-index-url https://visualstudio.com

# Instala as dependências oficiais por cima para garantir estabilidade absoluta
RUN pip install --force-reinstall runpod
RUN pip install boto3 requests pillow transformers

# Dar permissão explícita de execução ao script do Handler
RUN chmod +x handler.py

ENV PYTHONPATH=/workspace
ENV PYTHONUNBUFFERED=1

CMD ["python", "-u", "handler.py"]
