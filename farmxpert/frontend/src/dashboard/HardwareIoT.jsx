import React, { useEffect, useState } from "react";
import "../styles/Dashboard/HardwareIoT.css";

const BLYNK_TOKEN = "PBrw14c3z0O1biZJaH258X9MGpW-FnCE";
const BASE_URL = "https://blr1.blynk.cloud/external/api/get?token=" + BLYNK_TOKEN;

const SENSORS = [
  { label: "Air Temperature", pin: "V0", unit: "°C", color: "#FF6B6B" },
  { label: "Air Humidity", pin: "V1", unit: "%", color: "#4ECDC4" },
  { label: "Soil Moisture", pin: "V2", unit: "%", color: "#45B7D1" },
  { label: "Soil Temperature", pin: "V3", unit: "°C", color: "#FF9F43" },
  { label: "Soil EC", pin: "V4", unit: "µS/cm", color: "#A8D8EA" },
  { label: "Soil pH", pin: "V5", unit: "pH", color: "#AA96DA" },
  { label: "Nitrogen (N)", pin: "V6", unit: "mg/kg", color: "#FCBAD3" },
  { label: "Phosphorus (P)", pin: "V7", unit: "mg/kg", color: "#FFFFD2" },
  { label: "Potassium (K)", pin: "V8", unit: "mg/kg", color: "#837E7C" },
];

export default function HardwareIoT() {
  const [sensorData, setSensorData] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    try {
      const promises = SENSORS.map(async (sensor) => {
        const response = await fetch(`${BASE_URL}&${sensor.pin}`);
        if (!response.ok) throw new Error(`Failed to fetch ${sensor.label}`);
        const value = await response.text();
        return { [sensor.pin]: value };
      });

      const results = await Promise.all(promises);
      const newData = results.reduce((acc, curr) => ({ ...acc, ...curr }), {});
      setSensorData(newData);
      setLoading(false);
      setError(null);
    } catch (err) {
      console.error("Error fetching sensor data:", err);
      setError("Failed to fetch sensor data. Please check connection.");
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Fetch every 5 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="hardware-iot-page">
      <div className="hardware-iot-header">
        <div className="hardware-iot-header-left">
          <div className="hardware-iot-title">Live Farm Sensors</div>
          <div className="hardware-iot-subtitle">Real-time environmental and soil monitoring.</div>
        </div>
        <div className="hardware-iot-status">
          <span className={`status-indicator ${error ? "offline" : "online"}`}></span>
          {error ? "Offline" : "Live"}
        </div>
      </div>

      {loading && !Object.keys(sensorData).length ? (
        <div className="loading-state">Loading sensor data...</div>
      ) : (
        <div className="sensors-grid">
          {SENSORS.map((sensor) => (
            <div key={sensor.pin} className="sensor-card" style={{ borderTop: `4px solid ${sensor.color}` }}>
              <div className="sensor-label">{sensor.label}</div>
              <div className="sensor-value">
                {sensorData[sensor.pin] !== undefined ? sensorData[sensor.pin] : "--"}
                <span className="sensor-unit">{sensor.unit}</span>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {error && <div className="error-message">{error}</div>}
    </div>
  );
}
