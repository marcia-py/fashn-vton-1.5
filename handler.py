import io
import os
import traceback

import requests
import runpod

from PIL import Image

from utils import upload_to_r2
from fashn_vton import TryOnPipeline

print("========== STARTING ==========")

try:
    print("Loading FASHN model...")

    pipeline = TryOnPipeline(
        weights_dir="./weights"
    )

    print("Model loaded!")

except Exception:
    print("FAILED TO INITIALIZE MODEL")
    traceback.print_exc()
    raise


def load_image(url):
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return Image.open(io.BytesIO(response.content)).convert("RGB")


def handler(job):
    try:
        job_input = job["input"]

        person_url = job_input["person_url"]
        garment_url = job_input["garment_url"]
        category = job_input["category"]

        print(f"Person URL: {person_url}")
        print(f"Garment URL: {garment_url}")
        print(f"Category: {category}")

        person = load_image(person_url)
        garment = load_image(garment_url)

        result = pipeline(
            person_image=person,
            garment_image=garment,
            category=category,
        )

        output_path = "/tmp/result.png"
        result.images[0].save(output_path)

        filename = upload_to_r2(
            file_path=output_path,
            bucket_name=os.environ["R2_BUCKET"],
            endpoint_url=os.environ["R2_ENDPOINT"],
            access_key_id=os.environ["R2_ACCESS_KEY"],
            secret_access_key=os.environ["R2_SECRET_KEY"],
        )

        return {
            "success": True,
            "image_url": f"{os.environ['R2_PUBLIC_URL']}/{filename}"
        }

    except Exception:
        traceback.print_exc()
        raise

runpod.serverless.start({"handler": handler})
