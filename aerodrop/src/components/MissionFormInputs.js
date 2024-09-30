import React from "react";
import { motion } from "framer-motion";

const MissionFormInputs = ({
  latitude,
  longitude,
  setLatitude,
  setLongitude,
  handleSubmit,
}) => {
  return (
    <motion.form
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
  );
};

export default MissionFormInputs;
