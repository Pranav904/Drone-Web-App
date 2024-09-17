from flask import Flask, request, jsonify
from pymavlink import mavutil
import time
import threading

app = Flask(__name__)

# Global variable to store the mavlink connection
master = None

# Function to wait for acknowledgment of a command
def wait_for_ack(command):
    while True:
        message = master.recv_match(type='COMMAND_ACK', blocking=True)
        message = message.to_dict()
        if message['command'] == command:
            if message['result'] == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                return True
            else:
                return False

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
        stream_id,  # MAV_DATA_STREAM
        rate,  # Rate in Hz (times per second)
        1  # Start streaming
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
def wait_for_mission_request(master):
    while True:
        message = master.recv_match(type=['MISSION_REQUEST', 'MISSION_REQUEST_INT'], blocking=True)
        if message is not None:
            return message.seq

# Function to send a mission item to the drone
def send_mission_items(mission_items):
    # Send each mission item
    for i in range(len(mission_items)):
        # Wait for mission request
        seq = wait_for_mission_request(master)
        if seq != i:
            print(f"Error: Expected request for item {i}, but got request for item {seq}")
            break
        
        # Send mission item
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
        time.sleep(1)

        # Get current location
        current_lat, current_lon, current_alt = get_current_location()

        # Create new mission
        mission_items = [
            mavutil.mavlink.MAVLink_mission_item_int_message(
                master.target_system,  # target_system (autopilot system id)
                master.target_component,  # target_component (autopilot component id)
                0,  # sequence number
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,  # frame
                mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,  # command type
                0,  # current (not the current mission item)
                1,  # autocontinue
                0, 0, 0, 0,  # param1, param2, param3, param4
                int(current_lat * 1e7),  # latitude (scaled to int32)
                int(current_lon * 1e7),  # longitude (scaled to int32)
                current_alt,  # altitude
                mavutil.mavlink.MAV_MISSION_TYPE_MISSION,  # mission_type
            ),
            mavutil.mavlink.MAVLink_mission_item_int_message(
                master.target_system,  # target_system (autopilot system id)
                master.target_component,  # target_component (autopilot component id)
                1,  # sequence number
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,  # frame
                mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,  # command type
                0,  # current (not the current mission item)
                1,  # autocontinue
                15, 0, 0, 0,  # param1 (pitch), param2, param3, param4
                0,  # latitude (scaled to int32, set to zero for takeoff)
                0,  # longitude (scaled to int32, set to zero for takeoff)
                10,  # altitude
                mavutil.mavlink.MAV_MISSION_TYPE_MISSION,  # mission_type
            ),
            mavutil.mavlink.MAVLink_mission_item_int_message(
                master.target_system,  # target_system (autopilot system id)
                master.target_component,  # target_component (autopilot component id)
                2,  # sequence number
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,  # frame
                mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,  # command type
                0,  # current (not the current mission item)
                1,  # autocontinue
                0, 0, 0, 0,  # param1, param2, param3, param4
                int(drop_lat * 1e7),  # latitude (scaled by 1e7 to int32)
                int(drop_lon * 1e7),  # longitude (scaled by 1e7 to int32)
                10,  # altitude
                mavutil.mavlink.MAV_MISSION_TYPE_MISSION,  # mission_type
            ),
            mavutil.mavlink.MAVLink_mission_item_int_message(
                master.target_system,  # target_system (autopilot system id)
                master.target_component,  # target_component (autopilot component id)
                3,  # sequence number
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,  # frame
                mavutil.mavlink.MAV_CMD_NAV_LOITER_TIME,  # command type
                0,  # current (not the current mission item)
                1,  # autocontinue
                10, 0, 0, 0,  # param1 (loiter time), param2, param3, param4
                int(drop_lat * 1e7),  # latitude (scaled by 1e7 to int32)
                int(drop_lon * 1e7),  # longitude (scaled by 1e7 to int32)
                1,  # altitude
                mavutil.mavlink.MAV_MISSION_TYPE_MISSION,  # mission_type
            ),
            mavutil.mavlink.MAVLink_mission_item_int_message(
                master.target_system,  # target_system (autopilot system id)
                master.target_component,  # target_component (autopilot component id)
                4,  # sequence number
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,  # frame
                mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH,  # command type
                0,  # current (not the current mission item)
                1,  # autocontinue
                0, 0, 0, 0,  # param1, param2, param3, param4
                0,  # latitude (for RTL, set to zero)
                0,  # longitude (for RTL, set to zero)
                0,  # altitude (for RTL, set to zero)
                mavutil.mavlink.MAV_MISSION_TYPE_MISSION,  # mission_type
            ),
        ]

        # Send mission count
        master.mav.mission_count_send(master.target_system, master.target_component, len(mission_items), mavutil.mavlink.MAV_MISSION_TYPE_MISSION)
        print(f"Sent mission count: {len(mission_items)}")

        # Send each mission item


        # Wait for mission acknowledgment
        ack = master.recv_match(type='MISSION_ACK', blocking=True, timeout=10)
        if ack is None:
            return jsonify({"error": "Mission upload failed: No acknowledgment received"}), 500

        # Switch to GUIDED mode
        mode_id = master.mode_mapping()['GUIDED']
        master.set_mode(mode_id)
        if not wait_for_ack(mavutil.mavlink.MAV_CMD_DO_SET_MODE):
            return jsonify({"error": "Failed to switch to GUIDED mode"}), 500

        # Arm the drone
        master.arducopter_arm()
        if not wait_for_ack(mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM):
            return jsonify({"error": "Failed to arm the drone"}), 500

        # Start the mission
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
    drone_thread.start()

    # Wait for the drone connection to be established
    time.sleep(5)

    # Start the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)