import React, { useEffect, useState } from "react"
import "../styles//Dashboard/FarmMap.css"

export default function FarmMap() {
  const [apiKey, setApiKey] = useState("")
  const [error, setError] = useState("")

  useEffect(() => {
    const existing = localStorage.getItem("google_maps_api_key")
    if (existing) setApiKey(existing)
  }, [])

  const handleChange = (e) => {
    setApiKey(e.target.value)
    if (error) setError("")
  }

  const handleActivate = () => {
    const trimmed = apiKey.trim()
    if (!trimmed) {
      setError("Please enter your Google Maps API key.")
      return
    }

    localStorage.setItem("google_maps_api_key", trimmed)
    setError("")
  }

  const isDisabled = apiKey.trim().length === 0

  return (
    <div className="farm-map-page">
      <div className="farm-map-card" role="region" aria-label="Farm Map setup">
        <div className="farm-map-icon" aria-hidden="true">
          <span className="farm-map-icon-emoji">🗺️</span>
        </div>

        <h1 className="farm-map-title">Enable Geospatial Mapping</h1>
        <p className="farm-map-description">
          To visualize your farm and allow agents to reference field locations, you need a Google Maps API key
          with Maps JavaScript and Geometry libraries enabled.
        </p>

        <div className="farm-map-form">
          <input
            className="farm-map-input"
            type="password"
            value={apiKey}
            onChange={handleChange}
            placeholder="Paste API Key (AIza...)"
            aria-label="Google Maps API key"
          />

          <button
            className="farm-map-button"
            type="button"
            onClick={handleActivate}
            disabled={isDisabled}
          >
            Activate Map
          </button>

          {error && <div className="farm-map-error">{error}</div>}

          <div className="farm-map-helper">Keys are stored locally in your browser.</div>
        </div>
      </div>
    </div>
  )
}
