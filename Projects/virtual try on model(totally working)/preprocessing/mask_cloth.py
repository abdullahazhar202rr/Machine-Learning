import os
import numpy as np
from PIL import Image, ImageOps
from rembg import remove

# === Paths ===
base_dir = os.path.abspath(os.path.dirname(__file__))
cloth_dir = os.path.join(base_dir, "../datasets/test/cloth")
mask_dir = os.path.join(base_dir, "../datasets/test/cloth-mask")
os.makedirs(mask_dir, exist_ok=True)

# === Canvas settings ===
CANVAS_WIDTH, CANVAS_HEIGHT = 768, 1024

# === Smart center & crop helper ===
def center_cloth_on_canvas(image_rgba, canvas_size=(768, 1024)):
    # Extract alpha and crop empty space
    alpha = image_rgba.split()[3]
    bbox = alpha.getbbox()
    if bbox:
        image_rgba = image_rgba.crop(bbox)
        alpha = image_rgba.split()[3]

    # Resize while maintaining aspect ratio
    ratio = min(canvas_size[0] / image_rgba.width, canvas_size[1] / image_rgba.height)
    new_size = (int(image_rgba.width * ratio), int(image_rgba.height * ratio))
    image_resized = image_rgba.resize(new_size, Image.LANCZOS)
    alpha_resized = image_resized.split()[3]

    # Paste centered on canvas
    canvas = Image.new("RGB", canvas_size, (255, 255, 255))
    canvas_mask = Image.new("L", canvas_size, 0)
    paste_x = (canvas_size[0] - new_size[0]) // 2
    paste_y = (canvas_size[1] - new_size[1]) // 2

    rgb = Image.new("RGB", image_resized.size, (255, 255, 255))
    rgb.paste(image_resized, mask=alpha_resized)
    canvas.paste(rgb, (paste_x, paste_y))
    canvas_mask.paste(alpha_resized.point(lambda x: 255 if x > 30 else 0), (paste_x, paste_y))
    return canvas, canvas_mask

# === Process each cloth image ===
for fname in sorted(os.listdir(cloth_dir)):
    if not fname.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
        continue

    in_path = os.path.join(cloth_dir, fname)
    base_name, _ = os.path.splitext(fname)

    print(f"🧵 Processing: {fname}")
    img = Image.open(in_path).convert("RGBA")

    # Step 1: Background Removal
    removed = remove(np.array(img))
    cloth_rgba = Image.fromarray(removed).convert("RGBA")

    # Step 2: Center cloth on 768x1024 white canvas
    canvas_img, canvas_mask = center_cloth_on_canvas(cloth_rgba, canvas_size=(CANVAS_WIDTH, CANVAS_HEIGHT))

    # Step 3: Save cleaned cloth image (.jpg)
    save_img_path = os.path.join(cloth_dir, base_name + ".jpg")
    canvas_img.save(save_img_path, "JPEG")
    print(f"✅ Cleaned cloth saved: {save_img_path}")

    # Step 4: Save binary mask (.jpg or .png)
    save_mask_path = os.path.join(mask_dir, base_name + ".jpg")
    canvas_mask.save(save_mask_path)
    print(f"🎭 Mask saved: {save_mask_path}")

print("🎉 All cloths processed successfully with rembg + centered fit!")
