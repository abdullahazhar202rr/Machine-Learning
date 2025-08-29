## How to setup

1. Install [llama.cpp](https://github.com/ggml-org/llama.cpp)
2. Run `llama-server -hf ggml-org/SmolVLM-500M-Instruct-GGUF`  
   Note: you may need to add `-ngl 99` to enable GPU (if you are using NVidia/AMD/Intel GPU)  
   Note (2): You can also try other models [here](https://github.com/ggml-org/llama.cpp/blob/master/docs/multimodal.md)
   
   #### all things in steps below after doing all those steps come here again for further
3. Open `index.html`
4. Optionally change the instruction (for example, make it returns JSON)
5. Click on "Start" and enjoy


Absolutely! Let me break it down step by step like a proper classroom session. 🏫

We’ll focus on **how to start and use `llama.cpp`** on your machine.

---

## **Step 1: Clone the Repo**

If you haven’t already:

```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
```

---

## **Step 2: Build the Code**

`llama.cpp` is in C++, so we need to compile it. There are **two main options**:

### **Option A: CPU-only (simplest)**

```bash
mkdir build
cd build
cmake ..
make -j$(nproc)
```

* `-j$(nproc)` uses all CPU cores for faster compilation.
* After this, you’ll have executables like `main` and `llama-server` in `build/bin/`.

### **Option B: GPU (faster, optional)**

1. Make sure CUDA is installed.
2. Use:

```bash
cmake .. -DGGML_CUDA=ON
make -j$(nproc)
```

* This enables GPU acceleration for NVIDIA GPUs.
* On AMD/Intel GPU, you can use other backends like Metal or ROCm (requires extra setup).

---

## **Step 3: Download a Model**

`llama.cpp` doesn’t include models. You need to get one from **Hugging Face**. Example:

```bash
./bin/llama-download -hf ggml-org/SmolVLM-500M-Instruct-GGUF
```

* This downloads and caches the model in `~/.cache/llama.cpp/`.
* You can also use bigger models like **LLaMA 7B**, but they need more RAM.

---

## **Step 4: Run the Model (Command Line)**

### **Option A: Simple text generation**

```bash
./bin/main -m ~/.cache/llama.cpp/SmolVLM-500M-Instruct-GGUF/SmolVLM-500M-Instruct-Q8_0.gguf
```

* `-m` points to the model file.
* You’ll get a prompt like:

```
> 
```

* Type a question, hit Enter, and the AI responds.

---

### **Option B: Run the web server**

```bash
./bin/llama-server -hf ggml-org/SmolVLM-500M-Instruct-GGUF
```

* Starts a server at `http://127.0.0.1:8080`.
* Open `index.html` in a browser to interact with the model visually.

> Tip: Use `-ngl 99` if you have GPU support and want GPU layers enabled.

---

## **Step 5: Optional Features**

* **Quantize a model** (make it smaller and faster for CPU):

```bash
./bin/quantize model.gguf model-q.gguf
```

* **Change context length**:

```bash
./bin/main -m model.gguf -c 4096
```

* **Load with GPU layers**:

```bash
./bin/main -m model.gguf -ngl 99
```

---