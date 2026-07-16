import requests
import runpod
from PIL import Image

print("STEP 1")


def handler(job):
    return {"success": True}


runpod.serverless.start({"handler": handler})
