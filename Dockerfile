FROM pytorch/pytorch:2.8.0-cuda12.8-cudnn9-runtime

WORKDIR /workspace

COPY . .

RUN python -m pip install --upgrade pip setuptools wheel

RUN pip install -e .

RUN pip install runpod boto3 requests

CMD ["python", "-c", "print('Container started successfully')"]
