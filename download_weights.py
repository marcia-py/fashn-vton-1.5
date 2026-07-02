import os
import subprocess

if not os.path.exists("./weights/model.safetensors"):
    subprocess.run(
        [
            "python",
            "scripts/download_weights.py",
            "--weights-dir",
            "./weights",
        ],
        check=True,
    )

print("Weights ready.")