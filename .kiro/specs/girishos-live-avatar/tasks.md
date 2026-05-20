# Implementation Plan: GirishOS Live Avatar

## Overview

Build an AI-powered interactive meeting host with a realistic talking-head avatar. The backend runs on Google Colab (Python + FastAPI + SadTalker) and the frontend is a Next.js app deployed on Vercel. The pipeline processes audience questions through Groq LLM → Edge TTS → SadTalker to produce lip-synced video responses in 3-5 seconds.

Implementation starts with the backend pipeline (core value), then frontend, then integration. Pre-demo preparation tasks ensure fallback clips are ready before any live demo.

## Tasks

- [-] 1. Backend: Project structure and core pipeline setup on Colab
  - [x] 1.1 Create the Colab notebook skeleton with dependency installation cells
    - Create a Jupyter notebook (`girishos_backend.ipynb`) with cells for: pip installs (fastapi, uvicorn, edge-tts, groq, pyngrok, nest-asyncio, websockets), SadTalker clone + setup, model download
    - Create a `backend/` directory with Python modules: `main.py`, `pipeline.py`, `groq_client.py`, `tts_engine.py`, `sadtalker_engine.py`, `config.py`, `models.py`
    - Define `PipelineConfig` dataclass in `config.py` with all settings from design (Groq model, TTS voice, resolution, timeouts)
    - _Requirements: 2.1, 6.1_

  - [ ] 1.2 Implement input validation and data models
    - Create `models.py` with Pydantic models: `PipelineRequest`, `VideoResult`, `HealthStatus`, `FallbackResult`
    - Implement question text validation (1-500 chars, reject empty/whitespace-only)
    - Implement HTML sanitization (strip all HTML tags, preserve text content)
    - Implement duplicate question ID tracking and rejection
    - Implement rate limiting (1 question per 5 seconds per client)
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [ ]* 1.3 Write property tests for input validation
    - **Property 6: Input Validation Rejects Invalid Questions**
    - **Property 7: HTML Sanitization**
    - **Property 8: Duplicate Question ID Rejection**
    - **Property 9: Rate Limiting Enforcement**
    - **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**

- [ ] 2. Backend: Groq LLM Client
  - [ ] 2.1 Implement the Groq LLM client with GirishOS personality
    - Create `groq_client.py` with `GroqClient` class
    - Implement `generate_response()` with system prompt defining GirishOS personality (witty, AI-knowledgeable, engaging, Indian English)
    - Limit responses to 150 tokens max (2-3 sentences)
    - Implement conversation context tracking (last 5 Q&A pairs)
    - Implement fallback responses for API failures (pre-defined witty responses)
    - Handle rate limiting (HTTP 429) with retry after window
    - _Requirements: 2.1, 2.3_

  - [ ]* 2.2 Write property test for LLM response length constraint
    - **Property 11: LLM Response Length Constraint**
    - **Validates: Requirement 2.3**

- [ ] 3. Backend: Edge TTS Engine
  - [ ] 3.1 Implement the Edge TTS synthesis engine
    - Create `tts_engine.py` with `EdgeTTSEngine` class
    - Implement `synthesize()` using `edge-tts` library with voice `en-IN-PrabhatNeural` and rate `+10%`
    - Output WAV format at 24000 Hz sample rate
    - Enforce max audio duration of 12 seconds (truncate text if needed)
    - Implement retry logic (2 retries with 1-second delay)
    - _Requirements: 2.4, 3.1_

- [ ] 4. Backend: SadTalker Animation Engine
  - [ ] 4.1 Implement the SadTalker wrapper for video generation
    - Create `sadtalker_engine.py` with `SadTalkerEngine` class
    - Implement `generate_video()` that calls SadTalker inference with source image + audio
    - Configure 256x256 resolution, 25 FPS, expression scale 1.2, pose style 0
    - Output H.264 MP4 for browser compatibility
    - Implement `warm_up()` to pre-load models into GPU memory
    - Clean up temporary files after generation
    - _Requirements: 2.5, 3.1, 3.2, 3.3, 3.4_

- [ ] 5. Backend: Response caching
  - [ ] 5.1 Implement LRU response cache
    - Create cache module with max 20 entries
    - Implement cache key computation from question text (normalized)
    - Implement cache lookup returning cached `VideoResult` within 500ms
    - Implement LRU eviction when cache is full (evict oldest entry)
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [ ]* 5.2 Write property tests for caching
    - **Property 4: Cache Round-Trip**
    - **Property 5: Cache Size Bound with Eviction**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4**

