// /src/app/api/scan/route.js
import axios from "axios";

const networkRange = "192.168.62.247"; // Replace with your network range
const portStartRange = 5000;
const portEndRange = 5050;
const droneEndpoint = "/drone_info"; // Known endpoint on each drone

export async function GET(req) {
  const activeDrones = [];

  const checkDrone = async (ip) => {
    try {
      console.log(`http://${ip}${droneEndpoint}`);
      const response = await axios.get(`http://${ip}${droneEndpoint}`, {
        timeout: 2000,
      });
      if (response.status === 200 && response.data.drone_id) {
        activeDrones.push({ ip, id: response.data.drone_id });
      }
    } catch (error) {
      // Ignore errors (timeout, connection refused, etc.)
    }
  };

  const checkPromises = [];
  for (let i = portStartRange; i <= portEndRange; i++) {
    const ip = `${networkRange}:${i}`;
    checkPromises.push(checkDrone(ip));
  }

  await Promise.all(checkPromises);

  return new Response(JSON.stringify({ activeDrones }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}
