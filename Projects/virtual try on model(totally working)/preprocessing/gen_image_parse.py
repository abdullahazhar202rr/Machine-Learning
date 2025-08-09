import os
import subprocess

image_dir = "datasets/test/image"
save_dir = "datasets/test/image-parse"

os.makedirs(save_dir, exist_ok=True)

for filename in os.listdir(image_dir):
    if filename.endswith(".jpg") or filename.endswith(".png"):
        input_path = os.path.join(image_dir, filename)
        
        # ✅ Force output to .png
        base_name = os.path.splitext(filename)[0]
        output_path = os.path.join(save_dir, base_name + ".png")

        cmd = [
            "python",
            "preprocessing/Single-Human-Parsing-LIP/inference.py",
            input_path,
            "--save_path", output_path,
            "--models-path", "preprocessing/Single-Human-Parsing-LIP/checkpoints",
            "--backend", "resnet50"
        ]
        subprocess.run(cmd)

print("✅ Image parsing completed. Saved as PNG.")
