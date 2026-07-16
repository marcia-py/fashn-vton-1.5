import requests
import runpod
from PIL import Image
from utils import upload_to_r2

print("STEP 1")


def handler(job):
    return {"success": True}


runpod.serverless.start({"handler": handler})
