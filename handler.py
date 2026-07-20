import io
import os
import gc
import traceback
import requests
import runpod
import torch
from PIL import Image

pipeline = None
upload_to_r2 = None

print("========== CONTAINER BOOT SUCCESSFUL ==========")

def init_worker():
    print("========== RUNPOD SERVERLESS WORKER BOOTED ==========")
    return True

def load_image(url):
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return Image.open(io.BytesIO(response.content)).convert("RGB")

def handler(job):
    global pipeline, upload_to_r2
    
    try:
        if pipeline is None:
            print("========== INITIALIZING MODEL PIPELINE ==========")
            from utils import upload_to_r2 as r2_uploader
            from fashn_vton import TryOnPipeline
            
            upload_to_r2 = r2_uploader
            pipeline = TryOnPipeline(weights_dir="./weights")
            print("Model pipeline loaded successfully!")

        job_input = job["input"]
        person_url = job_input["person_url"]
        garment_url = job_input["garment_url"]
        render_category = job_input["category"] # "top", "bottom", ou "auto"

        # Adapta o formato de texto do Render para o formato exigido pelo seu pipeline.py
        category_mapping = {
            "top": "tops",
            "bottom": "bottoms",
            "one-piece": "one-pieces",
            "auto": "tops"
        }
        final_category = category_mapping.get(render_category, "tops")

        print(f"Executing Job ID: {job.get('id')} | Category: {final_category}")

        person = load_image(person_url)
        garment = load_image(garment_url)

        # Chamada exata baseada nas definições do seu pipeline.py (__call__)
        result = pipeline(
            person_image=person,
            garment_image=garment,
            category=final_category
        )

        print("Pipeline finished executing. Extracting output image object...")
        output_path = "/tmp/result.png"

        # Garante a extração correta da imagem de dentro da estrutura PipelineOutput
        if hasattr(result, "images") and isinstance(result.images, list):
            final_image = result.images[0]
        elif isinstance(result, list):
            final_image = result[0]
        else:
            final_image = result

        final_image.save(output_path)
        print("Image saved. Executing cloud upload...")

        filename = upload_to_r2(
            file_path=output_path,
            bucket_name=os.environ["R2_BUCKET"],
            endpoint_url=os.environ["R2_ENDPOINT"],
            access_key_id=os.environ["R2_ACCESS_KEY"],
            secret_access_key=os.environ["R2_SECRET_KEY"],
        )

        public_url = f"{os.environ['R2_PUBLIC_URL']}/{filename}"
        print(f"Upload completed successfully. Link: {public_url}")

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
