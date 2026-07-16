import runpod
from fashn_vton import TryOnPipeline

print("STEP 1")

print("STEP 2")
pipeline = TryOnPipeline(
    weights_dir="./weights"
)

print("STEP 3")


def handler(job):
    return {"success": True}

runpod.serverless.start({"handler": handler})
