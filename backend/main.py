"""GirishOS FastAPI Backend Server."""
import os
import sys
import json
import asyncio
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config import PipelineConfig
from pipeline import PipelineOrchestrator
from validators import InputValidator
from models import FallbackResult

app = FastAPI(title="GirishOS Backend", version="1.0.0")
config = PipelineConfig(groq_api_key=os.environ.get("GROQ_API_KEY", ""))

# CORS - allow all origins for demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize pipeline
pipeline = PipelineOrchestrator(config)
validator = InputValidator(rate_limit_seconds=5.0)


@app.on_event("startup")
async def startup():
    """Warm up pipeline on server start."""
    print("🔥 Warming up pipeline...")
    await pipeline.warm_up()
    print("✅ Pipeline ready!")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    status = await pipeline.health_check()
    return {
        "status": "ok",
        "message": "GirishOS backend is running",
        "components": status,
    }


@app.get("/video/{path:path}")
async def serve_video(path: str):
    """Serve generated video files."""
    video_path = os.path.join(pipeline._video_serve_dir, path)
    if os.path.exists(video_path):
        return FileResponse(video_path, media_type="video/mp4")
    return {"error": "Video not found"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time communication."""
    await websocket.accept()
    client_id = str(id(websocket))
    print(f"🔌 Client connected: {client_id}")

    async def notify_stage(question_id: str, stage: str):
        """Send pipeline stage update to client."""
        try:
            await websocket.send_json({
                "type": "processing",
                "questionId": question_id,
                "stage": stage,
            })
        except Exception:
            pass

    pipeline.set_notify_callback(notify_stage)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "heartbeat":
                await websocket.send_json({"type": "heartbeat_ack"})

            elif msg_type == "question":
                question_id = data.get("id", "unknown")
                question_text = data.get("text", "")

                print(f"\n❓ Question [{question_id[:8]}]: {question_text[:80]}")

                # Validate
                error = validator.validate_question(question_text, question_id, client_id)
                if error:
                    await websocket.send_json({
                        "type": "error",
                        "questionId": question_id,
                        "message": error,
                        "fallback": False,
                    })
                    continue

                # Sanitize
                question_text = validator.sanitize(question_text)
                validator.mark_processed(question_id, client_id)

                # Process through pipeline
                result = await pipeline.process_question_safe(question_text, question_id)

                if isinstance(result, FallbackResult):
                    await websocket.send_json({
                        "type": "fallback_response",
                        "questionId": question_id,
                        "text": result.text,
                        "level": result.level.value,
                        "showTextOverlay": result.show_text_overlay,
                    })
                else:
                    # Convert local path to URL
                    video_rel_path = os.path.relpath(result.video_url, pipeline._video_serve_dir)
                    # URL-encode the path to handle special chars like ##
                    from urllib.parse import quote
                    video_url_path = "/video/" + quote(video_rel_path, safe="/")

                    await websocket.send_json({
                        "type": "video_ready",
                        "questionId": question_id,
                        "url": video_url_path,
                        "duration": result.duration,
                        "text": result.text_response,
                        "generationTime": result.generation_time,
                    })
                    print(f"  ✅ Response sent ({result.generation_time:.1f}s total)")

    except WebSocketDisconnect:
        print(f"🔌 Client disconnected: {client_id}")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.host, port=config.port)
