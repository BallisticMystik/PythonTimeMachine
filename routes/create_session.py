import requests
import json
import random
import time
import hmac
import asyncio
import hashlib
from aevo_client import AevoClient
from flask import render_template, request, redirect, url_for, flash, jsonify
from app_init import app, db
import os
from models import Session, User
from forms import CreateSessionForm

# Initialize AevoClient globally in app config for dependency injection
app.config['AEVO_CLIENT'] = AevoClient(
    signing_key=os.getenv("AEVO_SIGNING_KEY"),
    wallet_address=os.getenv("WALLET_ADDRESS"),
    api_key=os.getenv("AEVO_API_KEY"),
    api_secret=os.getenv("AEVO_API_SECRET"),
    env=os.getenv("ENV", "testnet")
)

def handle_immediate_entry(session, order_size, instrument_id):
    """Handles immediate entry orders synchronously"""
    try:
        aevo_client = app.config['AEVO_CLIENT']
        order_response = aevo_client.post_order(
            instrument_id=instrument_id,
            is_buy=session.position == 'long',
            limit_price=0,
            quantity=order_size
        )
        print("Order response:", order_response)
        return order_response
    except Exception as e:
        print(f"Error creating immediate order: {str(e)}")
        return {"error": str(e)}

@app.route('/create_session', methods=['GET', 'POST'])
def create_session():
    user = User.query.first()
    if not user or not all([user.signing_key, user.wallet_address, user.api_key, user.api_secret, user.env]):
        flash('Please configure your account settings first.', 'error')
        return redirect(url_for('account_config'))
    
    aevo_client = AevoClient(
        signing_key=user.decrypt_data(user.signing_key),
        wallet_address=user.decrypt_data(user.wallet_address),
        api_key=user.decrypt_data(user.api_key),
        api_secret=user.decrypt_data(user.api_secret),
        env=user.env
    )
    
    form = CreateSessionForm()
    instrument_id_mapping = {
        'SEI-PERP': 6104,
        'ETH-PERP': 1,
        'BTC-PERP': 3657
    }
    if form.validate_on_submit():
        ticker = form.ticker.data
        if not ticker or not ticker.endswith('-PERP'):
            flash(f"Invalid ticker format: {ticker}. Must end with -PERP", 'error')
            return render_template('create_session.html', form=form)

        instrument_id = instrument_id_mapping.get(ticker)
        if not instrument_id:
            flash(f"No instrument ID mapping found for ticker: {ticker}", 'error')
            return render_template('create_session.html', form=form)
        
        try:
            markets = aevo_client.get_markets(ticker.split('-')[0])
            if 'error' in markets:
                flash(f"Error validating asset: {markets['error']}", 'error')
                return render_template('create_session.html', form=form)
            market_price = float(markets[0]['mark_price'])
        except Exception as e:
            flash(f"Failed to validate asset: {str(e)}", 'error')
            return render_template('create_session.html', form=form)
        
        session = Session(
            user_id=user.id,
            account_percentage=form.account_percentage.data,
            leverage=form.leverage.data,
            stoploss=form.stoploss.data,
            ticker=ticker,
            timeframe=form.timeframe.data,
            position=form.position.data,
            immediate_entry=form.immediate_entry.data,
            active=True,
            mark_price=market_price
        )
        
        try:
            account_info = aevo_client.rest_get_account()
            account_balance = float(account_info.get('balance', 0))
            order_size = (account_balance * session.account_percentage / 100 * session.leverage) / market_price
            session.amount = order_size
            db.session.add(session)
            db.session.commit()
            
            if session.immediate_entry:
                order_response = aevo_client.post_order(
                    instrument_id=instrument_id,
                    is_buy=session.position == 'long',
                    limit_price=0,
                    quantity=order_size
                )
                if 'error' in order_response:
                    flash(f"Order creation error: {order_response['error']}", 'error')
                    return render_template('create_session.html', form=form)
            
            return jsonify({
                'message': 'Session created successfully',
                'session_id': session.id,
                'order_response': order_response if session.immediate_entry else "No immediate order placed"
            }), 201
        except Exception as e:
            flash(f"Unexpected error creating session: {str(e)}", 'error')
            return render_template('create_session.html', form=form)

    return render_template('create_session.html', form=form)

def calculate_order_size(session):
    # Placeholder: replace with actual calculation based on balance, percentage, leverage
    return 1000000

# Additional Routes
@app.route('/get_instrument_price/<string:instrument_name>')
def get_instrument_price(instrument_name):
    aevo_client = app.config['AEVO_CLIENT']
    ticker_data = aevo_client.get_markets(instrument_name.split('-')[0])
    for market in ticker_data:
        if market['instrument_name'] == instrument_name:
            return jsonify({'price': market['mark_price']})
    return jsonify({'error': 'Instrument not found'}), 404

@app.route('/get_instruments')
def get_instruments():
    aevo_client = app.config['AEVO_CLIENT']
    assets = ["ETH", "BTC", "WIF", "BONK", "SOL", "POPCAT", "ICP", "AEVO", "SEI"]
    all_instruments = []
    for asset in assets:
        instruments = aevo_client.get_markets(asset)
        all_instruments.extend(instruments)
    return jsonify(all_instruments)
