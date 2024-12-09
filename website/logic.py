from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import Attendance
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, emit
from website import socketio
from mqtt_client import connect_to_aws, publish_to_handshake_device, get_device_id, set_device_id, set_device_status, get_device_status
from mqtt_client import device_status_event, stop_mqtt_client, publish_to_request_upload, upload_raw_data_event, get_sorted_data
import time

logic = Blueprint('logic', __name__)


# Handle the device connection page
# ================================
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


# Handle the attendance page
# ==========================
@logic.route('/attendance', methods=['GET', 'POST'])
@login_required
def attendance():
    # set_device_status(True) # For testing
    return render_template('attendance.html', is_device_connected = get_device_status(), user=current_user)


def save_raw_data_to_attendance():
    # db.session.query(Attendance).filter_by(user_id=current_user.id).delete()
    db.session.query(Attendance).delete()
    db.session.commit()

    data = get_sorted_data()

    for d in data:
        attendance = Attendance(
            id=d['id'],
            name=d['name'], 
            date=d['date'], 
            check1=d['check1'], 
            check2=d['check2'], 
            check3=d['check3'], 
            check4=d['check4'], 
            check5=d['check5'], 
            check6=d['check6'], 
            user_id=current_user.id)
        db.session.add(attendance)
    db.session.commit()


def get_data_from_attendance_db():
    attendances = Attendance.query.filter_by(user_id=current_user.id).all()

    data = []
    for attendance in attendances:
        data.append({
            'id': attendance.id,
            'name': attendance.name,
            'date': attendance.date,  
            'check1': attendance.check1,
            'check2': attendance.check2,
            'check3': attendance.check3,
            'check4': attendance.check4,
            'check5': attendance.check5,
            'check6': attendance.check6,
        })

    return data


@socketio.on('upload_raw_data')
def handle_upload_raw_data():
    if get_device_id() and get_device_status():
        publish_to_request_upload(get_device_id())
    else:
        emit('upload_status', {"status": "Device is not connected.", "class": "text-danger"})

    emit('upload_status', {"status": "Uploading ...", "class": "text-info"})
    success = upload_raw_data_event.wait(timeout=30)
    if not success:
        emit('upload_status', {"status": "Upload failed.", "class": "text-danger"})
    else:
        upload_raw_data_event.clear()
        save_raw_data_to_attendance()
        emit('raw_data_received', {'data': get_sorted_data()})
        emit('upload_status', {"status": "Upload completed", "class": "text-success"})



@socketio.on('reload_page')
def handle_reload_page():
    # set_device_status(True) # Only for testing
    if get_data_from_attendance_db() and get_device_status():
        emit('raw_data_received', {'data': get_data_from_attendance_db()})



# Handle the import data page
# ==========================
@logic.route('/import_data', methods=['GET', 'POST'])
@login_required
def import_data():
    return render_template('import_data.html', user=current_user)


