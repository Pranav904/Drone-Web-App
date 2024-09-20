// MissionForm.js
import React, { useState, useCallback } from "react";
import axios from "axios";
import {AnimatePresence } from "framer-motion";
import MissionFormInputs from "./MissionFormInputs";
import MissionHistory from "./MissionHistory";
import StatusAnimation from "./StatusAnimation";
import MissionMap from "./MissionMap";
import "./MissionForm.css";

const MissionForm = () => {
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [status, setStatus] = useState("");
  const [message, setMessage] = useState("");
  const [showForm, setShowForm] = useState(true);
  const [missionHistory, setMissionHistory] = useState([]);
  const [showMissionHistory, setShowMissionHistory] = useState(false);
  const [markerPosition, setMarkerPosition] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus("loading");
    setShowMissionHistory(false);

    const payload = {
      latitude: parseFloat(latitude),
      longitude: parseFloat(longitude),
    };

    try {
      const response = await axios.post(
        "http://localhost:5000/drop_coordinates",
        payload,
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (response.status === 200) {
        setStatus("success");
        setMessage(
          `Mission started successfully at (${latitude}, ${longitude})`
        );
        setShowForm(false);
        setTimeout(() => {
          setMissionHistory([...missionHistory, message]);
          setStatus("");
          setShowForm(true);
          setShowMissionHistory(true);
        }, 2000);
      }
    } catch (error) {
      setStatus("error");
      setMessage(error.response?.data?.error || "Failed to start the mission.");
      setShowForm(false);
      setTimeout(() => {
        setStatus("");
        setShowForm(true);
        setShowMissionHistory(true);
      }, 2000);
    }
  };

  const onMapClick = useCallback((e) => {
    const lat = e.latLng.lat();
    const lng = e.latLng.lng();
    setLatitude(lat.toFixed(6));
    setLongitude(lng.toFixed(6));
    setMarkerPosition({ lat, lng });
  }, []);

  return (
    <div className="mission-control-container">
      <h1>Drone Mission Control</h1>
      <div className="content-wrapper">
        <div className="form-container">
          <AnimatePresence>
            {showForm && (
              <MissionFormInputs
                latitude={latitude}
                longitude={longitude}
                setLatitude={setLatitude}
                setLongitude={setLongitude}
                handleSubmit={handleSubmit}
              />
            )}
          </AnimatePresence>

          {showMissionHistory && (
            <MissionHistory missionHistory={missionHistory} />
          )}

          <StatusAnimation status={status} message={message} />
        </div>

        <MissionMap
          markerPosition={markerPosition}
          onMapClick={onMapClick}
        />
      </div>
    </div>
  );
};

export default MissionForm;