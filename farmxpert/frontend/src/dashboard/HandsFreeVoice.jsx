import React, { useEffect, useMemo, useRef, useState } from "react"
import "../styles/Dashboard/HandsFreeVoice.css"

const DEFAULT_LOCALE = "en-IN"

export default function HandsFreeVoice() {
  const [isListening, setIsListening] = useState(false)
  const [status, setStatus] = useState("idle") // idle | listening | thinking | speaking | error
  const [userTranscript, setUserTranscript] = useState("")
  const [assistantText, setAssistantText] = useState("")
  const [detectedLanguage, setDetectedLanguage] = useState("English")
  const [locale, setLocale] = useState(DEFAULT_LOCALE)
  const [error, setError] = useState(null)
  const [apiReachable, setApiReachable] = useState(null)

  const recognitionRef = useRef(null)
  const transcriptRef = useRef("")
  const finalTranscriptRef = useRef("")
  const sessionIdRef = useRef(null)
  const isSpeakingRef = useRef(false)
  const abortStreamRef = useRef(null)
  const silenceTimerRef = useRef(null)
  const lastFinalRef = useRef("")

  const SpeechRecognition = useMemo(() => {
    return window.SpeechRecognition || window.webkitSpeechRecognition || null
  }, [])

  const stopSpeaking = () => {
    try {
      window.speechSynthesis?.cancel()
    } catch (e) {
      // no-op
    }
    isSpeakingRef.current = false
  }

  const stopStream = () => {
    try {
      abortStreamRef.current?.abort()
    } catch (e) {
      // no-op
    }
  }

  const clearSilenceTimer = () => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current)
      silenceTimerRef.current = null
    }
  }

  const armSilenceTimer = () => {
    clearSilenceTimer()
    silenceTimerRef.current = setTimeout(() => {
      stopRecognition()
    }, 1400)
  }

  const apiFetch = async (path, options) => {
    try {
      return await fetch(path, options)
    } catch (e) {
      return await fetch(`http://localhost:8000${path}`, options)
    }
  }

  const speak = async (text, speechLocale) => {
    if (!text) return
    if (!("speechSynthesis" in window)) return

    stopSpeaking()
    setStatus("speaking")
    isSpeakingRef.current = true

    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = speechLocale || locale || DEFAULT_LOCALE
    utterance.rate = 1
    utterance.pitch = 1

    utterance.onend = () => {
      isSpeakingRef.current = false
      if (isListening) {
        startRecognition()
      } else {
        setStatus("idle")
      }
    }
    utterance.onerror = () => {
      isSpeakingRef.current = false
      setStatus("error")
    }

    window.speechSynthesis.speak(utterance)
  }

  const detectLanguage = async (text) => {
    const res = await apiFetch("/api/super-agent/language/detect", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    })
    if (!res.ok) {
      throw new Error(`Language detect failed: ${res.status} ${res.statusText}`)
    }
    return await res.json()
  }

  const queryGeminiResponse = async (query, sessionId) => {
    const res = await apiFetch("/api/super-agent/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        session_id: sessionId,
        context: {
          locale,
          conversational: true
        }
      }),
    })
    if (!res.ok) {
      throw new Error(`Query failed: ${res.status} ${res.statusText}`)
    }

    const data = await res.json()
    // Use natural_language field if available, fallback to response
    return data.natural_language || data.response || "I'm sorry, I couldn't process that."
  }

  const stopRecognition = () => {
    try {
      recognitionRef.current?.stop()
    } catch (e) {
      // no-op
    }
  }

  const commitUserTurn = async () => {
    if (!isListening) return
    if (status === "thinking") return

    const finalText = (transcriptRef.current || "").trim()
    transcriptRef.current = ""
    finalTranscriptRef.current = ""

    if (!finalText) {
      try {
        recognitionRef.current?.start()
      } catch (e) {
        // no-op
      }
      return
    }

    setStatus("thinking")
    setAssistantText("")

    try {
      const lang = await detectLanguage(finalText)
      setDetectedLanguage(lang.language || "")
      setLocale(lang.locale || DEFAULT_LOCALE)

      const sessionId = sessionIdRef.current || crypto.randomUUID()
      sessionIdRef.current = sessionId

      const answer = await queryGeminiResponse(finalText, sessionId)
      setAssistantText(answer)
      await speak(answer, (lang.locale || DEFAULT_LOCALE))
    } catch (err) {
      setError(err?.message || "Voice session failed")
      setStatus("error")
      try {
        recognitionRef.current?.start()
      } catch (e) {
        // no-op
      }
    } finally {
      setUserTranscript("")
      lastFinalRef.current = ""
    }
  }

  const startRecognition = () => {
    if (!SpeechRecognition) {
      setError("Speech recognition is not supported in this browser (use Chrome/Edge).")
      setStatus("error")
      return
    }

    if (isSpeakingRef.current) {
      return
    }

    if (!recognitionRef.current) {
      const rec = new SpeechRecognition()
      rec.continuous = true
      rec.interimResults = true
      rec.lang = locale || DEFAULT_LOCALE

      rec.onstart = () => {
        setStatus("listening")
        setError(null)
        armSilenceTimer()
      }

      rec.onresult = (event) => {
        let newFinal = ""
        let interimTranscript = ""

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const t = event.results[i][0].transcript
          if (event.results[i].isFinal) newFinal += t
          else interimTranscript += t
        }

        if (newFinal.trim()) {
          finalTranscriptRef.current = (finalTranscriptRef.current + " " + newFinal).trim()
        }

        const combined = (finalTranscriptRef.current + " " + interimTranscript).trimStart()
        transcriptRef.current = combined
        setUserTranscript(combined)

        if (combined) {
          lastFinalRef.current = combined
          armSilenceTimer()
        }

        if (combined && isSpeakingRef.current) {
          stopSpeaking()
          stopStream()
        }
      }

      rec.onerror = (e) => {
        setError(e?.error || "Speech recognition error")
        setStatus("error")
      }

      rec.onend = async () => {
        if (!isListening) return
        if (isSpeakingRef.current) return

        if (lastFinalRef.current) {
          transcriptRef.current = lastFinalRef.current
        }
        lastFinalRef.current = ""
        clearSilenceTimer()
        await commitUserTurn()
      }

      recognitionRef.current = rec
    } else {
      recognitionRef.current.lang = locale || DEFAULT_LOCALE
    }

    try {
      recognitionRef.current.start()
    } catch (e) {
      // no-op
    }
  }

  const startSession = () => {
    setIsListening(true)
    setError(null)
    startRecognition()
  }

  const endSession = () => {
    setIsListening(false)
    setStatus("idle")
    setUserTranscript("")
    setAssistantText("")
    clearSilenceTimer()
    stopRecognition()
    stopSpeaking()
    stopStream()
    transcriptRef.current = ""
    finalTranscriptRef.current = ""
    lastFinalRef.current = ""
  }

  const toggleSession = () => {
    if (isListening) {
      endSession()
    } else {
      startSession()
    }
  }

  useEffect(() => {
    let mounted = true

    const probe = async () => {
      try {
        const res = await apiFetch("/api/health", { method: "GET" })
        if (!mounted) return
        setApiReachable(res.ok)
      } catch (e) {
        if (!mounted) return
        setApiReachable(false)
      }
    }

    probe()

    return () => {
      mounted = false
      endSession()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="handsfree-voice-page">
      <div className="handsfree-voice-center">
        <div className="handsfree-voice-topbar">
          <div className="handsfree-voice-pill">
            <span className={`handsfree-voice-dot handsfree-voice-dot-${status}`} />
            <span className="handsfree-voice-pill-text">
              {status === "idle" && "Ready"}
              {status === "listening" && "Listening"}
              {status === "thinking" && "Thinking"}
              {status === "speaking" && "Speaking"}
              {status === "error" && "Error"}
            </span>
          </div>

          <div className="handsfree-voice-pill">
            <span className={`handsfree-voice-api ${apiReachable === true ? "ok" : apiReachable === false ? "bad" : ""}`}>
              API
            </span>
            <span className="handsfree-voice-pill-text">{detectedLanguage || "Auto"} · {locale}</span>
          </div>
        </div>

        <button
          type="button"
          className={`handsfree-voice-livebtn ${isListening ? "active" : ""} ${status}`}
          onClick={toggleSession}
          aria-label={isListening ? "Stop" : "Start"}
        >
          <div className="handsfree-voice-livebtn-inner">
            <svg
              className="handsfree-voice-mic-icon"
              viewBox="0 0 24 24"
              width="30"
              height="30"
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
          </div>
          <div className="handsfree-voice-livebtn-label">
            {!isListening ? "Tap to talk" : status === "speaking" ? "Tap to stop" : "Listening"}
          </div>
        </button>

        <div className="handsfree-voice-captions">
          <div className="handsfree-voice-caption">
            <div className="handsfree-voice-caption-head">Farmer</div>
            <div className="handsfree-voice-caption-body">{userTranscript || (isListening ? "…" : "")}</div>
          </div>
          <div className="handsfree-voice-caption">
            <div className="handsfree-voice-caption-head">FarmXpert</div>
            <div className="handsfree-voice-caption-body">{assistantText || (isListening ? "…" : "")}</div>
          </div>
          {error && <div className="handsfree-voice-error">{error}</div>}
        </div>
      </div>

      {isListening && (
        <div className="handsfree-voice-controls">
          <button className="handsfree-voice-control" type="button" onClick={() => { stopSpeaking(); stopStream(); }}>
            Stop reply
          </button>
          <button className="handsfree-voice-control danger" type="button" onClick={endSession}>
            End
          </button>
        </div>
      )}
    </div>
  )
}
