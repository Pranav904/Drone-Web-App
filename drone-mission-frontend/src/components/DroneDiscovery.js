import React, { useState } from "react";
import axios from "axios";
import "./DroneDiscovery.css";

// Simulated network IP retrieval - placeholder for actual implementation
const getNetworkIPs = async () => {
  return ["127.0.0.1:5000", "127.0.0.1:5001"];
};

const DroneDiscovery = ({ onDroneSelect }) => {
  const [drones, setDrones] = useState([]);
  const [selectedDrone, setSelectedDrone] = useState(null); // Only one drone can be selected
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
    setSelectedDrone(drone.id);
    onDroneSelect(drone); // Pass the selected drone to the parent immediately
  };

  return (
    <div className="p-4">
      <button
        onClick={scanNetwork}
        disabled={isScanning}
        className="bg-blue-500 text-white px-4 py-2 rounded disabled:bg-gray-400"
      >
        {isScanning ? "Scanning..." : "Scan for Drones"}
      </button>
      {error && <p className="text-red-500 mt-2">{error}</p>}
      <ul className="drone-list">
        {drones.map((drone) => (
          <li
            key={drone.id}
            className={`drone-item ${
              selectedDrone === drone.id ? "selected" : ""
            }`}
          >
            <label className="drone-label">
              <input
                type="radio"
                name="droneSelection"
                value={drone.id}
                checked={selectedDrone === drone.id}
                onChange={() =>
                  handleDroneSelection({ id: drone.id, ip: drone.ip })
                }
              />
              <span className="drone-info">
                <strong>Drone ID:</strong> {drone.id} - <strong>IP:</strong>{" "}
                {drone.ip}
              </span>
            </label>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default DroneDiscovery;
