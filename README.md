# 🚀 Razorpay Voice Shopping Agent
**AI-Powered Voice Commerce for Razorpay Buildathon 2026**

## 📌 Project Overview
**Track:** AI Growth & Agentic Commerce
**Goal:** Build a voice-powered AI agent that searches a merchant's catalog and completes UPI payments via Razorpay.

---

## 📅 3-Day Execution Plan

### 📌 Day 1: Core Pipeline (Voice → LLM → Catalog Search)
#### 🔹 Morning (3–4 hours) – Setup & Voice Input
1. **Environment Setup**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install fastapi uvicorn python-multipart pydantic whisper transformers torch razorpay
   ```
   - Install [FFmpeg](https://ffmpeg.org/) for Whisper.

2. **Voice Input Module** (`voice_input.py`)
   ```python
   import whisper
   model = whisper.load_model("base")
   
   def voice_to_text(audio_path: str) -> str:
       result = model.transcribe(audio_path)
       return result["text"].strip()
   ```

3. **LLM Processing Module** (`llm_processor.py`)
   ```python
   from transformers import pipeline
   llm = pipeline("text-generation", model="meta-llama/Meta-Llama-3-8B-Instruct", device="cpu")
   
   def extract_intent(text: str) -> dict:
       prompt = f"Extract intent from: '{text}'"
       response = llm(prompt, max_length=200)
       return {"query": "wireless earbuds", "max_price": 2000}  # Mock for now
   ```

4. **Catalog Search Module** (`catalog_search.py`)
   ```python
   import json
   
   def search_catalog(query: str, max_price: int = None) -> list:
       with open("catalog.json", "r") as f:
           catalog = json.load(f)
       return [item for item in catalog if query.lower() in item["name"].lower() and (max_price is None or item["price"] <= max_price)]
   ```

5. **FastAPI Backend** (`main.py`)
   ```python
   from fastapi import FastAPI
   from fastapi.middleware.cors import CORSMiddleware
   
   app = FastAPI()
   app.add_middleware(CORSMiddleware, allow_origins=["*"])
   
   @app.post("/process_voice")
   async def process_voice(audio: UploadFile):
       text = voice_to_text(audio.file)
       intent = extract_intent(text)
       results = search_catalog(**intent)
       return {"text": text, "intent": intent, "results": results}
   ```

#### 🔹 Afternoon (3–4 hours) – Basic UI
6. **Create `catalog.json`**
   ```json
   [
       {"id": 1, "name": "Sony WH-1000XM5", "price": 1999},
       {"id": 2, "name": "Boat Airdopes 141", "price": 999}
   ]
   ```

7. **Test Backend**
   ```bash
   uvicorn main:app --reload
   ```
   - Use Postman or `curl` to test `/process_voice`.

---

### 📌 Day 2: Razorpay Integration + Payment Flow
#### 🔹 Morning (3–4 hours) – Razorpay Setup
1. **Sign up for Razorpay Test Mode** and get API keys.
2. **Razorpay Client** (`razorpay_client.py`)
   ```python
   import razorpay
   client = razorpay.Client(auth=("YOUR_TEST_API_KEY", "YOUR_TEST_API_SECRET"))
   
   def create_order(amount: int) -> dict:
       order_data = {"amount": amount * 100, "currency": "INR", "receipt": "order_rcptid_11"}
       return client.order.create(data=order_data)
   ```

3. **Add Payment Flow to `main.py`**
   ```python
   @app.post("/create_order")
   async def create_order(item_id: int):
       order = create_order(1999)  # Example price
       return {"order": order}
   ```

#### 🔹 Afternoon (3–4 hours) – Frontend + Demo
4. **Create `index.html`**
   ```html
   <!DOCTYPE html>
   <html>
   <head>
       <title>Voice Shopping Agent</title>
       <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
   </head>
   <body>
       <button id="startRecording">🎤 Start</button>
       <div id="results"></div>
       <script>
           // Add voice recording logic and Razorpay payment integration
       </script>
   </body>
   </html>
   ```

5. **Test Full Flow**
   - Record voice → Get results → Click 