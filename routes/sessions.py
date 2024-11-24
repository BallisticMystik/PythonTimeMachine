from flask import render_template, jsonify, request, flash, redirect, url_for
from app_init import app, db
from models import User
from models import Session
from aevo_client import AevoClient
import os

aevo_client = None

def initialize_aevo_client():
    global aevo_client
    with app.app_context():
        user = User.query.first()  # Assuming we're working with a single user for now
        if user:
            signing_key = user.decrypt_data(user.signing_key) if user.signing_key else None
            wallet_address = user.decrypt_data(user.wallet_address) if user.wallet_address else None
            api_key = user.decrypt_data(user.api_key) if user.api_key else None
            api_secret = user.decrypt_data(user.api_secret) if user.api_secret else None
            env = user.env if user.env else 'testnet'
            if all([signing_key, wallet_address, api_key, api_secret, env]):
                aevo_client = AevoClient(signing_key, wallet_address, api_key, api_secret, env)
    return aevo_client

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    app.logger.info(f"Received webhook data: {data}")
    if data.get('key') != 'TOPX':
        return jsonify({'error': 'Invalid key'}), 400
    strategy = data.get('strategy', {})
    order_action = strategy.get('order_action')
    order_contracts = strategy.get('order_contracts')
    order_price = strategy.get('order_price')
    if not all([order_action, order_contracts, order_price]):
        return jsonify({'error': 'Incomplete strategy data'}), 400
    app.logger.info(f"Executing trade: {order_action} {order_contracts} contracts at {order_price}")
    # TODO: Implement trade execution logic here
    return jsonify({'message': 'Trade executed successfully'}), 200

@app.route('/previous_sessions')
def previous_sessions():
    # Fetch trade history from the Aevo API
    trade_history = aevo_client.rest_get_trade_history()
    return render_template('previous_sessions.html', trade_history=trade_history)
    trade_history = aevo_client.rest_get_trade_history()
    return render_template('previous_sessions.html', trade_history=trade_history)

@app.route('/current_sessions')
def current_sessions_view():
    return render_template('current_sessions.html')

@app.route('/api/current_sessions')
def current_sessions():
    sessions = Session.query.all()  # Fetch all sessions
    return jsonify([session.to_dict() for session in sessions])
