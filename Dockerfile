# CUDA 12.8 + PyTorch
FROM runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/workspace/huggingface

WORKDIR /workspace

COPY . .

RUN python -m pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements-runpod.txt

RUN pip install --no-deps -e .

# Download all FASHN weights during build
RUN python download_weights.py

CMD ["python", "-u", "handler.py"]