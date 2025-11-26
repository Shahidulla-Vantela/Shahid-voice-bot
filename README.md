# Shahid - AI Voice Assistant

An interactive voice chatbot that responds to questions about me (Shahid) - an AI/ML Engineer. Built with real-time speech-to-text, LLM responses, and text-to-speech.

## 🎯 Features

- 🎙️ **One-click voice interaction** - Click to speak, click to send
- 🗣️ **Natural voice responses** - Real-time TTS with ElevenLabs
- 💬 **Three response styles** - Concise, Conversational, or Detailed
- 🔄 **New Chat** - Reset conversation anytime
- 👋 **Auto-greeting** - Introduces myself when you start

## 🛠️ Tech Stack

- **Frontend**: HTML, CSS, JavaScript (single file)
- **Backend**: FastAPI (Python)
- **Speech-to-Text**: Deepgram Nova-2
- **LLM**: Groq (Llama 3.3 70B) - Free tier
- **Text-to-Speech**: ElevenLabs - Streaming

## 🚀 Quick Start (Local)

### 1. Clone & Setup
```bash
git clone <your-repo-url>
cd voice-assistant
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Get API Keys (All Free Tiers)
- **Deepgram**: https://console.deepgram.com/ ($200 free credit)
- **Groq**: https://console.groq.com/ (Free tier)
- **ElevenLabs**: https://elevenlabs.io/ (10k chars/month free)

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 4. Run
```bash
uvicorn main:app --reload
```

### 5. Open
Visit http://localhost:8000

## 🌐 Deploy to Render (Free)

1. Push code to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your GitHub repo
4. Add environment variables:
   - `DEEPGRAM_API_KEY`
   - `GROQ_API_KEY`
   - `ELEVENLABS_API_KEY`
5. Deploy!

## 📁 Project Structure

```
├── main.py           # Backend (FastAPI + all services)
├── index.html        # Frontend (HTML + CSS + JS)
├── requirements.txt  # Python dependencies
├── .env              # API keys (don't commit!)
├── .env.example      # Template for API keys
├── knowledge_base/   # Resume/CV files (optional)
├── Procfile          # Heroku/Railway deployment
├── render.yaml       # Render.com deployment
└── README.md
```

## 💡 Sample Questions

- "What should I know about your life story?"
- "What's your #1 superpower?"
- "What are your top 3 growth areas?"
- "What misconceptions do people have about you?"
- "How do you push your boundaries?"

## 📝 License

MIT
