from flask import Flask, render_template, request, send_from_directory, url_for
import os
import subprocess
import shutil

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "datasets", "test", "image")
CLOTH_DIR = os.path.join(BASE_DIR, "datasets", "test", "cloth")
PAIRS_TXT = os.path.join(BASE_DIR, "datasets", "test_pairs.txt")
RESULTS_DIR = os.path.join(BASE_DIR, "results", "viton_hd")

os.makedirs(RESULTS_DIR, exist_ok=True)

@app.route('/model_images/<filename>')
def model_images(filename):
    return send_from_directory(IMAGE_DIR, filename)

@app.route('/cloth_uploaded')
def cloth_uploaded():
    return send_from_directory(CLOTH_DIR, "cloth.jpg")

@app.route('/result_image')
def result_image():
    return send_from_directory(RESULTS_DIR, "final_result.jpg")

@app.route("/", methods=["GET", "POST"])
def index():
    model_files = sorted([f for f in os.listdir(IMAGE_DIR) if f.endswith(".jpg")])
    cloth_preview = None
    result_url = None

    if request.method == "POST":
        selected_model = request.form.get("model")
        cloth_file = request.files["cloth"]

        if selected_model and cloth_file:
            cloth_path = os.path.join(CLOTH_DIR, "cloth.jpg")
            cloth_file.save(cloth_path)
            cloth_preview = url_for("cloth_uploaded")

            with open(PAIRS_TXT, "w") as f:
                f.write(f"{selected_model} cloth.jpg\n")

            try:
                subprocess.run(
                    ["python", "test.py", "--name", "viton_hd"],
                    check=True,
                    cwd=BASE_DIR
                )

                # === Find actual output file ===
                actual_output = None
                for root, dirs, files in os.walk(RESULTS_DIR):
                    for file in files:
                        if file.endswith(".jpg") or file.endswith(".png"):
                            actual_output = os.path.join(root, file)

                if actual_output:
                    final_output = os.path.join(RESULTS_DIR, "final_result.jpg")
                    shutil.copy(actual_output, final_output)
                    result_url = url_for("result_image")

            except subprocess.CalledProcessError as e:
                print(f"Error running test.py: {e}")

    return render_template(
        "index.html",
        model_files=model_files,
        cloth_preview=cloth_preview,
        result_url=result_url
    )

if __name__ == "__main__":
    app.run(debug=True)
