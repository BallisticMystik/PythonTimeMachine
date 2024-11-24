from flask import Blueprint, request, jsonify
import logging
from shared_resources import db
from models import Session, User
from aevo_client import AevoClient
import os

webhook_bp = Blueprint('webhook', __name__)
logger = logging.getLogger(__name__)

def create_market_order(aevo_client, instrument_id, is_buy, quantity):
    try:
        logger.info(f"Creating market order: instrument_id={instrument_id}, is_buy={is_buy}, quantity={quantity}")
        order = aevo_client.rest_create_market_order(
            instrument_id=instrument_id,
            is_buy=is_buy,
            quantity=quantity
        )
        logger.info(f"Order created successfully: {order}")
        return order
    except Exception as e:
        logger.error(f"Error creating market order: {str(e)}")
        raise

@webhook_bp.route('/', methods=['POST'])
def webhook_handler():
    data = request.json
    logger.info(f"Received webhook data: {data}")
    
    # Verify the authenticity of the request
    if data.get('key') != 'TOPX':
        return jsonify({"status": "error", "message": "Invalid key"}), 400
    
    try:
        # Get the active session for the instrument
        ticker = data.get('ticker')
        session = Session.query.filter_by(ticker=ticker, active=True).first()
        if not session:
            return jsonify({"status": "error", "message": f"No active session found for {ticker}"}), 404
        
        # Initialize Aevo client
        user = User.query.get(session.user_id)
        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404
        
        aevo_client = AevoClient(
            signing_key=user.decrypt_data(user.signing_key),
            wallet_address=user.decrypt_data(user.wallet_address),
            api_key=user.decrypt_data(user.api_key),
            api_secret=user.decrypt_data(user.api_secret),
            env=user.env or 'testnet'
        )
        
        # Get account balance and calculate order size
        account_info = aevo_client.rest_get_account()
        if not isinstance(account_info, dict) or 'balance' not in account_info:
            return jsonify({"status": "error", "message": "Failed to fetch account balance"}), 500
        
        account_balance = float(account_info['balance'])
        markets = aevo_client.get_markets(ticker.split('-')[0])
        if not markets:
            return jsonify({"status": "error", "message": f"Failed to fetch market data for {ticker}"}), 500
        
        market_price = float(markets[0]['mark_price'])
        order_size = (account_balance * session.account_percentage / 100 * session.leverage) / market_price
        
        # Determine order direction from webhook data
        order_action = data.get('strategy', {}).get('order_action', '').lower()
        is_buy = order_action in ['buy', 'long']
        
        # Create the market order
        order_response = create_market_order(
            aevo_client=aevo_client,
            instrument_id=session.ticker,
            is_buy=is_buy,
            quantity=order_size
        )
        
        # Update session with order details
        session.amount = order_size
        session.mark_price = market_price
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Order executed successfully",
            "order": order_response,
            "session_id": session.id
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500