- [ ] 6. Backend: Pipeline orchestrator and fallback logic
  - [ ] 6.1 Implement the full pipeline orchestrator
    - Create `pipeline.py` with `PipelineOrchestrator` class
    - Implement `process_question()` coordinating: cache check → Groq LLM → Edge TTS → SadTalker → serve video
    - Implement request queue (process one at a time to avoid GPU contention)
    - Report pipeline stage progress via WebSocket notifications (llm, tts, animation, encoding)
    - Enforce 8-second total pipeline timeout
    - _Requirements: 2.1, 2.2, 2.6_

  - [ ] 6.2 Implement fallback decision tree
    - Implement `handle_pipeline_failure()` with graceful degradation levels:
      - Level 2: Animation fails → audio-only + static avatar image
      - Level 3: TTS also fails → text-only + pre-generated filler video
      - Level 4: Total failure → pre-generated error recovery clip
    - Ensure user always receives a response within 8 seconds regardless of failures
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [ ]* 6.3 Write property test for fallback completeness
    - **Property 3: Fallback Completeness**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4**

- [ ] 7. Backend: FastAPI server, WebSocket endpoint, and Colab keep-alive
  - [ ] 7.1 Implement FastAPI WebSocket server
    - Create `main.py` with FastAPI app
    - Implement `/ws` WebSocket endpoint handling: question messages, heartbeat, cancel
    - Implement `/health` HTTP endpoint for health checks
    - Implement heartbeat acknowledgment (respond to client heartbeats)
    - Implement CORS configuration (allow Vercel frontend domain)
    - Serve generated video files via static file serving
    - _Requirements: 2.6, 4.1_

  - [ ] 7.2 Implement Colab keep-alive loop and tunnel management
    - Implement `colab_keep_alive_loop()` as background async task
    - Touch GPU every 60 seconds (`torch.zeros(1).cuda()`)
    - Verify tunnel health on each iteration, restart if dropped
    - Log new tunnel URL to Colab output when tunnel restarts
    - Monitor GPU memory usage, log warnings above 80% VRAM
    - Maintain session for at least 25 minutes
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ] 7.3 Create the complete Colab notebook with all cells
    - Cell 1: Install all pip dependencies
    - Cell 2: Clone SadTalker repo + install its requirements + download models
    - Cell 3: Upload Girish's photo (with instructions)
    - Cell 4: Import all backend modules and configure (Groq API key from Colab secrets)
    - Cell 5: Start ngrok tunnel + FastAPI server with keep-alive loop
    - Include markdown cells with setup instructions for the demo host
    - _Requirements: 6.1, 6.2, 6.3_

  - [ ]* 7.4 Write property test for WebSocket message completeness
    - **Property 13: WebSocket Message Completeness**
    - **Validates: Requirement 2.6**

- [ ] 8. Checkpoint - Backend pipeline complete
  - Ensure all backend tests pass, ask the user if questions arise.
  - Verify the pipeline can be run end-to-end in a Colab notebook (manual test)

- [ ] 9. Frontend: Project setup and video player
  - [ ] 9.1 Initialize Next.js project with dependencies
    - Create Next.js 14 app with TypeScript, Tailwind CSS, and framer-motion
    - Set up project structure: `components/`, `hooks/`, `lib/`, `types/`, `public/assets/`
    - Define TypeScript interfaces: `VideoClip`, `PlayerState`, `ClientMessage`, `ServerMessage`, `ConnectionStatus`, `DemoScript`, `DemoStage`, `FallbackClip`
    - Configure environment variable `NEXT_PUBLIC_BACKEND_URL` for WebSocket connection
    - _Requirements: 1.1, 8.1_

  - [ ] 9.2 Implement the Video Queue Player with double-buffering
    - Create `VideoQueuePlayer` class/hook managing clip playback
    - Implement FIFO queue with `enqueue()` and `playNext()` methods
    - Implement double-buffering: pre-load next clip in hidden video element while current plays
    - Implement cross-fade transitions (200ms) between clips using framer-motion
    - Show idle animation when queue is empty
    - Show "thinking" animation while waiting for live response
    - _Requirements: 1.2, 1.4, 1.5, 8.1, 8.2, 8.3, 8.4, 8.5_

  - [ ]* 9.3 Write property tests for video queue FIFO ordering
    - **Property 1: Video Queue FIFO Ordering**
    - **Property 2: Seamless Clip Transitions**
    - **Validates: Requirements 1.2, 1.4, 1.5, 8.1, 8.2, 8.3**

- [ ] 10. Frontend: WebSocket connection manager
  - [ ] 10.1 Implement WebSocket connection manager with resilience
    - Create `useConnectionManager` hook
    - Implement WebSocket connection through ngrok tunnel URL
    - Send heartbeat every 10 seconds to detect disconnection
    - Implement auto-reconnection with exponential backoff (delay = base × 2^attempt, max 3 attempts)
    - Notify UI of connection state changes (connected, connecting, disconnected, reconnecting)
    - Queue messages during brief disconnections
    - Switch to fallback mode after 3 failed reconnection attempts
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 10.2 Write property test for reconnection exponential backoff
    - **Property 10: Reconnection Exponential Backoff**
    - **Validates: Requirements 4.2, 4.5**

