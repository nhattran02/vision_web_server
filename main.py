from threading import Thread
from website import create_app, socketio
from mqtt_client import connect_to_aws, stop_mqtt_client
import atexit

app = create_app()

if __name__ == '__main__':
    atexit.register(stop_mqtt_client)
    socketio.run(app, debug=True, host='127.0.0.1', port=5000)
