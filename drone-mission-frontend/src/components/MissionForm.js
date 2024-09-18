import React, { useState, useRef } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import RingsLoaderComponent from './RingsLoaderComponent';
import './MissionForm.css';
import { CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/solid' // Assuming you're using Heroicons

const MissionForm = () => {
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [status, setStatus] = useState("");
  const [message, setMessage] = useState("");
  const [showForm, setShowForm] = useState(true);
  const [missionHistory, setMissionHistory] = useState([]); 
  const formRef = useRef(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus("loading");

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
        setMessage(`Mission started successfully at (${latitude}, ${longitude})`);
        setShowForm(false); 
        setTimeout(() => {
          setMissionHistory([...missionHistory, message]); 
          setStatus(""); 
          setShowForm(true); 
        }, 2000); 
      }
    } catch (error) {
      setStatus("error");
      setMessage(error.response?.data?.error || "Failed to start the mission.");
      setShowForm(false);
      setTimeout(() => {
        setStatus("");
        setShowForm(true);
      }, 2000);
    }
  };

  return (
    <div className="mission-form-container">
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
              className="submit-button"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Start Mission
            </motion.button>
          </motion.form>
        )}
      </AnimatePresence>

      {status === "loading" && <RingsLoaderComponent />}

      {status === "success" && (
        <motion.div
          className="success-animation"
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0 }}
          transition={{ duration: 0.5 }}
        >
          <CheckCircleIcon className="h-10 w-10 text-green-500" /> {/* Success icon */}
          <p>Success!</p>
        </motion.div>
      )}

      {status === "error" && (
        <motion.div
          className="error-animation"
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0 }}
          transition={{ duration: 0.5 }}
        >
          <XCircleIcon className="h-10 w-10 text-red-500" /> {/* Error icon */}
          <p>Error!</p>
        </motion.div>
      )}

      <div className="mission-history">
        <h3>Mission History:</h3>
        <ul>
          {missionHistory.map((item, index) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default MissionForm;