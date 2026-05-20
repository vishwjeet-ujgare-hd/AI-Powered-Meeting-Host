# 🤖 GirishOS - AI-Powered Interactive Meeting Host

GirishOS is an AI-powered virtual meeting host that transforms "AI pe Charcha" meetings into fun, interactive, engaging AI experiences.

## 🎯 What It Does

- **AI Avatar** presents meeting agendas with lip-synced video
- **Live Q&A** — audience asks questions, avatar responds in real-time (3-5 seconds)
- **Voice + Expressions** — realistic talking-head animation
- **Zero Cost** — entirely free-tier stack

## 🏗️ Architecture

```
Frontend (Next.js on Vercel)  ←→  WebSocket  ←→  Backend (FastAPI on Google Colab)
                                                      ↓
                                              Groq LLM (text response)
                                                      ↓
                                              Edge TTS (voice generation)
                                                      ↓
                                              SadTalker + GPU (avatar video)
```

## 🛠️ Tech Stack (All Free)

| Component | Technology | Cost |
|-----------|-----------|------|
| LLM | Groq API (llama-3.3-70b) | Free tier |
| Voice | Edge TTS (Microsoft) | Free, no API key |
| Avatar | SadTalker on Google Colab | Free GPU |
| Frontend | Next.js + Tailwind CSS | Vercel free tier |
| Backend | FastAPI + Python | Google Colab |
| Tunnel | ngrok | Free tier |

## 🚀 Quick Start

### Prerequisites

1. A front-facing photo (neutral expression, 512x512+)
2. Free [Groq API key](https://console.groq.com)
3. Free [ngrok auth token](https://dashboard.ngrok.com/signup)
4. Google account (for Colab)

### Setup

1. **Start Backend (Google Colab)**
   - Open `girishos_backend.ipynb` in [Google Colab](https://colab.research.google.com)
   - Select Runtime → Change runtime type → T4 GPU
   - Run all cells
   - Copy the WebSocket URL printed in the output

2. **Start Frontend (Local)**
   - `cd frontend && npm install`
   - Create `.env.local` with: `NEXT_PUBLIC_BACKEND_URL=wss://your-ngrok-url`
   - `npm run dev`
   - Open `http://localhost:3000`

## 📁 Project Structure

```
├── assets/
│   └── photos/          ← Place your avatar photo here
├── backend/
│   ├── config.py        ← Pipeline configuration
│   ├── models.py        ← Data models
│   ├── main.py          ← FastAPI server
│   ├── pipeline.py      ← Pipeline orchestrator
│   ├── groq_client.py   ← Groq LLM client
│   ├── tts_engine.py    ← Edge TTS engine
│   ├── sadtalker_engine.py ← SadTalker wrapper
│   └── cache.py         ← Response cache
├── frontend/            ← Next.js app (coming soon)
├── girishos_backend.ipynb ← Colab notebook
└── README.md
```

## ⚠️ Security

- API keys are stored in Google Colab Secrets (never in code)
- `.gitignore` prevents accidental key/photo commits
- Frontend `.env.local` is gitignored

## 📝 License

Internal project — AI pe Charcha initiative.
