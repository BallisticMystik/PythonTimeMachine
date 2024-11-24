from flask import Blueprint, request, jsonify
from app_init import app, db
from models import User, Session
from aevo_client import AevoClient
import os
import logging

api_bp = Blueprint('api_blueprint', __name__)
logger = logging.getLogger(__name__)

@api_bp.route('/api/orders', methods=['POST'])
def create_order():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        required_fields = ['instrument', 'side', 'size']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Get user and initialize Aevo client
        user = User.query.first()  # TODO: Replace with proper user authentication
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        from aevo_client import post_order
        
        # Create market order using the post_order function
        try:
            order_response = post_order(
                instrument_id=data['instrument'],
                is_buy=data['side'].lower() == 'buy',
                quantity=float(data['size']),
                limit_price=0  # Market order
            )
            
            if 'error' in order_response:
                return jsonify({"error": order_response['error']}), 400
            
            # Create session record
            session = Session(
                user_id=user.id,
                instrument_name=data['instrument'],
                amount=float(data['size']),
                active=True
            )
            db.session.add(session)
            db.session.commit()
            
            return jsonify({
                "status": "success",
                "order": order_response,
                "session_id": session.id
            }), 201
            
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            return jsonify({"error": f"Error creating order: {str(e)}"}), 500
            
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    try:
        user = User.query.first()  # TODO: Replace with proper user authentication
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        aevo_client = AevoClient(
            signing_key=user.decrypt_data(user.signing_key),
            wallet_address=user.decrypt_data(user.wallet_address),
            api_key=user.decrypt_data(user.api_key),
            api_secret=user.decrypt_data(user.api_secret),
            env=user.env or 'testnet'
        )
        
        order = aevo_client.get_order_by_id(order_id)
        return jsonify(order), 200
        
    except Exception as e:
        logger.error(f"Error fetching order: {str(e)}")
        return jsonify({"error": str(e)}), 500
