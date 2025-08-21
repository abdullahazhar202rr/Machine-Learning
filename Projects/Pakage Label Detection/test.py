from ultralytics import YOLO

# ✅ Load your test image
img = "20250603_150828.jpg"  # replace with your test image path

# ✅ Load your 3 models
# model1 = YOLO("best1.pt")
model2 = YOLO("best.pt")
# model3 = YOLO("best3.pt")

# ✅ Predict with each one
# result1 = model1.predict(img, conf=0.1, save=True)
result2 = model2.predict(img, conf=0.05,iou=0.5, save=True)
# result3 = model3.predict(img, conf=0.1, save=True)

print("✅ Predictions done! Check the 'runs/detect/predict*' folders.")
