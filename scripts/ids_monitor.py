import paho.mqtt.client as mqtt
import os

# ==============================
# CONFIGURATION
# ==============================

TEMP_THRESHOLD = 45
HUMIDITY_THRESHOLD = 70

TEMP_DELTA = 10
HUMIDITY_DELTA = 15

WINDOW_SIZE = 5
DEVIATION_THRESHOLD = 15

SNORT_ALERT_FILE = "/var/log/snort/alert"

# ==============================
# STATE VARIABLES
# ==============================

previous_temp = None
previous_humidity = None

temp_window = []
humidity_window = []

last_snort_alert = ""   # To avoid duplicate printing

# ==============================
# SNORT ALERT READER
# ==============================

def check_snort_alerts():
    global last_snort_alert

    if os.path.exists(SNORT_ALERT_FILE):
        with open(SNORT_ALERT_FILE, "r") as f:
            lines = f.readlines()
            if lines:
                latest = lines[-1].strip()

                if latest != last_snort_alert:
                    print("\n==============================")
                    print("[SNORT NETWORK ALERT]")
                    print(latest)
                    print("==============================\n")

                    last_snort_alert = latest

# ==============================
# MQTT CALLBACKS
# ==============================

def on_connect(client, userdata, flags, rc):
    print("CONNECTED to broker, rc =", rc)
    client.subscribe("iot/#")

def on_message(client, userdata, msg):
    global previous_temp, previous_humidity
    global temp_window, humidity_window

    # 🔹 Check network alerts from Snort
    check_snort_alerts()

    value = int(msg.payload.decode())

    # ==============================
    # TEMPERATURE SECTION
    # ==============================
    if msg.topic == "iot/temperature":
        print("Temperature:", value)

        # Threshold detection
        if value > TEMP_THRESHOLD:
            print("ALERT: High Temperature!")

        #  Sudden change detection
        if previous_temp is not None:
            if abs(value - previous_temp) > TEMP_DELTA:
                print("ALERT: Sudden Temperature Change!")

        #  Moving average detection
        temp_window.append(value)
        if len(temp_window) > WINDOW_SIZE:
            temp_window.pop(0)

        avg_temp = sum(temp_window) / len(temp_window)

        if abs(value - avg_temp) > DEVIATION_THRESHOLD:
            print("ALERT: Temperature Deviation from Normal Pattern!")

        previous_temp = value

    # ==============================
    # HUMIDITY SECTION
    # ==============================
    elif msg.topic == "iot/humidity":
        print("Humidity:", value)

        #  Threshold detection
        if value > HUMIDITY_THRESHOLD:
            print("ALERT: High Humidity!")

        # Sudden change detection
        if previous_humidity is not None:
            if abs(value - previous_humidity) > HUMIDITY_DELTA:
                print("ALERT: Sudden Humidity Change!")

        # Moving average detection
        humidity_window.append(value)
        if len(humidity_window) > WINDOW_SIZE:
            humidity_window.pop(0)

        avg_humidity = sum(humidity_window) / len(humidity_window)

        if abs(value - avg_humidity) > DEVIATION_THRESHOLD:
            print("ALERT: Humidity Deviation from Normal Pattern!")

        previous_humidity = value

# ==============================
# START MQTT CLIENT
# ==============================

client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)

print("Hybrid Lightweight IoT IDS Started...")
client.loop_forever()


