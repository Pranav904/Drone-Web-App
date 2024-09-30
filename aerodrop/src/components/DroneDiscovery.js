import React, { useState } from "react";
import axios from "axios";
import "./DroneDiscovery.css";
import LoadingButton from "@mui/lab/LoadingButton";
import RadarIcon from "@mui/icons-material/Radar";

const getNetworkIPs = async () => {
  // This is a placeholder. In a real implementation, you might get this from a backend API
  return ["127.0.0.1:5000", "127.0.0.1:5001"];
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
      const ipList = await getNetworkIPs();
      const discoveredDrones = [];

      for (const ip of ipList) {
        try {
          const response = await axios.get(`http://${ip}/drone_info`, {
            timeout: 2000,
          });
          if (response.status === 200 && response.data.drone_id) {
            discoveredDrones.push({
              ip: ip,
              id: response.data.drone_id,
            });
          }
        } catch (error) {
          // Ignore errors for IPs that don't respond or aren't drones
        }
      }

      setDrones(discoveredDrones);
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
