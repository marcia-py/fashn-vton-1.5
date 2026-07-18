import io
import os
import gc
import traceback
import requests
import runpod
import torch  # Força o controlo da libertação de VRAM de forma segura
from PIL import Image

# Variáveis globais
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
        print("Model loaded successfully into GPU VRAM!")
        
    except Exception as e:
        print("!!! CRITICAL ERROR DURING WORKER INITIALIZATION !!!")
        traceback.print_exc()
        raise e

def load_image(url):
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return Image.open(io.BytesIO(response.content)).convert("RGB")

def handler(job):
    global pipeline, upload_to_r2
    
    try:
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

        # Trata o retorno de forma dinâmica de acordo com a variação do objeto
        if hasattr(result, "images") and isinstance(result.images, list):
            final_image = result.images[0]
        elif isinstance(result, list):
            final_image = result[0]
        elif hasattr(result, "images"):
            final_image = result.images
        else:
            final_image = result

        # Guarda a imagem localmente temporária
        final_image.save(output_path)
        print("Image saved to local scratch disk. Executing cloud upload...")

        # Upload síncrono para o Cloudflare R2
        filename = upload_to_r2(
            file_path=output_path,
            bucket_name=os.environ["R2_BUCKET"],
            endpoint_url=os.environ["R2_ENDPOINT"],
            access_key_id=os.environ["R2_ACCESS_KEY"],
            secret_access_key=os.environ["R2_SECRET_KEY"],
        )

        public_url = f"{os.environ['R2_PUBLIC_URL']}/{filename}"
        print(f"Upload completed successfully. Link: {public_url}")

        # --- GESTÃO SEGURA DE MEMÓRIA PÓS-TAREFA ---
        # Libertamos referências de memória locais para evitar Out of Memory na tarefa seguinte
        del person
        del garment
        del final_image
        if os.path.exists(output_path):
            os.remove(output_path)
            
        # Força o Python e o CUDA a limparem lixo sem fechar o processo principal
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        print("Memory footprint cleaned. Returning result back to queue...")

        # Conclusão segura da resposta
        return {
            "success": True,
            "image_url": public_url
        }

    except Exception as e:
        print("=========================================")
        print("      EXECUTION ERROR INSIDE WORKER      ")
        print("=========================================")
        traceback.print_exc()
        
        # Limpeza mesmo em caso de falha catastrófica
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

# Execução do Orquestrador Serverless
runpod.serverless.start({
    "handler": handler,
    "init": init_worker
})

