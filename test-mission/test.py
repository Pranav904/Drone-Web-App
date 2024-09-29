from pymavlink import mavutil
import time

drop_lat = -35.3630029
drop_lon = 149.167257

# Function to wait for acknowledgment of a command
def wait_for_ack(master, command):
    while True:
        message = master.recv_match(type='COMMAND_ACK', blocking=True)
        message = message.to_dict()
        if message['command'] == command:
            if message['result'] == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                print(f"Command {command} acknowledged")
                return True
            else:
                print(f"Command {command} failed with result {message['result']}")
                return False

# Function to wait for mission request
def wait_for_mission_request(master):
    while True:
        message = master.recv_match(type=['MISSION_REQUEST', 'MISSION_REQUEST_INT'], blocking=True)
        if message is not None:
            return message.seq

# Function to get the current location of the drone
def get_current_location(master):
    # Request GLOBAL_POSITION_INT message
    while True:
        message = master.recv_match(type='GLOBAL_POSITION_INT', blocking=True)
        if message:
            message = message.to_dict()

            # Extract latitude, longitude, and altitude
            latitude = message['lat'] / 1e7  # Scale down to degrees
            longitude = message['lon'] / 1e7  # Scale down to degrees
            altitude = message['alt'] / 1000.0  # Altitude in meters (from millimeters)

            print(f"Current Location - Latitude: {latitude}, Longitude: {longitude}, Altitude: {altitude} m")
            return latitude, longitude, altitude

# Function to request data streams from the drone
def request_data_stream(master, stream_id, rate=1):
    master.mav.request_data_stream_send(
        master.target_system,
        master.target_component,
        stream_id,  # MAV_DATA_STREAM
        rate,  # Rate in Hz (times per second)
        1  # Start streaming
    )

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

# Connect to the drone
connection_string = 'tcp:127.0.0.1:5763'  # Replace with the appropriate connection string
master = mavutil.mavlink_connection(connection_string)

# Wait for a heartbeat before sending any commands
master.wait_heartbeat()
print("Heartbeat received")

# Request the position data stream at 1Hz (1 message per second)
request_data_stream(master, mavutil.mavlink.MAV_DATA_STREAM_POSITION, rate=1)
print("Requested position data stream...")

# Clear any existing mission
master.mav.mission_clear_all_send(master.target_system, master.target_component)
print("Cleared existing mission")

current_lat, current_lon, current_alt = get_current_location(master)

# Send mission items (example 5 waypoints)
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
for i in range(len(mission_items)):
    # Wait for mission request
    seq = wait_for_mission_request(master)
    if seq != i:
        print(f"Error: Expected request for item {i}, but got request for item {seq}")
        break
    
    # Send mission item
    master.mav.send(mission_items[i])
    print(f"Sent mission item {i}")

# Wait for mission acknowledgment
ack = master.recv_match(type='MISSION_ACK', blocking=True, timeout=10)
if ack is None:
    print("Error: Did not receive MISSION_ACK")
else:
    print(f"Mission upload complete with result: {ack.type}")

# Switch to AUTO mode
print("Switching to GUIDED mode")
mode_id = master.mode_mapping()['GUIDED']
master.set_mode(mode_id)
wait_for_ack(master, mavutil.mavlink.MAV_CMD_DO_SET_MODE)

time.sleep(5)  # Wait for the drone to switch to AUTO mode

# Arm the drone
print("Arming the drone")
master.arducopter_arm()
wait_for_ack(master, mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM)

# Start the mission
print("Starting the mission")
master.mav.command_long_send(
    master.target_system,
    master.target_component,
    mavutil.mavlink.MAV_CMD_MISSION_START,
    0,  # confirmation
    0, 0, 0, 0, 0, 0, 0  # params 1-7
)
wait_for_ack(master, mavutil.mavlink.MAV_CMD_MISSION_START)

print("Script completed")