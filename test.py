from pymavlink import mavutil
import time

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

# Connect to the drone
connection_string = 'tcp:127.0.0.1:5763'  # Replace with the appropriate connection string
master = mavutil.mavlink_connection(connection_string)

# Wait for a heartbeat before sending any commands
master.wait_heartbeat()
print("Heartbeat received")

# Clear any existing mission
master.mav.mission_clear_all_send(master.target_system, master.target_component)
print("Cleared existing mission")

# Send mission items (example 5 waypoints)
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
        int(-35.3352 * 1e7),  # latitude (scaled to int32)
        int(149.1652416 * 1e7),  # longitude (scaled to int32)
        587.13,  # altitude
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
        int(-35.3619967 * 1e7),  # latitude (scaled by 1e7 to int32)
        int(149.166027900 * 1e7),  # longitude (scaled by 1e7 to int32)
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
        int(-35.3619967 * 1e7),  # latitude (scaled by 1e7 to int32)
        int(149.166027900 * 1e7),  # longitude (scaled by 1e7 to int32)
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