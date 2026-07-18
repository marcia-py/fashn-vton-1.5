import io
import os
import traceback
import requests
import runpod
from PIL import Image

# Declaração das variáveis globais
pipeline = None
upload_to_r2 = None

print("========== CONTAINER BOOT SUCCESSFUL ==========")

def init_worker():
    global pipeline, upload_to_r2
    print("========== STARTING RUNPOD INITIALIZATION ==========")
    
    try:
        print("Importing project modules...")
        from utils import upload_to_r2 as r2_uploader
        from fashn_vton import TryOnPipeline
        
        upload_to_r2 = r2_uploader

        print("Loading FASHN model weights...")
        pipeline = TryOnPipeline(weights_dir="./weights")
        print("Model loaded successfully into GPU!")
        
    except Exception as e:
        print("!!! CRITICAL ERROR DURING WORKER INITIALIZATION !!!")
        traceback.print_exc()
        raise e

def load_image(url):
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return Image.open(io.BytesIO(response.content)).convert("RGB")

def handler(job):
    # Proteção absoluta: envolvemos TUDO num try/except para que o worker NUNCA morra
    try:
        job_input = job["input"]
        person_url = job_input["person_url"]
        garment_url = job_input["garment_url"]
        category = job_input["category"]

        print(f"Executing Job - Person: {person_url} | Garment: {garment_url} | Cat: {category}")

        person = load_image(person_url)
        garment = load_image(garment_url)

        # Processamento do Modelo FASHN VTON 1.5
        result = pipeline(
            person_image=person,
            garment_image=garment,
            category=category,
        )

        print("Pipeline finished executing. Extracting output image...")
        output_path = "/tmp/result.png"

        # Correção Robusta: Verifica se o output é uma lista ou um objeto de imagem direto
        if hasattr(result, "images") and isinstance(result.images, list):
            final_image = result.images[0]
        elif isinstance(result, list):
            final_image = result[0]
        elif hasattr(result, "images"):
            final_image = result.images
        else:
            final_image = result

        # Gravação temporária no sistema de ficheiros do container
        final_image.save(output_path)
        print("Image saved successfully to local disk. Uploading to R2...")

        # Envio para o Cloudflare R2
        filename = upload_to_r2(
            file_path=output_path,
            bucket_name=os.environ["R2_BUCKET"],
            endpoint_url=os.environ["R2_ENDPOINT"],
            access_key_id=os.environ["R2_ACCESS_KEY"],
            secret_access_key=os.environ["R2_SECRET_KEY"],
        )

        public_url = f"{os.environ['R2_PUBLIC_URL']}/{filename}"
        print(f"Upload complete! Public URL: {public_url}")

        return {
            "success": True,
            "image_url": public_url
        }

    except Exception as e:
        print("=========================================")
        print("      EXECUTION ERROR INSIDE WORKER      ")
        print("=========================================")
        traceback.print_exc()
        
        # Devolvemos o erro como um dicionário estruturado em vez de rebentar com o Python
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

# Inicialização do RunPod Serverless
runpod.serverless.start({
    "handler": handler,
    "init": init_worker
})
