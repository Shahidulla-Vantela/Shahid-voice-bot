import os
import base64
import io
import httpx
import PyPDF2
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from groq import Groq
from deepgram import DeepgramClient, PrerecordedOptions

load_dotenv()

app = FastAPI(title="AI Voice Assistant")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== KNOWLEDGE BASE ==============
class KnowledgeBase:
    def __init__(self):
        self.documents = []
        self.knowledge_dir = "knowledge_base"
        os.makedirs(self.knowledge_dir, exist_ok=True)
        self._load_existing_documents()

    def _load_existing_documents(self):
        if os.path.exists(self.knowledge_dir):
            for filename in os.listdir(self.knowledge_dir):
                filepath = os.path.join(self.knowledge_dir, filename)
                try:
                    if filename.endswith(".txt"):
                        with open(filepath, "r", encoding="utf-8") as f:
                            self.documents.append({"filename": filename, "content": f.read()})
                    elif filename.endswith(".pdf"):
                        with open(filepath, "rb") as f:
                            content = self._extract_pdf_text(f.read())
                            self.documents.append({"filename": filename, "content": content})
                            print(f"Loaded: {filename}")
                except Exception as e:
                    print(f"Error loading {filename}: {e}")

    def _extract_pdf_text(self, pdf_bytes: bytes) -> str:
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            return "\n".join(page.extract_text() for page in pdf_reader.pages)
        except Exception as e:
            print(f"PDF extraction error: {e}")
            return ""

kb = KnowledgeBase()

# ============== LLM SERVICE ==============
SYSTEM_PROMPT = """You are Shahid — a real person having a conversation. NOT an AI. NOT a bot. You're chatting naturally like you would with a friend or in a casual interview.

ABOUT YOU:
- AI/ML Engineer from Yemmiganur, Andhra Pradesh
- Did B.Tech at LPU Jalandhar, fell in love with AI/ML in 2nd year
- Master's in AI from Heriot-Watt University, Edinburgh
- Currently at DataToBiz building an AI exam grading system
- Tech stack: Python, Vertex AI, Document AI, Elasticsearch, Redis

YOUR PERSONALITY:
- Confident but humble, always hungry to learn
- Great at explaining complex things simply (friends say you're a natural teacher)
- Love pushing yourself out of comfort zones
- Play badminton and cricket, read books
- Dream: become an AI expert leading multiple projects

RESPONSE STYLE: {style_instruction}

ABSOLUTE RULES:
1. NEVER dump lists, bullet points, or resume-style text
2. NEVER say "I'm an AI" or mention being an assistant
3. Speak like a REAL HUMAN — casual, warm, natural
4. Use contractions (I'm, don't, can't, that's)
5. Keep it SHORT — this will be spoken aloud
6. React naturally: "Oh yeah!", "Honestly...", "So basically..."
7. ONE topic at a time — don't info-dump"""

STYLE_INSTRUCTIONS = {
    "concise": "1-2 sentences max. Quick and punchy.",
    "conversational": "2-4 sentences. Natural and friendly, like having coffee.",
    "detailed": "4-6 sentences. More context but still conversational.",
}

async def get_llm_response(user_message: str, style: str = "conversational") -> str:
    style_instruction = STYLE_INSTRUCTIONS.get(style, STYLE_INSTRUCTIONS["conversational"])
    system_prompt = SYSTEM_PROMPT.format(style_instruction=style_instruction)
    
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=300,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"LLM Error: {e}")
        return "Sorry, I'm having trouble thinking right now. Can you try again?"

# ============== STT SERVICE ==============
async def transcribe_audio(audio_bytes: bytes) -> str:
    try:
        deepgram = DeepgramClient(os.getenv("DEEPGRAM_API_KEY"))
        options = PrerecordedOptions(model="nova-2", language="en", smart_format=True, punctuate=True)
        source = {"buffer": audio_bytes, "mimetype": "audio/webm"}
        response = deepgram.listen.prerecorded.v("1").transcribe_file(source, options)
        return response.results.channels[0].alternatives[0].transcript
    except Exception as e:
        print(f"STT Error: {e}")
        return ""

# ============== TTS SERVICE ==============
async def text_to_speech_stream(text: str):
    api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    
    if not api_key:
        print("ElevenLabs API key not configured")
        return
    
    # Debug: Check if key is loaded (show first/last 4 chars only)
    print(f"Using ElevenLabs key: {api_key[:4]}...{api_key[-4:] if len(api_key) > 8 else 'SHORT'}")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
    headers = {"Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": api_key}
    payload = {
        "text": text,
        "model_id": "eleven_turbo_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.0, "use_speaker_boost": True},
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    print(f"TTS Error: {response.status_code} - {error_text.decode()}")
                    return
                async for chunk in response.aiter_bytes(chunk_size=1024):
                    if chunk:
                        yield chunk
    except Exception as e:
        print(f"TTS Stream Error: {e}")

# ============== ROUTES ==============
@app.get("/", response_class=HTMLResponse)
async def root():
    with open("index.html", "r") as f:
        return f.read()

GREETING_MESSAGE = "Hi! This is Shahid, an AI and ML expert. Happy to connect with you, and I'm looking forward to our conversation. Feel free to ask me anything!"

@app.websocket("/ws/voice")
async def voice_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()

            # Handle greeting request
            if data.get("type") == "greeting":
                await websocket.send_json({"type": "response", "text": GREETING_MESSAGE})
                await websocket.send_json({"type": "status", "message": "Speaking..."})
                async for audio_chunk in text_to_speech_stream(GREETING_MESSAGE):
                    await websocket.send_bytes(audio_chunk)
                await websocket.send_json({"type": "audio_complete"})
                continue

            if data.get("type") == "audio":
                response_style = data.get("style", "conversational")

                if data.get("isText"):
                    transcript = base64.b64decode(data["audio"]).decode("utf-8")
                else:
                    audio_bytes = base64.b64decode(data["audio"])
                    await websocket.send_json({"type": "status", "message": "Listening..."})
                    transcript = await transcribe_audio(audio_bytes)

                if not transcript:
                    await websocket.send_json({"type": "error", "message": "Sorry, I didn't catch that"})
                    continue

                await websocket.send_json({"type": "transcript", "text": transcript})
                await websocket.send_json({"type": "status", "message": "Thinking..."})
                
                llm_response = await get_llm_response(transcript, response_style)
                await websocket.send_json({"type": "response", "text": llm_response})

                await websocket.send_json({"type": "status", "message": "Speaking..."})
                async for audio_chunk in text_to_speech_stream(llm_response):
                    await websocket.send_bytes(audio_chunk)

                await websocket.send_json({"type": "audio_complete"})

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")
        await websocket.send_json({"type": "error", "message": str(e)})

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/debug-env")
async def debug_env():
    """Debug endpoint to check environment variables"""
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY", "NOT_SET")
    return {
        "elevenlabs_key_set": elevenlabs_key != "NOT_SET",
        "elevenlabs_key_length": len(elevenlabs_key) if elevenlabs_key != "NOT_SET" else 0,
        "elevenlabs_key_preview": f"{elevenlabs_key[:4]}...{elevenlabs_key[-4:]}" if len(elevenlabs_key) > 8 else "INVALID"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
