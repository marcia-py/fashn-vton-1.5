import io
import os
import gc
import traceback
import requests
import runpod
import torch
from PIL import Image

# Variáveis globais em estado latente
pipeline = None
upload_to_r2 = None

print("========== CONTAINER BOOT SUCCESSFUL ==========")

def init_worker():
    # Deixamos o init vazio para o container arrancar sem risco de timeout
    print("========== RUNPOD SERVERLESS WORKER BOOTED ==========")
    return True

def load_image(url):
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return Image.open(io.BytesIO(response.content)).convert("RGB")

def handler(job):
    global pipeline, upload_to_r2
    
    try:
        # 1. Carregamento Tardio (Lazy Loading) do Modelo no primeiro pedido
        if pipeline is None:
            print("========== FIRST REQUEST: INITIALIZING MODEL PIPELINE ==========")
            print("Importing project modules...")
            from utils import upload_to_r2 as r2_uploader
            from fashn_vton import TryOnPipeline
            
            upload_to_r2 = r2_uploader

            # Verifica se a pasta existe antes de carregar para evitar erros silenciosos
            weights_path = "./weights"
            print(f"Checking weights directory at: {os.path.abspath(weights_path)}")
            if os.path.exists(weights_path):
                print(f"Files inside weights: {os.listdir(weights_path)}")
            else:
                print("WARNING: weights directory does not exist locally!")

            print("Loading FASHN model weights into GPU VRAM...")
            pipeline = TryOnPipeline(weights_dir=weights_path)
            print("Model pipeline loaded successfully!")

        # 2. Processamento normal do Job
        job_input = job["input"]
        person_url = job_input["person_url"]
        garment_url = job_input["garment_url"]
        category = job_input["category"]

        print(f"Executing Job ID: {job.get('id')} - Category: {category}")

        person = load_image(person_url)
        garment = load_image(garment_url)

        # Executa a inferência do Modelo FASHN VTON 1.5
        result = pipeline(
            person_image=person,
            garment_image=garment,
            category=category,
        )

        print("Pipeline finished executing. Extracting output image object...")
        output_path = "/tmp/result.png"

        if hasattr(result, "images") and isinstance(result.images, list):
            final_image = result.images[0] if len(result.images) > 0 else result.images
        elif isinstance(result, list):
            final_image = result[0] if len(result) > 0 else result
        elif hasattr(result, "images"):
            final_image = result.images
        else:
            final_image = result

        final_image.save(output_path)
        print("Image saved to local scratch disk. Executing cloud upload...")

        # Upload para o Cloudflare R2
        filename = upload_to_r2(
            file_path=output_path,
            bucket_name=os.environ["R2_BUCKET"],
            endpoint_url=os.environ["R2_ENDPOINT"],
            access_key_id=os.environ["R2_ACCESS_KEY"],
            secret_access_key=os.environ["R2_SECRET_KEY"],
        )

        public_url = f"{os.environ['R2_PUBLIC_URL']}/{filename}"
        print(f"Upload completed successfully. Link: {public_url}")

        # Limpeza de VRAM
        del person, garment, final_image
        if os.path.exists(output_path):
            os.remove(output_path)
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        return {
            "success": True,
            "image_url": public_url
        }

    except Exception as e:
        print("=========================================")
        print("      EXECUTION ERROR INSIDE WORKER      ")
        print("=========================================")
        traceback.print_exc()
        
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

runpod.serverless.start({
    "handler": handler,
    "init": init_worker
})
