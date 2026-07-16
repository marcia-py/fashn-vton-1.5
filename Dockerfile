FROM pytorch/pytorch:2.8.0-cuda12.8-cudnn9-runtime

ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/workspace/huggingface

WORKDIR /workspace

COPY . .

RUN python -m pip install --upgrade pip setuptools wheel

RUN pip install -e .

RUN pip install \
    runpod \
    boto3 \
    requests

CMD ["python", "-u", "-X", "faulthandler", "handler.py"]
