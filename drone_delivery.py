from flask import Flask, request, jsonify
from pymavlink import mavutil
import time
import threading

app = Flask(__name__)

# Global variable to store the mavlink connection
master = None

# Function to wait for acknowledgment of a command
def wait_for_ack(command, timeout=5):  # Added timeout
    start_time = time.time()
    while time.time() - start_time < timeout:
        message = master.recv_match(type='COMMAND_ACK', blocking=True)
        if message and message.to_dict()['command'] == command:
            return message.to_dict()['result'] == mavutil.mavlink.MAV_RESULT_ACCEPTED
    return False  # Timeout

# Function to get the current location of the drone
def get_current_location():
    while True:
        message = master.recv_match(type='GLOBAL_POSITION_INT', blocking=True)
        if message:
            message = message.to_dict()
            latitude = message['lat'] / 1e7
            longitude = message['lon'] / 1e7
            altitude = message['alt'] / 1000.0
            return latitude, longitude, altitude

# Function to request data stream from the drone
def request_data_stream(stream_id, rate=1):
    master.mav.request_data_stream_send(
        master.target_system,
        master.target_component,
        stream_id,
        rate,
        1
    )

# Function to initialize the drone connection
def init_drone_connection():
    global master
    connection_string = 'tcp:127.0.0.1:5763'  # Replace with the appropriate connection string
    master = mavutil.mavlink_connection(connection_string)
    master.wait_heartbeat()
    print("Heartbeat received")
    request_data_stream(mavutil.mavlink.MAV_DATA_STREAM_POSITION, rate=1)

# Function to wait for mission request
def wait_for_mission_request(master, timeout=5):  # Added timeout
    start_time = time.time()
    while time.time() - start_time < timeout:
        message = master.recv_match(type=['MISSION_REQUEST', 'MISSION_REQUEST_INT'], blocking=True)
        if message is not None:
            return message.seq
    return None  # Timeout

# Function to send a mission item to the drone
def send_mission_items(mission_items):
    for i in range(len(mission_items)):
        seq = wait_for_mission_request(master)
        if seq is None:
            print(f"Error: Timeout waiting for request for item {i}")
            break
        elif seq != i:
            print(f"Error: Expected request for item {i}, but got request for item {seq}")
            break

        master.mav.send(mission_items[i])
        print(f"Sent mission item {i}")

@app.route('/send_coordinates', methods=['POST'])
def send_coordinates():
    data = request.json
    drop_lat = data.get('latitude')
    drop_lon = data.get('longitude')

    if not all([drop_lat, drop_lon]):
        return jsonify({"error": "Missing coordinates"}), 400

    try:
        # Clear existing mission
        master.mav.mission_clear_all_send(master.target_system, master.target_component)
        time.sleep(1)  # Brief pause after clearing

        # Get current location
        current_lat, current_lon, current_alt = get_current_location()

        # Create new mission (using helper function for readability)
        def create_mission_item(seq, command, params, lat=0, lon=0, alt=0):
            return mavutil.mavlink.MAVLink_mission_item_int_message(
                master.target_system,
                master.target_component,
                seq,
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                command,
                0, 1, *params,
                int(lat * 1e7), int(lon * 1e7), alt,
                mavutil.mavlink.MAV_MISSION_TYPE_MISSION
            )

        mission_items = [
            create_mission_item(0, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, (0, 0, 0, 0), current_lat, current_lon, current_alt),
            create_mission_item(1, mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, (15, 0, 0, 0), alt=10),
            create_mission_item(2, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, (0, 0, 0, 0), drop_lat, drop_lon, 10),
            create_mission_item(3, mavutil.mavlink.MAV_CMD_NAV_LOITER_TIME, (10, 0, 0, 0), drop_lat, drop_lon, 1),
            create_mission_item(4, mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH, (0, 0, 0, 0))
        ]

        # Send mission count
        master.mav.mission_count_send(master.target_system, master.target_component, len(mission_items), mavutil.mavlink.MAV_MISSION_TYPE_MISSION)
        print(f"Sent mission count: {len(mission_items)}")

        # Send each mission item
        send_mission_items(mission_items)

        # Wait for mission acknowledgment (with timeout)
        if not wait_for_ack(mavutil.mavlink.MAV_CMD_MISSION_COUNT):
            return jsonify({"error": "Mission upload failed: No acknowledgment received"}), 500

        # Switch to GUIDED mode (with timeout)
        mode_id = master.mode_mapping()['GUIDED']
        master.set_mode(mode_id)
        if not wait_for_ack(mavutil.mavlink.MAV_CMD_DO_SET_MODE):
            return jsonify({"error": "Failed to switch to GUIDED mode"}), 500

        # Arm the drone (with timeout)
        master.arducopter_arm()
        if not wait_for_ack(mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM):
            return jsonify({"error": "Failed to arm the drone"}), 500

        # Start the mission (with timeout)
        master.mav.command_long_send(
            master.target_system,
            master.target_component,
            mavutil.mavlink.MAV_CMD_MISSION_START,
            0, 0, 0, 0, 0, 0, 0, 0
        )
        if wait_for_ack(mavutil.mavlink.MAV_CMD_MISSION_START):
            return jsonify({"message": "Mission successfully started"}), 200
        else:
            return jsonify({"error": "Failed to start the mission"}), 500

    except Exception as e:
        return jsonify({"error": f"Mission failed due to: {str(e)}"}), 500

if __name__ == '__main__':
    # Start the drone connection in a separate thread
    drone_thread = threading.Thread(target=init_drone_connection)
    drone_thread.daemon = True  # Allow main thread to exit even if drone thread is running
    drone_thread.start()

    # Wait for the drone connection to be established (you might need to adjust this)
    time.sleep(5)

    # Start the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)