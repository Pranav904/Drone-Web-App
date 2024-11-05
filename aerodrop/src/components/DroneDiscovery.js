import React, { useState } from "react";
import axios from "axios";
import "./DroneDiscovery.css";
import LoadingButton from "@mui/lab/LoadingButton";
import RadarIcon from "@mui/icons-material/Radar";

const getDrones = async () => {
  try {
    const response = await axios.get("/api/scan");
    return response.data.activeDrones;
  } catch (error) {
    console.error("Error fetching IPs:", error);
    return [];
  }
};


const DroneDiscovery = ({ onDroneSelect }) => {
  const [drones, setDrones] = useState([]);
  const [selectedDrone, setSelectedDrone] = useState(null);
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState(null);

  const scanNetwork = async () => {
    setIsScanning(true);
    setError(null);
    try {
      const droneList = await getDrones();
      setDrones(droneList);
    } catch (error) {
      setError("Failed to scan network: " + error.message);
    } finally {
      setIsScanning(false);
    }
  };

  const handleDroneSelection = (drone) => {
    if (selectedDrone && selectedDrone.id === drone.id) {
      setSelectedDrone(null);
    } else {
      setSelectedDrone(drone);
    }
    onDroneSelect(drone);
  };

  return (
    <div className="p-4">
      <LoadingButton
        size="medium"
        onClick={scanNetwork}
        endIcon={<RadarIcon />}
        loading={isScanning}
        loadingPosition="end"
        variant="contained"
        style={{ color: "white" }}
      >
        {isScanning ? "Scanning..." : "Scan for Drones"}
      </LoadingButton>
      {error && <p className="text-red-500 mt-2">{error}</p>}

      <ul className="drone-list mt-4">
        {drones.map((drone) => (
          <li
            key={drone.id}
            className={`drone-item ${
              selectedDrone && selectedDrone.id === drone.id ? "selected" : ""
            }`}
            onClick={() => handleDroneSelection(drone)}
          >
            <label className="drone-label">
              <input
                type="radio"
                name="droneSelection"
                value={drone.id}
                checked={selectedDrone && selectedDrone.id === drone.id}
                onChange={() => handleDroneSelection(drone)}
              />
              <span className="drone-info">
                Drone ID: {drone.id} - IP: {drone.ip}
              </span>
            </label>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default DroneDiscovery;
