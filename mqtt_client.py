import ssl
import paho.mqtt.client as mqtt
from threading import Thread, Event
import json
from datetime import datetime, timedelta, timezone

# AWS IoT Core settings
AWS_ENDPOINT = "a2hnk4whzd8l7x-ats.iot.ap-southeast-1.amazonaws.com"
PORT = 8883
CLIENT_ID = "vision_web_aws"
SUB_TOPIC = "/device2server"
PUB_TOPIC = "/server2device"

CA_CERT = "aws_package/root_cert_auth.crt"
CLIENT_CERT = "aws_package/client.crt"
CLIENT_KEY = "aws_package/client.key"

ACK_CODE = "ACK"
NACK_CODE = "NACK"

mqtt_client = None  
mqtt_thread = None  
stop_event = Event() 
device_status_event = Event()
upload_raw_data_event = Event()

vietnam_timezone = timezone(timedelta(hours=7))

chunk_total = 0
received_chunks = {}
sorted_data = []

device_id = None
is_device_connected = False
is_mqtt_broker_connected = False
is_upload_header_received = False

def get_sorted_data():
    global sorted_data
    return sorted_data

def get_mqtt_broker_status():
    global is_mqtt_broker_connected
    return is_mqtt_broker_connected
    
def set_mqtt_broker_status(status):
    global is_mqtt_broker_connected
    is_mqtt_broker_connected = status
    print(f"SET MQTT Broker status: {is_mqtt_broker_connected}")

def get_device_id():
    global device_id
    return device_id

def set_device_id(id):
    global device_id
    device_id = id

def set_device_status(status):
    global is_device_connected
    is_device_connected = status
    if status:
        device_status_event.set()
    else:
        device_status_event.clear()
    print(f"SET Device status: {is_device_connected}")

def get_device_status():
    global is_device_connected
    return is_device_connected


def on_message(client, userdata, message):
    global chunk_total, received_chunks, is_upload_header_received, sorted_data
    msg = message.payload.decode()
    print(f"Received message from topic {message.topic}: {msg}")
    try:
        response = json.loads(msg)

        # Check timestamp of the message
        device_timestamp = response.get("timestamp")
        if device_timestamp:
            device_time = datetime.fromisoformat(device_timestamp)  # Parse ISO format timestamp
            current_time = datetime.now(vietnam_timezone)
            print(f"[COMMAND] Device timestamp: {device_timestamp}, current time: {current_time}")

            if (current_time - device_time).total_seconds() > 60:
                print(f"[COMMAND] Ignored old message with timestamp: {device_timestamp}")
                return

        # Check if the message is a handshake response
        if (response.get("device_id") == device_id) and (response.get("status") == ACK_CODE) and (response.get("action") == "handshake_rep"):
            print("[COMMAND] Handshake completed successfully.")
            set_device_status(True)
        # Check if the message is a upload_raw_data response
        elif (response.get("device_id") == device_id) and (response.get("status") == ACK_CODE) and (response.get("action") == "upload_raw_data_rep"):
            print("[COMMAND] Upload raw data completed successfully.")
            chunk_total = int(response.get("chunk_total", 0))
            received_chunks = {}  # Reset the dictionary to start collecting chunks
            sorted_data = []  # Reset the sorted data
            is_upload_header_received = True
            upload_raw_data_event.clear()
        elif response.get("chunk_index"):
            if is_upload_header_received:
                chunk_index = int(response["chunk_index"])
                print(f"[COMMAND] Received chunk {chunk_index} of raw data.")
                received_chunks[chunk_index] = response                

                # Check if all chunks are received
                if len(received_chunks) == chunk_total:
                    print("[COMMAND] All chunks received. Sorting and processing data...")
                    sorted_data = [received_chunks[i] for i in sorted(received_chunks)]
                    is_upload_header_received = False
                    upload_raw_data_event.set()
        else:
            print(f"[COMMAND] Unexpected response: {response}")
            set_device_status(False)
    except json.JSONDecodeError:
        print(f"[COMMAND] Failed to decode message: {msg}")    


def on_connect(client, userdata, flags, rc):
    print("Connected to AWS IoT Core")
    client.subscribe(SUB_TOPIC)
    set_mqtt_broker_status(True)
    # set_device_status(True)

def mqtt_loop():
    global mqtt_client
    while not stop_event.is_set(): 
        mqtt_client.loop(timeout=1.0) 

def connect_to_aws():
    print("connecting to aws ...")
    global mqtt_client, mqtt_thread

    # if mqtt_client is not None: 
    #     print("MQTT client is already running.")
    #     return

    mqtt_client = mqtt.Client(client_id=CLIENT_ID)
    mqtt_client.tls_set(
        ca_certs=CA_CERT,
        certfile=CLIENT_CERT,
        keyfile=CLIENT_KEY,
        cert_reqs=ssl.CERT_REQUIRED,
        tls_version=ssl.PROTOCOL_TLSv1_2,
    )
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    mqtt_client.connect(AWS_ENDPOINT, PORT)

    mqtt_thread = Thread(target=mqtt_loop, daemon=True)
    mqtt_thread.start()

def stop_mqtt_client():
    global mqtt_client, stop_event, mqtt_thread

    if mqtt_client is not None:
        print("Stopping MQTT client...")
        mqtt_client.disconnect()
        set_mqtt_broker_status(False)
        stop_event.set() 
        mqtt_thread.join() 
        mqtt_client = None



def publish_to_handshake_device(device_id):
    global mqtt_client
    if mqtt_client is not None:
        handshake_payload = {
            "device_id": device_id,
            "action": "handshake", 
            "timestamp": datetime.now(vietnam_timezone).isoformat()
        }
        payload_str = json.dumps(handshake_payload)
        mqtt_client.publish(PUB_TOPIC, payload_str)
        print(f"Published message to topic {PUB_TOPIC}: {payload_str}")


def publish_to_request_upload(device_id):
    global mqtt_client
    if mqtt_client is not None:
        upload_payload = {
            "device_id": device_id,
            "action": "upload_raw_data", 
            "timestamp": datetime.now(vietnam_timezone).isoformat()
        }
        payload_str = json.dumps(upload_payload)
        mqtt_client.publish(PUB_TOPIC, payload_str)
        print(f"Published message to topic {PUB_TOPIC}: {payload_str}")
