import requests
import runpod

print("STEP 1")


def handler(job):
    print("STEP 2")
    return {"success": True}


print("STEP 3")

runpod.serverless.start({"handler": handler})
