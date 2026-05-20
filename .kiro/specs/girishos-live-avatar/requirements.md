# Requirements Document

## Introduction

GirishOS Live Avatar is an AI-powered interactive meeting host for "AI pe Charcha" meetings. The system presents a realistic AI avatar of "Girish" that delivers pre-generated agenda content and responds to live audience questions with voice and animated facial expressions in real-time. The entire stack uses free-tier services: Groq (LLM), Edge TTS (voice), SadTalker on Google Colab (face animation), Next.js on Vercel (frontend), and FastAPI on Colab (backend). The system must reliably operate for a full 20-minute live demo without failure.

## Glossary

- **Avatar**: The AI-generated talking-head video of Girish with lip-synced speech and facial expressions
- **Pipeline**: The sequential processing chain: Question → Groq LLM → Edge TTS → SadTalker → Video clip
- **Frontend**: The Next.js web application hosted on Vercel that displays the avatar and accepts audience input
- **Backend**: The FastAPI server running on Google Colab that orchestrates the pipeline
- **Groq_LLM**: The free-tier Groq API service providing fast LLM inference (llama-3.3-70b-versatile)
- **Edge_TTS**: Microsoft Edge's free text-to-speech service producing natural voice audio
- **SadTalker**: The deep learning model that generates talking-head video from a photo and audio input
- **Video_Queue**: The frontend component that manages seamless playback of sequential video clips
- **Connection_Manager**: The frontend WebSocket handler with heartbeat monitoring and auto-reconnection
- **Fallback_Clip**: A pre-generated video clip used when the live pipeline fails
- **Keep_Alive_Loop**: A background process that prevents Colab from disconnecting during the demo
- **Tunnel**: The ngrok/localtunnel service that exposes the Colab backend to the public internet
- **Demo_Script**: The structured 20-minute sequence of pre-generated and live content stages

## Requirements

### Requirement 1: Pre-generated Agenda Presentation

**User Story:** As a meeting host, I want the GirishOS avatar to present the meeting agenda using pre-generated video clips, so that the opening segment has zero risk of failure and runs smoothly every time.

#### Acceptance Criteria

1. WHEN the demo host clicks "Start Demo", THE Frontend SHALL play the pre-generated intro video clip immediately without requiring backend connectivity
2. WHEN a pre-generated stage is active, THE Frontend SHALL play the corresponding pre-generated video clip in sequence without gaps exceeding 200 milliseconds
3. THE Frontend SHALL pre-load all pre-generated clips (intro, agenda, tech demo, closing) during initial page load before the demo starts
4. WHEN transitioning between pre-generated clips, THE Video_Queue SHALL cross-fade between clips within 200 milliseconds to maintain seamless visual continuity
5. WHEN a pre-generated clip finishes playing, THE Video_Queue SHALL automatically advance to the next clip in the Demo_Script sequence

### Requirement 2: Live Q&A Pipeline

**User Story:** As an audience member, I want to ask questions and receive real-time voice and video responses from the GirishOS avatar, so that I can have an interactive conversation during the meeting.

#### Acceptance Criteria

1. WHEN an audience member submits a question, THE Backend SHALL process it through the full Pipeline (Groq LLM → Edge TTS → SadTalker) and return a video response
2. WHEN a question is submitted, THE Pipeline SHALL produce a complete video response within 8 seconds total processing time
3. WHEN the Groq_LLM generates a response, THE Backend SHALL limit the response to 2-3 sentences (under 150 tokens) to keep TTS and animation times short
4. WHEN Edge_TTS synthesizes speech, THE Edge_TTS SHALL produce WAV audio with a duration not exceeding 12 seconds
5. WHEN SadTalker generates video, THE SadTalker SHALL produce an MP4 clip with lip movements synchronized to the audio within 100 milliseconds tolerance
6. WHEN a video response is ready, THE Backend SHALL deliver it to the Frontend via WebSocket with the video URL, duration, and subtitle text

### Requirement 3: Avatar Video Quality

**User Story:** As a meeting attendee, I want the avatar to look realistic with proper lip-sync and expressions, so that the experience feels engaging and natural.

#### Acceptance Criteria

1. THE SadTalker SHALL generate video at 256x256 resolution with 25 frames per second for consistent visual quality
2. WHEN generating video, THE SadTalker SHALL use an expression scale of 1.2 to produce slightly exaggerated facial expressions for audience engagement
3. THE SadTalker SHALL keep the model loaded in GPU memory between requests to avoid reload latency
4. WHEN a video clip is generated, THE Backend SHALL encode it as H.264 MP4 for universal browser compatibility

### Requirement 4: WebSocket Connection Resilience

**User Story:** As a demo host, I want the connection between frontend and backend to recover automatically from brief interruptions, so that the demo continues without manual intervention.

#### Acceptance Criteria

