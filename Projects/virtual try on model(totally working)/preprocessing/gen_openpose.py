import os
import subprocess

# Define absolute paths
openpose_dir = os.path.abspath("preprocessing/openpose")
openpose_bin = os.path.join(openpose_dir, "bin", "OpenPoseDemo.exe")
model_folder = os.path.join(openpose_dir, "models")

image_dir = os.path.abspath("datasets/test/image")
json_output = os.path.abspath("datasets/test/openpose-json")
img_output = os.path.abspath("datasets/test/openpose-img")

# Create output folders if they don't exist
os.makedirs(json_output, exist_ok=True)
os.makedirs(img_output, exist_ok=True)

# OpenPose command
cmd = [
    openpose_bin,
    "--image_dir", image_dir,
    "--write_json", json_output,
    "--write_images", img_output,
    "--display", "0",
    "--render_pose", "1",               # Body pose only
    "--disable_blending",              # ✅ Only skeleton on black bg
    "--render_threshold", "0.1",
    "--model_folder", model_folder,
    "--net_resolution", "-1x368"       # Optional: better pose resolution
]

print("▶ Running OpenPose...")
result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=openpose_dir)

# Check for errors
if result.returncode != 0:
    print("❌ OpenPose failed.")
    print("STDERR:\n", result.stderr)
    print("STDOUT:\n", result.stdout)
else:
    print("✅ OpenPose skeletons generated with black background.")