import React, { useEffect, useRef, useState } from "react"
import "../styles/Dashboard/HardwareIoT.css"

// POST /api/iot/connect
// POST /api/iot/provision
// GET  /api/iot/status

export default function HardwareIoT() {
  const [status, setStatus] = useState("idle")
  const timerRef = useRef(null)

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current)
      }
    }
  }, [])

  const handleConnect = () => {
    if (status === "connecting") return

    if (timerRef.current) {
      clearTimeout(timerRef.current)
    }

    setStatus("connecting")

    timerRef.current = setTimeout(() => {
      setStatus("failed")
    }, 5000)
  }

  const connectLabel = status === "idle" ? "Connect" : status === "connecting" ? "Connecting..." : "Not Connected"

  return (
    <div className="hardware-iot-page">
      <div className="hardware-iot-header">
        <div className="hardware-iot-header-left">
          <div className="hardware-iot-title">Hardware Integration</div>
          <div className="hardware-iot-subtitle">Real-time telemetry via MQTT Protocol.</div>
        </div>

        <button
          type="button"
          className={`hardware-iot-connect-btn ${status}`}
          onClick={handleConnect}
          disabled={status === "connecting"}
        >
          {status === "connecting" && <span className="hardware-iot-spinner" aria-hidden="true" />}
          <span>{connectLabel}</span>
        </button>
      </div>

      <div className="hardware-iot-content">
        <div className="hardware-iot-provision-card" role="button" tabIndex={0} aria-label="Provision New Device">
          <div className="hardware-iot-plus" aria-hidden="true">
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
              <path d="M12 5v14" />
              <path d="M5 12h14" />
            </svg>
          </div>

          <div className="hardware-iot-provision-title">Provision New Device</div>
          <div className="hardware-iot-provision-subtitle">
            Publishes a new device discovery
            <br />
            packet to the MQTT broker.
          </div>
        </div>
      </div>
    </div>
  )
}
