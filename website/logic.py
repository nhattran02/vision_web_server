from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user


logic = Blueprint('logic', __name__)

@logic.route('/device_connection', methods=['GET', 'POST'])
@login_required
def device_connection():
    device_id = None
    status = "Waiting for connection..."
    connection_status = None
    disconnect_status = None
    alerts = []
    alerts.append({"message": "Waiting for connection...", "class": "alert-info"})

    if request.method == 'POST':
        device_id = request.form.get('device_id', "").strip()
        if 'connect' in request.form:
            if device_id:
                alerts = []
                alerts.append({"message": f"Connecting to device: {device_id}", "class": "alert-warning"})
                alerts = []
                alerts.append({"message": f"Connected to device: {device_id}", "class": "alert-success"})
            else:
                alerts = []
                alerts.append({"message": "Device ID is required to connect.", "class": "alert-danger"})

        elif 'disconnect' in request.form:
            alerts = []
            alerts.append({"message": "Disconnected.", "class": "alert-info"})

    return render_template('device_connection.html', 
                           device_id=device_id, 
                           status=status, 
                           connection_status=connection_status, 
                           disconnect_status=disconnect_status, 
                           user = current_user, alerts=alerts)


