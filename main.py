from threading import Thread
from website import create_app
from mqtt_client import connect_to_aws, stop_mqtt_client
import atexit

app = create_app()

if __name__ == '__main__':
    connect_to_aws()
    atexit.register(stop_mqtt_client)
    app.run(debug=True)
