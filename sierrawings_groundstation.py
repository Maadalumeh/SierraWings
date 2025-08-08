
import time
import sys
import threading
from pymavlink import mavutil

class MAVLinkManager:
    def __init__(self):
        self.master = None
        self.running = False

    def connect(self):
        try:
            # Try USB ports
            print("Searching for USB connection...")
            for i in range(20):
                try:
                    port = f"COM{i}" if sys.platform.startswith("win") else f"/dev/ttyUSB{i}"
                    self.master = mavutil.mavlink_connection(port, baud=57600)
                    self.master.wait_heartbeat(timeout=5)
                    print(f"✅ Connected to MAVLink device via USB: {port}")
                    return
                except:
                    continue

            # If USB not found, try UDP
            print("Trying UDP 0.0.0.0:14550...")
            self.master = mavutil.mavlink_connection("udp:0.0.0.0:14550")
            self.master.wait_heartbeat(timeout=10)
            print("✅ Connected to MAVLink device via UDP")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            sys.exit(1)

    def listen(self):
        while self.running:
            try:
                msg = self.master.recv_match(blocking=True, timeout=1)
                if not msg:
                    continue

                if msg.get_type() == "HEARTBEAT":
                    print(f"[MODE] {mavutil.mode_string_v10(msg)}")
                elif msg.get_type() == "SYS_STATUS":
                    print(f"[BATTERY] {msg.voltage_battery/1000.0}V | {msg.battery_remaining}%")
                elif msg.get_type() == "GLOBAL_POSITION_INT":
                    print(f"[GPS] Lat: {msg.lat/1e7}, Lon: {msg.lon/1e7}, Alt: {msg.relative_alt/100.0}m")
                elif msg.get_type() == "STATUSTEXT":
                    print(f"[ALERT] {msg.text}")
            except Exception as e:
                print(f"[Listen Error] {e}")

    def send_command(self, command):
        if command == "arm":
            self.master.arducopter_arm()
            print("✅ Drone armed")
        elif command == "disarm":
            self.master.arducopter_disarm()
            print("✅ Drone disarmed")
        elif command == "takeoff":
            self.master.mav.command_long_send(
                self.master.target_system, self.master.target_component,
                mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
                0, 0, 0, 0, 0, 0, 0, 10)
            print("🚁 Takeoff command sent")
        elif command == "land":
            self.master.mav.command_long_send(
                self.master.target_system, self.master.target_component,
                mavutil.mavlink.MAV_CMD_NAV_LAND,
                0, 0, 0, 0, 0, 0, 0, 0)
            print("🛬 Land command sent")
        elif command == "rtl":
            self.set_mode("RTL")
        else:
            print("❌ Unknown command")

    def set_mode(self, mode):
        mode_id = self.master.mode_mapping().get(mode)
        if mode_id is None:
            print(f"❌ Unknown mode: {mode}")
            return

        self.master.mav.set_mode_send(
            self.master.target_system,
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            mode_id)
        print(f"🔄 Mode set to {mode}")

    def start(self):
        self.running = True
        threading.Thread(target=self.listen, daemon=True).start()

    def stop(self):
        self.running = False

if __name__ == "__main__":
    manager = MAVLinkManager()
    manager.connect()
    manager.start()

    try:
        while True:
            cmd = input("Enter command (arm, disarm, takeoff, land, rtl, mode:<MODE>, exit): ").strip().lower()
            if cmd == "exit":
                manager.stop()
                break
            elif cmd.startswith("mode:"):
                mode = cmd.split(":")[1].upper()
                manager.set_mode(mode)
            else:
                manager.send_command(cmd)
    except KeyboardInterrupt:
        manager.stop()
        print("
⛔ Exiting...")
