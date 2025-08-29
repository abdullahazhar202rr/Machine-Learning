import torch
from ultralytics import YOLO
import matplotlib.pyplot as plt

# Load both YOLO models
model1 = YOLO('best.pt')
model2 = YOLO('best2.pt')

# Test image (you can replace this with your own image path)
image_path = 'pic2.jpg'

# Run inference on both models
results1 = model1(image_path)
results2 = model2(image_path)

# Show the results (detect objects) from both models
def show_results(results, model_name):
    # Extract the first item in the list, which is the Results object
    result = results[0]
    
    # Show the image with predicted bounding boxes
    result.show()  # This will open the image with detected boxes
    print(f"{model_name} Predictions:")
    print(result.to_df())  # Get prediction details in dataframe format using to_df()

# Show results for both models
show_results(results1, "Model 1")
show_results(results2, "Model 2")

# Compare confidence scores
def compare_confidence(results1, results2):
    # Get the highest confidence score for each model
    conf1 = results1[0].boxes.conf.max() if len(results1[0].boxes) > 0 else 0
    conf2 = results2[0].boxes.conf.max() if len(results2[0].boxes) > 0 else 0
    print(f"Model 1 highest confidence: {conf1:.4f}")
    print(f"Model 2 highest confidence: {conf2:.4f}")

    # Determine the better model based on highest confidence
    if conf1 > conf2:
        print("Model 1 is better based on confidence!")
    elif conf2 > conf1:
        print("Model 2 is better based on confidence!")
    else:
        print("Both models have equal confidence.")

# Compare the models' confidence
compare_confidence(results1, results2)