1. THE Connection_Manager SHALL send a heartbeat message every 10 seconds to detect disconnection early
2. WHEN the WebSocket connection drops, THE Connection_Manager SHALL attempt automatic reconnection with exponential backoff up to 3 retry attempts
3. WHEN a disconnection is detected, THE Frontend SHALL notify the UI of the connection state change within 3 seconds
4. WHEN reconnection succeeds within 30 seconds, THE Connection_Manager SHALL resume normal operation without user intervention
5. IF reconnection fails after 3 attempts, THEN THE Frontend SHALL switch to fallback mode and display pre-generated content

### Requirement 5: Fallback and Graceful Degradation

**User Story:** As a demo host, I want the system to never show silence or a blank screen during failures, so that the audience always sees a response regardless of backend issues.

#### Acceptance Criteria

1. IF the SadTalker animation stage fails, THEN THE Backend SHALL fall back to serving audio-only response with a static avatar image (Level 2 fallback)
2. IF both SadTalker and Edge_TTS fail, THEN THE Backend SHALL fall back to text-only response displayed over a pre-generated filler video clip (Level 3 fallback)
3. IF the entire backend is unreachable, THEN THE Frontend SHALL play a pre-generated error recovery clip and display a text response (Level 4 fallback)
4. WHEN any pipeline stage fails, THE Backend SHALL still produce a visible or audible response to the user within 8 seconds
5. THE Frontend SHALL have at least 5 pre-loaded fallback clips categorized as thinking, joke, transition, and error recovery types

### Requirement 6: Colab Session Stability

**User Story:** As a demo host, I want the Google Colab session to remain active for the entire 20-minute demo, so that the backend does not disconnect mid-presentation.

#### Acceptance Criteria

1. THE Keep_Alive_Loop SHALL execute a GPU touch operation every 60 seconds to prevent Colab from timing out due to inactivity
2. WHILE the demo is running, THE Keep_Alive_Loop SHALL verify the Tunnel health on each iteration and restart it if the connection has dropped
3. THE Keep_Alive_Loop SHALL maintain the Colab session for at least 25 minutes continuously (20-minute demo plus 5-minute buffer)
4. WHEN the Tunnel drops and is restarted, THE Backend SHALL log the new public URL to the Colab output for the demo host to update if needed
5. THE Backend SHALL monitor GPU memory usage and keep it below 80 percent of available VRAM to prevent out-of-memory crashes

### Requirement 7: Response Caching

**User Story:** As a system operator, I want repeated or similar questions to be answered instantly from cache, so that the system responds faster and reduces load on the pipeline.

#### Acceptance Criteria

1. WHEN a question is processed successfully, THE Backend SHALL cache the video result for future identical questions
2. WHEN an identical question is received, THE Backend SHALL return the cached response within 500 milliseconds without re-running the pipeline
3. THE Backend SHALL maintain a cache of the last 20 responses during the session
4. WHEN the cache is full, THE Backend SHALL evict the oldest entry to make room for new responses

### Requirement 8: Frontend Video Playback

**User Story:** As a meeting attendee, I want video clips to play seamlessly without visible gaps or stuttering, so that the avatar presentation feels continuous and professional.

#### Acceptance Criteria

1. THE Video_Queue SHALL play clips in strict FIFO order matching the sequence they were received
2. WHEN a clip finishes playing and the queue is non-empty, THE Video_Queue SHALL transition to the next clip with no more than 200 milliseconds gap
3. WHILE a clip is playing and the queue is non-empty, THE Video_Queue SHALL pre-load the next clip in a hidden video element (double-buffering)
4. WHEN the video queue is empty and no clip is playing, THE Frontend SHALL display an idle animation of the avatar
5. WHILE waiting for a live response, THE Frontend SHALL display a "thinking" animation to indicate processing is in progress

### Requirement 9: Input Validation and Rate Limiting

**User Story:** As a system operator, I want user input to be validated and rate-limited, so that the system is protected from abuse and remains stable during the demo.

#### Acceptance Criteria

1. WHEN a question is submitted, THE Backend SHALL validate that the question text is between 1 and 500 characters
2. IF a question with an empty or whitespace-only text is submitted, THEN THE Backend SHALL reject it and return an error message
3. THE Backend SHALL enforce a rate limit of 1 question per 5 seconds per client to prevent overloading the pipeline
4. WHEN a duplicate question ID is submitted, THE Backend SHALL reject it to prevent duplicate processing
5. WHEN user input is received, THE Backend SHALL sanitize it by stripping HTML tags before passing it to the Groq_LLM

### Requirement 10: Demo Script Orchestration

**User Story:** As a demo host, I want a structured 20-minute demo flow that mixes pre-generated and live content, so that I can deliver a polished presentation with minimal risk.

#### Acceptance Criteria

1. THE Demo_Script SHALL define stages covering the full 20-minute duration with each stage marked as pre-generated, live, or mixed type
2. WHEN a pre-generated stage is scheduled, THE Frontend SHALL trigger playback automatically or on manual host action based on the stage configuration
3. WHEN transitioning from a pre-generated stage to a live Q&A stage, THE Frontend SHALL enable the chat input and indicate readiness for audience questions
4. THE Demo_Script SHALL include at least 5 fallback clips and pre-generated content for intro, agenda, and closing segments to ensure zero-risk bookend segments
