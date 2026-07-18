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

# 1. Instala o teu pacote local e as suas dependências padrão primeiro
RUN pip install -e .

# 2. Força a remoção de qualquer OpenCV ou ONNX com binds de GPU corrompidos
RUN pip uninstall -y opencv-python opencv-python-headless onnxruntime onnxruntime-gpu

# 3. Instala as versões limpas e compatíveis com Servidores
RUN pip install opencv-python-headless onnxruntime

# 4. Garante as ferramentas do RunPod e HuggingFace para downloads rápidos
RUN pip install --force-reinstall runpod
RUN pip install boto3 requests pillow transformers huggingface_hub

# ========================================================
# 5. DESCARGA AUTOMÁTICA DOS PESOS (Executada durante o Build)
# ========================================================
RUN mkdir -p /workspace/weights
RUN python scripts/download_weights.py --weights-dir /workspace/weights
# ========================================================

# Dar permissão explícita de execução ao script do Handler
RUN chmod +x handler.py

ENV PYTHONPATH=/workspace
ENV PYTHONUNBUFFERED=1

CMD ["python", "-u", "handler.py"]
