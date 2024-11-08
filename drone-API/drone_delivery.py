from flask import Flask, request, jsonify
from pymavlink import mavutil
import threading
import time
import math
import logging
from flask_cors import CORS
import socket
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
EARTH_RADIUS = 6371000  # in meters

class DroneController:
    def __init__(self, connection_string, drone_id):
        self.connection_string = connection_string
        self.drone_id = drone_id
        self.connection_lock = threading.Lock()
        self.connection_established = threading.Event()
        self.master = None

    def initialize_connection(self):
        """Initializes MAVLink connection."""
        with self.connection_lock:
            if self.master:
                self.master.close()
            self.master = mavutil.mavlink_connection(self.connection_string)
        
        try:
            self.master.wait_heartbeat(timeout=10)
            logger.info("Heartbeat received; connection established.")
            self.request_data_stream(mavutil.mavlink.MAV_DATA_STREAM_POSITION, rate=1)
            self.connection_established.set()
        except Exception as e:
            logger.error(f"Failed to initialize connection: {str(e)}")
            self.connection_established.clear()

    def get_master(self):
        """Retrieves the MAVLink connection, initializing if necessary."""
        if not self.connection_established.is_set():
            self.initialize_connection()
        return self.master

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculates the Haversine distance between two points on Earth."""
        phi1, phi2 = map(math.radians, [lat1, lat2])
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
        return 2 * EARTH_RADIUS * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def request_data_stream(self, stream_id, rate=1):
        """Requests a data stream from the MAVLink connection."""
        self.master.mav.request_data_stream_send(self.master.target_system, self.master.target_component, stream_id, rate, 1)

    def get_current_location(self, timeout=10):
        """Retrieves the current location of the drone."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            message = self.master.recv_match(type='GLOBAL_POSITION_INT', blocking=True, timeout=1)
            if message:
                lat = message.lat / 1e7
                lon = message.lon / 1e7
                alt = message.alt / 1000.0
                logger.info(f"Current Location - Latitude: {lat}, Longitude: {lon}, Altitude: {alt} m")
                return lat, lon, alt
        raise TimeoutError("Failed to get current location")

    def execute_mission(self, drop_lat, drop_lon):
        """Executes a predefined mission with given drop coordinates."""
        try:
            if not self.connection_established.is_set():
                raise ConnectionError("No connection to the drone")

            # Clear any existing mission
            self.master.mav.mission_clear_all_send(self.master.target_system, self.master.target_component)
            time.sleep(1)

            # Get the current location and check distance to the drop point
            current_lat, current_lon, current_alt = self.get_current_location()
            distance = self.calculate_distance(current_lat, current_lon, drop_lat, drop_lon)
            if distance > 1000:
                raise ValueError(f"Drop coordinates are {distance:.2f}m away, exceeding the 1000m limit.")

            # Define mission items (simplified here)
            mission_items = [
                self.create_mission_item(0, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, current_lat, current_lon, current_alt),
                self.create_mission_item(1, mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, alt=10),
                self.create_mission_item(2, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, drop_lat, drop_lon, 10),
                self.create_mission_item(3, mavutil.mavlink.MAV_CMD_NAV_LOITER_TIME, drop_lat, drop_lon, 1),
                self.create_mission_item(4, mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH)
            ]

            # Upload mission
            self.upload_mission(mission_items)
            # Arm and start mission
            self.set_mode_and_arm()
            self.start_mission()
            return True, "Mission started successfully"
        except Exception as e:
            logger.error(f"Error during mission execution: {str(e)}")
            return False, str(e)

    def create_mission_item(self, seq, command, lat=0, lon=0, alt=0, params=(0, 0, 0, 0)):
        """Creates a MAVLink mission item."""
        return mavutil.mavlink.MAVLink_mission_item_int_message(
            self.master.target_system, self.master.target_component,
            seq, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
            command, 0, 1, *params,
            int(lat * 1e7), int(lon * 1e7), alt,
            mavutil.mavlink.MAV_MISSION_TYPE_MISSION
        )

    def upload_mission(self, mission_items):
        """Uploads mission items to the drone."""
        self.master.mav.mission_count_send(self.master.target_system, self.master.target_component, len(mission_items))
        for i, item in enumerate(mission_items):
            self.wait_for_mission_request(i)
            self.master.mav.send(item)

        if not self.master.recv_match(type='MISSION_ACK', blocking=True, timeout=10):
            raise TimeoutError("Did not receive MISSION_ACK")

    def set_mode_and_arm(self):
        """Sets the drone mode to GUIDED and arms it."""
        mode_id = self.master.mode_mapping()['GUIDED']
        self.master.set_mode(mode_id)
        self.wait_for_ack(mavutil.mavlink.MAV_CMD_DO_SET_MODE)
        self.master.arducopter_arm()
        self.wait_for_ack(mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM)

    def start_mission(self):
        """Starts the mission by sending the MISSION_START command."""
        self.master.mav.command_long_send(
            self.master.target_system, self.master.target_component,
            mavutil.mavlink.MAV_CMD_MISSION_START, 0, 0, 0, 0, 0, 0, 0, 0
        )
        self.wait_for_ack(mavutil.mavlink.MAV_CMD_MISSION_START)

    def wait_for_ack(self, command, timeout=10):
        """Waits for command acknowledgment."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            message = self.master.recv_match(type='COMMAND_ACK', blocking=True, timeout=1)
            if message and message.command == command:
                return message.result == mavutil.mavlink.MAV_RESULT_ACCEPTED
        raise TimeoutError(f"Timeout waiting for acknowledgment of command {command}")

    def wait_for_mission_request(self, seq, timeout=10):
        """Waits for mission request."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            message = self.master.recv_match(type=['MISSION_REQUEST', 'MISSION_REQUEST_INT'], blocking=True, timeout=1)
            if message and message.seq == seq:
                return message.seq
        raise TimeoutError("Timeout waiting for mission request")

