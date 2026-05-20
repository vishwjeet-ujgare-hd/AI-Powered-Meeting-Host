"use client";

import { useState, useEffect, useRef, useCallback } from "react";

type ConnectionStatus = "connecting" | "connected" | "disconnected" | "reconnecting";
type PipelineStage = "llm" | "tts" | "animation" | "encoding" | null;

interface ChatMessage {
  id: string;
  type: "question" | "answer" | "error";
  text: string;
  timestamp: number;
}

export default function Home() {
  const [status, setStatus] = useState<ConnectionStatus>("disconnected");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentStage, setCurrentStage] = useState<PipelineStage>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [currentText, setCurrentText] = useState("");
  const wsRef = useRef<WebSocket | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const heartbeatRef = useRef<NodeJS.Timeout | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "wss://localhost:8000";
  const HTTP_URL = BACKEND_URL.replace("wss://", "https://").replace("ws://", "http://");

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setStatus("connecting");
    const ws = new WebSocket(`${BACKEND_URL}/ws`);

    ws.onopen = () => {
      setStatus("connected");
      console.log("✅ Connected to GirishOS backend");

      // Start heartbeat
      heartbeatRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "heartbeat" }));
        }
      }, 10000);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "processing") {
        setCurrentStage(data.stage);
      } else if (data.type === "video_ready") {
        setIsProcessing(false);
        setCurrentStage(null);
        setCurrentText(data.text);

        // Build full video URL
        const fullVideoUrl = `${HTTP_URL}${data.url}`;
        setVideoUrl(fullVideoUrl);

        setMessages((prev) => [
          ...prev,
          {
            id: data.questionId,
            type: "answer",
            text: data.text,
            timestamp: Date.now(),
          },
        ]);
      } else if (data.type === "fallback_response") {
        setIsProcessing(false);
        setCurrentStage(null);
        setCurrentText(data.text);
        setMessages((prev) => [
          ...prev,
          {
            id: data.questionId,
            type: "answer",
            text: data.text,
            timestamp: Date.now(),
          },
        ]);
      } else if (data.type === "error") {
        setIsProcessing(false);
        setCurrentStage(null);
        setMessages((prev) => [
          ...prev,
          {
            id: data.questionId,
            type: "error",
            text: data.message,
            timestamp: Date.now(),
          },
        ]);
      }
    };

    ws.onclose = () => {
      setStatus("disconnected");
      if (heartbeatRef.current) clearInterval(heartbeatRef.current);
      console.log("❌ Disconnected from backend");

      // Auto-reconnect after 3 seconds
      setTimeout(() => {
        setStatus("reconnecting");
        connect();
      }, 3000);
    };

    ws.onerror = () => {
      setStatus("disconnected");
    };

    wsRef.current = ws;
  }, [BACKEND_URL, HTTP_URL]);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (heartbeatRef.current) clearInterval(heartbeatRef.current);
    };
  }, [connect]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || status !== "connected" || isProcessing) return;

    const questionId = crypto.randomUUID();

    // Send to backend
    wsRef.current?.send(
      JSON.stringify({
        type: "question",
        text: question,
        id: questionId,
      })
    );

    // Add to messages
    setMessages((prev) => [
      ...prev,
      {
        id: questionId,
        type: "question",
        text: question,
        timestamp: Date.now(),
      },
    ]);

    setIsProcessing(true);
    setCurrentStage("llm");
    setQuestion("");
  };

  const getStageText = (stage: PipelineStage) => {
    switch (stage) {
      case "llm": return "Thinking...";
      case "tts": return "Generating voice...";
      case "animation": return "Animating avatar...";
      case "encoding": return "Preparing video...";
      default: return "Processing...";
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case "connected": return "bg-green-500";
      case "connecting":
      case "reconnecting": return "bg-yellow-500";
      case "disconnected": return "bg-red-500";
    }
  };

  return (
    <main className="flex flex-col items-center min-h-screen p-4 md:p-8">
      {/* Header */}
      <div className="w-full max-w-4xl mb-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl md:text-3xl font-bold text-white">
            🤖 GirishOS
          </h1>
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${getStatusColor()}`} />
            <span className="text-sm text-gray-400 capitalize">{status}</span>
          </div>
        </div>
        <p className="text-gray-500 mt-1">AI-Powered Meeting Host • AI pe Charcha</p>
      </div>

      {/* Avatar / Video Section */}
      <div className="w-full max-w-4xl mb-6">
        <div className="relative bg-gray-900 rounded-2xl overflow-hidden aspect-video max-h-[400px] flex items-center justify-center border border-gray-800">
          {videoUrl ? (
            <video
              ref={videoRef}
              src={videoUrl}
              autoPlay
              className="w-full h-full object-contain"
              onEnded={() => setVideoUrl(null)}
            />
          ) : isProcessing ? (
            <div className="flex flex-col items-center gap-4">
              <div className="w-24 h-24 rounded-full bg-gray-800 flex items-center justify-center">
                <div className="flex gap-1">
                  <span className="thinking-dot w-3 h-3 bg-blue-400 rounded-full" />
                  <span className="thinking-dot w-3 h-3 bg-blue-400 rounded-full" />
                  <span className="thinking-dot w-3 h-3 bg-blue-400 rounded-full" />
                </div>
              </div>
              <p className="text-gray-400 text-sm">{getStageText(currentStage)}</p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-4">
              <div className="w-32 h-32 rounded-full bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center text-5xl">
                🤖
              </div>
              <p className="text-gray-400">Ask me anything about AI!</p>
            </div>
          )}

          {/* Subtitle overlay */}
          {currentText && !isProcessing && (
            <div className="absolute bottom-0 left-0 right-0 bg-black/70 p-3">
              <p className="text-white text-center text-sm">{currentText}</p>
            </div>
          )}
        </div>
      </div>

      {/* Chat Messages */}
      <div className="w-full max-w-4xl mb-4 flex-1 overflow-y-auto max-h-[200px] space-y-3">
        {messages.map((msg) => (
          <div
            key={msg.id + msg.timestamp}
            className={`flex ${msg.type === "question" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] px-4 py-2 rounded-2xl text-sm ${
                msg.type === "question"
                  ? "bg-blue-600 text-white"
                  : msg.type === "error"
                  ? "bg-red-900/50 text-red-300 border border-red-800"
                  : "bg-gray-800 text-gray-200"
              }`}
            >
              {msg.text}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="w-full max-w-4xl">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder={
              status === "connected"
                ? "Ask GirishOS a question..."
                : "Connecting to backend..."
            }
            disabled={status !== "connected" || isProcessing}
            className="flex-1 px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={status !== "connected" || isProcessing || !question.trim()}
            className="px-6 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isProcessing ? "..." : "Ask"}
          </button>
        </form>
      </div>
    </main>
  );
}
