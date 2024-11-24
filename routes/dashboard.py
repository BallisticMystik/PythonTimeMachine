from flask import render_template, jsonify, flash, redirect, url_for
from app_init import app
import os
import requests
import json
import time
import hmac
import hashlib

def get_headers(path, method, body):
    timestamp = str(time.time_ns())
    message = f"{os.environ['AEVO_API_KEY']},{timestamp},{method.upper()},{path},{body}".encode("utf-8")
    signature = hmac.new(os.environ['AEVO_API_SECRET'].encode("utf-8"), message, hashlib.sha256).hexdigest()

    headers = {
        "AEVO-TIMESTAMP": timestamp,
        "AEVO-SIGNATURE": signature,
        "AEVO-KEY": os.environ['AEVO_API_KEY'],
        "accept": "application/json",
        "content-type": "application/json"
    }

    return headers

@app.route('/dashboard')
def dashboard():
    ws_controller = app.config.get('WS_CONTROLLER')
    if not ws_controller:
        return render_template('dashboard.html', ws_status={'status': 'Not initialized', 'last_update': None})
    return render_template('dashboard.html', ws_status=ws_controller.get_connection_status())

@app.route('/portfolio')
def portfolio():
    url = "https://api.aevo.xyz/portfolio"
    headers = get_headers("/portfolio", "GET", "")
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        portfolio_data = response.json()
        return render_template('portfolio.html', portfolio_data=portfolio_data)
    else:
        flash(f"Error fetching portfolio data: {response.text}", 'error')
        return redirect(url_for('dashboard'))

@app.route('/reset', methods=['POST'])
def reset_application_state():
    try:
        # Logic to clear session data or reset application state
        # For now, we'll just simulate a successful reset
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
@app.route('/test_orders')
def test_orders():
    return render_template('test_orders.html')

@app.route('/ws_status')
def ws_status():
    ws_controller = app.config.get('WS_CONTROLLER')
    if ws_controller:
        return jsonify(ws_controller.get_connection_status())
    return jsonify({'status': 'Not initialized', 'last_update': None})

@app.route('/account_performance')
def account_performance():
    return render_template('account_performance.html')