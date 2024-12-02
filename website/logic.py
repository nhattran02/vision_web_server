from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, emit
from website import socketio
from mqtt_client import connect_to_aws, publish_to_handshake_device, get_device_id, set_device_id, set_device_status, get_device_status
from mqtt_client import device_status_event
import time

logic = Blueprint('logic', __name__)


@logic.route('/device_connection', methods=['GET', 'POST'])
@login_required
def device_connection():
    print("get_device_status", get_device_status())
    return render_template('device_connection.html', device_id = get_device_id(), is_device_connected = get_device_status(), user=current_user)

@socketio.on('connect')
def handle_connect():
    print("Client connected")

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")


@socketio.on('connect_device')
def handle_connect_device(data):
    set_device_id(data.get('device_id', None))
    if get_device_id():
        emit('update_status', {"status": f"Connecting to device: {get_device_id()}", "class": "alert-warning"})
        set_device_status(False)
        connect_to_aws()
        publish_to_handshake_device(get_device_id())
        success = device_status_event.wait(timeout=5)

        if success and get_device_status():
            emit('update_status', {"status": f"Connected to device: {get_device_id()}", "class": "alert-success"})
            set_device_status(True)
        else:
            emit('update_status', {"status": "Failed to connect to device within timeout.", "class": "alert-danger"})
            set_device_status(False)
        
    else:
        emit('update_status', {"status": "Device ID is required to connect.", "class": "alert-danger"})

@socketio.on('disconnect_device')
def handle_disconnect_device():
    emit('update_status', {"status": "Disconnected.", "class": "alert-danger"})
    set_device_status(False)














# @logic.route('/device_connection', methods=['GET', 'POST'])
# @login_required
# def device_connection():
#     device_id = None
#     status = "Waiting for connection..."
#     connection_status = None
#     disconnect_status = None
#     alerts = []
#     alerts.append({"message": "Waiting for connection...", "class": "alert-info"})

#     if request.method == 'POST':
#         device_id = request.form.get('device_id', "").strip()
#         if 'connect' in request.form:
#             if device_id:
#                 alerts = []
#                 alerts.append({"message": f"Connecting to device: {device_id}", "class": "alert-warning"})
#                 alerts = []
#                 alerts.append({"message": f"Connected to device: {device_id}", "class": "alert-success"})
#             else:
#                 alerts = []
#                 alerts.append({"message": "Device ID is required to connect.", "class": "alert-danger"})

#         elif 'disconnect' in request.form:
#             alerts = []
#             alerts.append({"message": "Disconnected.", "class": "alert-info"})

#     return render_template('device_connection.html', 
#                            device_id=device_id, 
#                            status=status, 
#                            connection_status=connection_status, 
#                            disconnect_status=disconnect_status, 
#                            user = current_user, alerts=alerts)


