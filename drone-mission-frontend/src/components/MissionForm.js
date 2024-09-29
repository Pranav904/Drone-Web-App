// MissionForm.js
import React, { useState, useCallback } from "react";
import axios from "axios";
import { AnimatePresence } from "framer-motion";
import MissionFormInputs from "./MissionFormInputs";
import StatusAnimation from "./StatusAnimation";
import MissionMap from "./MissionMap";
import "./MissionForm.css";
import DroneDiscovery from "./DroneDiscovery";

const MissionForm = () => {
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [status, setStatus] = useState("");
  const [message, setMessage] = useState("");
  const [showForm, setShowForm] = useState(true);
  const [showDroneList, setDroneList] = useState(true);
  const [markerPosition, setMarkerPosition] = useState(null);
  const [selectedDrone, setSelectedDrone] = useState({}); // Add state to track selected drone

  // Capture selected drone from DroneDiscovery
  const handleDroneSelect = (drone) => {
    setSelectedDrone(drone);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus("loading");
    setDroneList(false);

    const payload = {
      latitude: parseFloat(latitude),
      longitude: parseFloat(longitude),
      drone_id: selectedDrone.id, // Include the selected drone in the payload
    };

    let destination = selectedDrone.ip;

    try {
      const response = await axios.post(
        `http://${destination}/drop_coordinates`,
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
          `Mission started successfully with drone (${selectedDrone.id}) at (${latitude}, ${longitude})`
        );
        setShowForm(false);
        setTimeout(() => {
          setStatus("");
          setShowForm(true);
          setDroneList(true);
        }, 2000);
      }
    } catch (error) {
      setStatus("error");
      setMessage(error.response?.data?.error || "Failed to start the mission.");
      setShowForm(false);
      setTimeout(() => {
        setStatus("");
        setShowForm(true);
        setDroneList(true);
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

          {showDroneList && (
            <DroneDiscovery onDroneSelect={handleDroneSelect} />
          )}

          <StatusAnimation status={status} message={message} />
        </div>

        <MissionMap markerPosition={markerPosition} onMapClick={onMapClick} />
      </div>
    </div>
  );
};

export default MissionForm;