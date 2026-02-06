import React, { useState } from "react"
import "../styles/Dashboard/HandsFreeVoice.css"

export default function HandsFreeVoice() {
  const [isListening, setIsListening] = useState(false)

  const startSession = () => setIsListening(true)
  const endSession = () => setIsListening(false)

  // POST /api/voice/start
  // POST /api/voice/stop

  return (
    <div className="handsfree-voice-page">
      <div className="handsfree-voice-center">
        <div className={`handsfree-voice-mic ${isListening ? "handsfree-voice-mic-active" : ""}`}>
          {!isListening ? (
            <svg
              className="handsfree-voice-mic-icon"
              viewBox="0 0 24 24"
              width="28"
              height="28"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3z" />
              <path d="M19 11a7 7 0 0 1-14 0" />
              <line x1="12" y1="18" x2="12" y2="22" />
              <line x1="8" y1="22" x2="16" y2="22" />
              <line x1="4" y1="4" x2="20" y2="20" />
            </svg>
          ) : (
            <svg
              className="handsfree-voice-mic-icon"
              viewBox="0 0 24 24"
              width="28"
              height="28"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3z" />
              <path d="M19 11a7 7 0 0 1-14 0" />
              <line x1="12" y1="18" x2="12" y2="22" />
              <line x1="8" y1="22" x2="16" y2="22" />
            </svg>
          )}
        </div>

        {!isListening ? (
          <>
            <div className="handsfree-voice-title">Ready to connect</div>
            <div className="handsfree-voice-subtitle">Hands-free voice interface for field operations.</div>
          </>
        ) : (
          <>
            <div className="handsfree-voice-title">Listening...</div>
            <div className="handsfree-voice-subtitle">Ask about weather, machinery status, or log a task.</div>
          </>
        )}
      </div>

      <div className="handsfree-voice-actions">
        {!isListening ? (
          <button className="handsfree-voice-btn handsfree-voice-btn-start" type="button" onClick={startSession}>
            <span className="handsfree-voice-btn-icon" aria-hidden="true">
              <svg
                viewBox="0 0 24 24"
                width="18"
                height="18"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3z" />
                <path d="M19 11a7 7 0 0 1-14 0" />
                <line x1="12" y1="18" x2="12" y2="22" />
                <line x1="8" y1="22" x2="16" y2="22" />
              </svg>
            </span>
            START VOICE SESSION
          </button>
        ) : (
          <div className="handsfree-voice-actions-listening">
            <button className="handsfree-voice-mini" type="button" onClick={endSession} aria-label="End session">
              <svg
                viewBox="0 0 24 24"
                width="18"
                height="18"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3z" />
                <path d="M19 11a7 7 0 0 1-14 0" />
                <line x1="12" y1="18" x2="12" y2="22" />
                <line x1="8" y1="22" x2="16" y2="22" />
              </svg>
            </button>

            <button className="handsfree-voice-btn handsfree-voice-btn-end" type="button" onClick={endSession}>
              END SESSION
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
