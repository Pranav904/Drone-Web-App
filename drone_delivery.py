from flask import Flask, request, jsonify
import threading
from pymavlink import mavutil
import time
import math
import logging
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variables
connection_string = 'tcp:127.0.0.1:5763'  # Replace with the appropriate connection string
master = None
connection_lock = threading.Lock()
connection_established = threading.Event()

def initialize_connection():
    global master
    with connection_lock:
        if master is not None:
            try:
                master.close()
            except Exception as e:
                logger.error(f"Error closing existing connection: {str(e)}")
        master = mavutil.mavlink_connection(connection_string)
    
    try:
        master.wait_heartbeat(timeout=10)
        logger.info("Heartbeat received")
        request_data_stream(master, mavutil.mavlink.MAV_DATA_STREAM_POSITION, rate=1)
        logger.info("Requested position data stream")
        connection_established.set()
    except Exception as e:
        logger.error(f"Failed to initialize connection: {str(e)}")
        connection_established.clear()

def get_master():
    global master
    if not connection_established.is_set():
        initialize_connection()
    return master

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth's radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

def wait_for_ack(master, command, timeout=10):
    start_time = time.time()
    while time.time() - start_time < timeout:
        message = master.recv_match(type='COMMAND_ACK', blocking=True, timeout=1)
        if message and message.command == command:
            if message.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                logger.info(f"Command {command} acknowledged")
                return True
            else:
                logger.warning(f"Command {command} failed with result {message.result}")
                return False
    logger.error(f"Timeout waiting for acknowledgment of command {command}")
    return False

def get_current_location(master, timeout=10):
    start_time = time.time()
    while time.time() - start_time < timeout:
        message = master.recv_match(type='GLOBAL_POSITION_INT', blocking=True, timeout=1)
        if message:
            lat = message.lat / 1e7
            lon = message.lon / 1e7
            alt = message.alt / 1000.0
            logger.info(f"Current Location - Latitude: {lat}, Longitude: {lon}, Altitude: {alt} m")
            return lat, lon, alt
    raise TimeoutError("Failed to get current location")

def request_data_stream(master, stream_id, rate=1):
    master.mav.request_data_stream_send(
        master.target_system, master.target_component,
        stream_id, rate, 1
    )

def create_mission_item(seq, command, params, lat=0, lon=0, alt=0):
    return mavutil.mavlink.MAVLink_mission_item_int_message(
        master.target_system, master.target_component,
        seq, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
        command, 0, 1, *params,
        int(lat * 1e7), int(lon * 1e7), alt,
        mavutil.mavlink.MAV_MISSION_TYPE_MISSION
    )

def wait_for_mission_request(master, timeout=10):
    start_time = time.time()
    while time.time() - start_time < timeout:
        message = master.recv_match(type=['MISSION_REQUEST', 'MISSION_REQUEST_INT'], blocking=True, timeout=1)
        if message:
            return message.seq
    raise TimeoutError("Timeout waiting for mission request")

def execute_mission(drop_lat, drop_lon):
    try:
        master = get_master()
        if not connection_established.is_set():
            raise ConnectionError("No connection to the drone")

        master.mav.mission_clear_all_send(master.target_system, master.target_component)
        logger.info("Cleared existing mission")
        time.sleep(1)

        current_lat, current_lon, current_alt = get_current_location(master)

        distance = calculate_distance(current_lat, current_lon, drop_lat, drop_lon)
        if distance > 1000:
            raise ValueError(f"Drop coordinates are {distance:.2f}m away, which exceeds the 1000m limit.")

        mission_items = [
            create_mission_item(0, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, (0, 0, 0, 0), current_lat, current_lon, current_alt),
            create_mission_item(1, mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, (15, 0, 0, 0), alt=10),
            create_mission_item(2, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, (0, 0, 0, 0), drop_lat, drop_lon, 10),
            create_mission_item(3, mavutil.mavlink.MAV_CMD_NAV_LOITER_TIME, (10, 0, 0, 0), drop_lat, drop_lon, 1),
            create_mission_item(4, mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH, (0, 0, 0, 0))
        ]

        master.mav.mission_count_send(master.target_system, master.target_component, len(mission_items), mavutil.mavlink.MAV_MISSION_TYPE_MISSION)
        for i, item in enumerate(mission_items):
            seq = wait_for_mission_request(master)
            if seq != i:
                raise ValueError(f"Unexpected mission request sequence. Expected {i}, got {seq}")
            master.mav.send(item)
            logger.info(f"Sent mission item {i}")

        if not master.recv_match(type='MISSION_ACK', blocking=True, timeout=10):
            raise TimeoutError("Did not receive MISSION_ACK")
        logger.info("Mission uploaded successfully")

        logger.info("Switching to GUIDED mode")
        mode_id = master.mode_mapping()['GUIDED']
        master.set_mode(mode_id)
        if not wait_for_ack(master, mavutil.mavlink.MAV_CMD_DO_SET_MODE):
            raise RuntimeError("Failed to receive acknowledgment for mode switch")

        logger.info("Arming the drone")
        master.arducopter_arm()
        if not wait_for_ack(master, mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM):
            raise RuntimeError("Failed to arm the drone")

        logger.info("Starting the mission")
        master.mav.command_long_send(
            master.target_system, master.target_component,
            mavutil.mavlink.MAV_CMD_MISSION_START,
            0, 0, 0, 0, 0, 0, 0, 0
        )
        if not wait_for_ack(master, mavutil.mavlink.MAV_CMD_MISSION_START):
            raise RuntimeError("Failed to start the mission")

        logger.info("Mission started successfully")
        return True, "Mission started successfully"

    except Exception as e:
        logger.error(f"Error during mission execution: {str(e)}")
        return False, str(e)

@app.route('/drop_coordinates', methods=['POST'])
def receive_coordinates():
    if not connection_established.is_set():
        return jsonify({"error": "No connection to the drone. Please retry the connection and try again."}), 503

    data = request.json
    if not data:
        return jsonify({"error": "No data provided. Please include 'latitude' and 'longitude' in the request body."}), 400

    try:
        drop_lat = float(data.get('latitude'))
        drop_lon = float(data.get('longitude'))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid latitude or longitude format. Please provide valid floating-point numbers."}), 400

    if not (-90 <= drop_lat <= 90) or not (-180 <= drop_lon <= 180):
        return jsonify({"error": "Latitude or longitude out of valid range. Latitude should be between -90 and 90, longitude between -180 and 180."}), 400

    success, message = execute_mission(drop_lat, drop_lon)
    if success:
        return jsonify({"status": "Mission started", "latitude": drop_lat, "longitude": drop_lon}), 200
    else:
        return jsonify({"error": f"Mission execution failed: {message}"}), 500

@app.route('/connection_status', methods=['GET'])
def connection_status():
    return jsonify({"connected": connection_established.is_set()}), 200

@app.route('/retry_connection', methods=['POST'])
def retry_connection():
    initialize_connection()
    if connection_established.is_set():
        return jsonify({"status": "Connection established successfully"}), 200
    else:
        return jsonify({"error": "Failed to establish connection. Please check the drone and connection settings."}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found. Please check the URL and try again."}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed. Please check the allowed HTTP methods for this endpoint."}), 405

@app.errorhandler(500)
def internal_server_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({"error": "Internal server error occurred. Please try again later or contact support."}), 500

if __name__ == '__main__':
    initialize_connection()
    app.run(debug=False, port=5000)