- [ ] 11. Frontend: Chat UI and avatar display
  - [ ] 11.1 Implement the Live Q&A chat panel
    - Create `LiveQAPanel` component with question input, submit button, and status indicator
    - Disable input when connection is disconnected or during pre-generated stages
    - Show connection status indicator (green/yellow/red dot)
    - Display subtitles synchronized with video playback
    - Implement accessible form with proper ARIA labels
    - _Requirements: 2.1, 10.3_

  - [ ] 11.2 Implement the Avatar Display component
    - Create `AvatarDisplay` component wrapping the video player
    - Display video clips at proper aspect ratio (256x256 source, scaled up)
    - Show idle animation (subtle breathing/blinking loop) when no clip is playing
    - Show "thinking" animation (pulsing dots or subtle movement) while pipeline processes
    - Handle fallback display: static image + audio, or text overlay on filler video
    - _Requirements: 3.1, 5.1, 5.2, 5.3, 8.4, 8.5_

- [ ] 12. Frontend: Demo script orchestration
  - [ ] 12.1 Implement demo script player and stage management
    - Create `useDemoScript` hook managing the 20-minute demo flow
    - Define demo stages: intro (pre-gen), agenda (pre-gen), tech demo (pre-gen), warm-up Q&A (live), game (mixed), open Q&A (live), jokes (mixed), motivational (pre-gen), goodbye (pre-gen)
    - Implement auto-advance for pre-generated stages
    - Implement manual trigger ("Start Demo" button) for initial playback
    - Enable/disable chat input based on current stage type (live vs pre-generated)
    - Pre-load all pre-generated clips during initial page load
    - Include at least 5 fallback clips (thinking, joke, transition, error recovery categories)
    - _Requirements: 1.1, 1.2, 1.3, 10.1, 10.2, 10.3, 10.4, 5.5_

  - [ ]* 12.2 Write property test for demo script duration validation
    - **Property 12: Demo Script Duration Validation**
    - **Validates: Requirement 10.1**

- [ ] 13. Checkpoint - Frontend complete
  - Ensure all frontend tests pass, ask the user if questions arise.
  - Verify components render correctly in browser (manual check)

- [ ] 14. Integration: Connect frontend to backend
  - [ ] 14.1 Wire WebSocket communication end-to-end
    - Connect frontend `ConnectionManager` to backend `/ws` endpoint through ngrok URL
    - Implement message routing: question submission → pipeline → video_ready response
    - Implement processing stage updates (show "Generating response...", "Creating voice...", "Animating avatar...")
    - Handle fallback responses from backend (audio-only, text-only modes)
    - Test full flow: type question → see thinking animation → receive and play video clip
    - _Requirements: 2.1, 2.6, 4.1, 5.1, 5.2, 5.3_

  - [ ]* 14.2 Write integration tests for the full pipeline
    - Test WebSocket connection establishment and heartbeat exchange
    - Test question submission and video response receipt
    - Test fallback activation on simulated backend failure
    - Test reconnection behavior on simulated disconnect
    - _Requirements: 2.1, 4.1, 4.2, 5.3_

- [ ] 15. Pre-demo preparation: Generate fallback and pre-generated clips
  - [ ] 15.1 Create a clip generation script
    - Create `scripts/generate_clips.py` that uses the backend pipeline to pre-generate clips
    - Generate intro clip (~30s): "Welcome to AI pe Charcha! I'm GirishOS..."
    - Generate agenda clip (~20s): Explain today's meeting agenda
    - Generate 5 "thinking" filler clips (3-5s each): "Hmm, let me think...", "That's interesting...", etc.
    - Generate 3 joke clips for game segment
    - Generate closing clip (~20s): Goodbye with personality
    - Generate 3 error recovery clips: "Let me rephrase that...", "One moment...", etc.
    - Save all clips to `public/assets/clips/` directory
    - _Requirements: 1.3, 5.5, 10.4_

  - [ ] 15.2 Create demo host setup guide
    - Create `DEMO_GUIDE.md` with step-by-step instructions:
      1. Open Colab notebook and run all cells
      2. Upload Girish's photo (requirements: front-facing, neutral, good lighting, 512x512+)
      3. Copy ngrok URL to frontend `.env`
      4. Run pre-demo health check
      5. Verify fallback clips are loaded
      6. Start demo with "Start Demo" button
    - Include troubleshooting section for common issues
    - _Requirements: 6.4, 10.1_

- [ ] 16. Final checkpoint - Full system integration
  - Ensure all tests pass, ask the user if questions arise.
  - Run the pre-demo checklist from the design document (health check, full pipeline test, fallback test, keep-alive verification)

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Backend tasks (1-8) should be completed first since they form the core pipeline
- Frontend tasks (9-13) can be developed in parallel once interfaces are defined
- The Colab notebook (task 7.3) is the primary deployment artifact for the backend
- Pre-demo preparation (task 15) must be run before any live demo — it requires a working backend
- Property tests use Hypothesis (Python) and fast-check (TypeScript)
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
