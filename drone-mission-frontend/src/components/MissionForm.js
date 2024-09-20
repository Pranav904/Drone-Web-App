import React, { useState, useRef, useCallback } from "react";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import { GoogleMap, LoadScript, Marker } from "@react-google-maps/api";
import { CheckCircleIcon, XCircleIcon } from "@heroicons/react/24/solid";
import RingsLoaderComponent from "./RingsLoaderComponent";
import "./MissionForm.css";

const mapContainerStyle = {
  width: "98%",
  height: "100%",
};

const center = {
  lat: 12.841,
  lng: 80.154,
};

const MissionForm = () => {
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [status, setStatus] = useState("");
  const [message, setMessage] = useState("");
  const [showForm, setShowForm] = useState(true);
  const [missionHistory, setMissionHistory] = useState([]);
  const [showMissionHistory, setShowMissionHistory] = useState(false);
  const [markerPosition, setMarkerPosition] = useState(null);
  const formRef = useRef(null);

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
              <motion.form
                ref={formRef}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                transition={{ duration: 0.3 }}
                onSubmit={handleSubmit}
                className="mission-form"
              >
                <div className="form-field">
                  <motion.label
                    initial={{ x: -20, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: 0.1 }}
                  >
                    Latitude:
                  </motion.label>
                  <motion.input
                    className="latitude input"
                    type="number"
                    step="any"
                    value={latitude}
                    onChange={(e) => setLatitude(e.target.value)}
                    required
                    initial={{ scale: 0.8 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.2 }}
                  />
                </div>

                <div className="form-field">
                  <motion.label
                    initial={{ x: -20, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: 0.3 }}
                  >
                    Longitude:
                  </motion.label>
                  <motion.input
                    className="longitude input"
                    type="number"
                    step="any"
                    value={longitude}
                    onChange={(e) => setLongitude(e.target.value)}
                    required
                    initial={{ scale: 0.8 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.4 }}
                  />
                </div>

                <motion.button
                  type="submit"
                  className="start-mission-btn"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  Start Mission
                </motion.button>
              </motion.form>
            )}
          </AnimatePresence>

          {showMissionHistory && (
            <div className="mission-history">
              <h3>Mission History:</h3>
              <ul>
                {missionHistory.map((mission, index) => (
                  <li key={index}>{mission}</li>
                ))}
              </ul>
            </div>
          )}
          {status === "loading" && <RingsLoaderComponent />}
          {status === "success" && (
            <div className="animation">
              <motion.div
                className="success-animation"
                initial={{ opacity: 0, scale: 0.5 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0 }}
                transition={{ duration: 0.5, exit: { duration: 0.5, delay: 2 }  }}
              >
                <CheckCircleIcon className="text-green-500" />
                <p>Success!</p>
                <p>{message}</p>
              </motion.div>
            </div>
          )}

          {status === "error" && (
            <div className="animation">
              <motion.div
                className="error-animation"
                initial={{ opacity: 0, scale: 0.5 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0 }}
                transition={{ duration: 0.5, exit: { duration: 0.5, delay: 2 } }}
              >
                <XCircleIcon className="text-red-500" />
                <p>Error!</p>
                <p>{message}</p>
              </motion.div>
            </div>
          )}
        </div>

        <div className="map-container">
          <LoadScript
            googleMapsApiKey={process.env.REACT_APP_GOOGLE_MAPS_API_KEY}
          >
            <GoogleMap
              mapContainerStyle={mapContainerStyle}
              center={center}
              zoom={18}
              onClick={onMapClick}
            >
              {markerPosition && <Marker position={markerPosition} />}
            </GoogleMap>
          </LoadScript>
        </div>
      </div>
    </div>
  );
};

export default MissionForm;
