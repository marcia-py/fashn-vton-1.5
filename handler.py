import runpod

print("STEP 1 - handler.py loaded")


def handler(job):
    print("STEP 2 - handler called")

    return {
        "success": True
    }


print("STEP 3 - starting RunPod server")

runpod.serverless.start({"handler": handler})