class DroneAPI:
    def __init__(self, connection_string, drone_id):
        self.drone_controller = DroneController(connection_string, drone_id)
        self.app = Flask(__name__)
        CORS(self.app)
        self.setup_routes()

    def setup_routes(self):
        @self.app.route('/drone_info', methods=['GET'])
        def get_drone_info():
            """Retrieves drone information."""
            if not self.drone_controller.connection_established.is_set():
                return jsonify({"error": "No connection to the drone. Retry connection."}), 503

            try:
                # lat, lon, alt = self.drone_controller.get_current_location()
                lat, lon , alt = 0, 0, 0
                return jsonify({"drone_id": self.drone_controller.drone_id, "latitude": lat, "longitude": lon, "altitude": alt}), 200
            except Exception as e:
                logger.error(f"Error getting drone information: {str(e)}")
                return jsonify({"error": f"Failed to get drone information: {str(e)}"}), 500

        @self.app.route('/drop_coordinates', methods=['POST'])
        def receive_coordinates():
            """Receives drop coordinates and executes a mission."""
            if not self.drone_controller.connection_established.is_set():
                return jsonify({"error": "No connection to the drone. Retry connection."}), 503

            data = request.json
            if not data or data.get('drone_id') != self.drone_controller.drone_id:
                return jsonify({"error": f"Invalid drone ID. Expected {self.drone_controller.drone_id}. Got {data.get('drone_id')}"}), 400

            try:
                drop_lat, drop_lon = float(data['latitude']), float(data['longitude'])
                if not (-90 <= drop_lat <= 90) or not (-180 <= drop_lon <= 180):
                    return jsonify({"error": "Invalid latitude/longitude range."}), 400

                success, message = self.drone_controller.execute_mission(drop_lat, drop_lon)
                status = "Mission started" if success else f"Mission execution failed: {message}"
                return jsonify({"status": status, "latitude": drop_lat, "longitude": drop_lon}), 200 if success else 500
            except ValueError:
                return jsonify({"error": "Invalid latitude or longitude format."}), 400

        @self.app.route('/connection_status', methods=['GET'])
        def connection_status():
            """Checks drone connection status."""
            return jsonify({"connected": self.drone_controller.connection_established.is_set()}), 200

    def find_available_port(self, start_port):
        """Finds the next available port starting from the given port number."""
        port = start_port
        while True:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                if sock.connect_ex(('localhost', port)) != 0:  # Check if the port is available
                    return port
                port += 1

    def run(self, debug=False, port=5000):
        """Runs the Flask app, finding an available port if necessary."""
        self.drone_controller.initialize_connection()
        available_port = self.find_available_port(port)
        logger.info(f"Starting Flask server on port: {available_port}")
        self.app.run(host="0.0.0.0", debug=debug, port=available_port)

if __name__ == '__main__':
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Drone Controller API')
    parser.add_argument('--connection', type=str, 
                       default='tcp:127.0.0.1:5762',
                       help='Connection string (e.g., tcp:127.0.0.1:5762)')
    parser.add_argument('--drone-id', type=str,
                       default='DRONE_001',
                       help='Unique drone identifier')
    parser.add_argument('--port', type=int,
                       default=5000,
                       help='Port for the Flask server')
    parser.add_argument('--debug', action='store_true',
                       help='Run Flask in debug mode')

    args = parser.parse_args()

    # Log the configuration
    logger.info(f"Starting drone controller with:")
    logger.info(f"Connection string: {args.connection}")
    logger.info(f"Drone ID: {args.drone_id}")
    logger.info(f"Server port: {args.port}")
    logger.info(f"Debug mode: {args.debug}")

    try:
        api = DroneAPI(args.connection, args.drone_id)
        api.run(debug=args.debug, port=args.port)
    except Exception as e:
        logger.error(f"Failed to start drone controller: {str(e)}")
        exit(1)