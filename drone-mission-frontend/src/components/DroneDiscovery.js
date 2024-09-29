import React, { useState } from 'react';
import axios from 'axios';

const DroneDiscovery = () => {
  const [drones, setDrones] = useState([]);
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState(null);

  const scanNetwork = async () => {
    setIsScanning(true);
    setError(null);
    try {
      // This would be replaced with your actual network scanning logic
      const ipList = await getNetworkIPs();
      const discoveredDrones = [];

      for (const ip of ipList) {
        try {
          const response = await axios.get(`http://${ip}/drone_info`, { timeout: 2000 });
          if (response.status === 200 && response.data.drone_id) {
            discoveredDrones.push({
              ip: ip,
              id: response.data.drone_id
            });
          }
        } catch (error) {
          // Ignore errors for IPs that don't respond or aren't drones
        }
      }

      setDrones(discoveredDrones);
    } catch (error) {
      setError('Failed to scan network: ' + error.message);
    } finally {
      setIsScanning(false);
    }
  };

  // Simulated network IP retrieval - replace with actual implementation
  const getNetworkIPs = async () => {
    // This is a placeholder. In a real implementation, you might get this from a backend API
    return ["127.0.0.1:5000", "127.0.0.1:5001"];
  };

  return (
    <div className="p-4">
      <button 
        onClick={scanNetwork} 
        disabled={isScanning}
        className="bg-blue-500 text-white px-4 py-2 rounded disabled:bg-gray-400"
      >
        {isScanning ? 'Scanning...' : 'Scan for Drones'}
      </button>
      {error && <p className="text-red-500 mt-2">{error}</p>}
      <ul className="mt-4">
        {drones.map((drone) => (
          <li key={drone.id} className="bg-gray-100 p-2 mb-2 rounded">
            Drone ID: {drone.id} - IP: {drone.ip}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default DroneDiscovery;