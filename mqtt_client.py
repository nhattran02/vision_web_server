import ssl
import paho.mqtt.client as mqtt
from threading import Thread, Event

# AWS IoT Core settings
AWS_ENDPOINT = "a2hnk4whzd8l7x-ats.iot.ap-southeast-1.amazonaws.com"
PORT = 8883
CLIENT_ID = "vision_web_aws"
SUB_TOPIC = "/device2aws"
PUB_TOPIC = "/aws2device"

CA_CERT = "aws_package/root_cert_auth.crt"
CLIENT_CERT = "aws_package/client.crt"
CLIENT_KEY = "aws_package/client.key"

mqtt_client = None  
mqtt_thread = None  
stop_event = Event() 

def on_message(client, userdata, message):
    print(f"Received message from topic {message.topic}: {message.payload.decode()}")

def on_connect(client, userdata, flags, rc):
    print("Connected to AWS IoT Core")
    client.subscribe(SUB_TOPIC)

def mqtt_loop():
    global mqtt_client
    while not stop_event.is_set(): 
        mqtt_client.loop(timeout=1.0) 

def connect_to_aws():
    print("connecting to aws ...")
    global mqtt_client, mqtt_thread

    if mqtt_client is not None: 
        print("MQTT client is already running.")
        return

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
        stop_event.set() 
        mqtt_thread.join() 
        mqtt_client.disconnect() 
