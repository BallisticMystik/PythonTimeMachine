from loguru import logger as log
from shared_resources import db
from utils.queue_handler import queue_handler
from models import TradingSession, WebhookAlert
from routes.api import create_order, close_position, open_position
from aevo_client_config import AevoClientConfig

def create_session(user, percentage, leverage, stop_loss, timeframe, instrument, session_start):
    new_session = TradingSession(
        user_id=user.id,
        instrument=instrument,
        leverage=leverage,
        stop_loss=stop_loss,
        timeframe=timeframe,
        percentage=percentage
    )
    db.session.add(new_session)
    db.session.commit()

    if session_start == 'now':
        result = execute_session(new_session.id, None)
        if result:
            return f'Session created and order placed. Session ID: {new_session.id}'
        else:
            return 'Error placing order immediately.'
    else:
        queue_handler.add_to_queue(new_session.id)
        return f'Session created and queued. Session ID: {new_session.id}'

def process_queue_for_instrument(instrument, order_action):
    queue_handler.process_queue(instrument, order_action)
    for session in queue_handler.get_queued_sessions():
        if session.instrument == instrument:
            execute_session(session.id, None)

def execute_session(session_id, webhook_alert_id=None):
    session = TradingSession.query.get(session_id)
    if not session:
        log.error(f"Session {session_id} not found")
        return False

    aevo_client = AevoClientConfig().get_aevo_client()
    
    try:
        # Fetch current market price
        market_price = float(aevo_client.get_markets(session.instrument.split('-')[0])[0]['mark_price'])
        
        # Calculate order size
        account_balance = float(aevo_client.rest_get_account()['balance'])
        order_size = (account_balance * session.percentage / 100 * session.leverage) / market_price
        
        # Create and execute order
        order = create_order(session, aevo_client, True, order_size)  # Assuming 'True' for is_buy
        
        if order:
            log.info(f"Order placed for session {session_id}: {order}")
            return True
        else:
            log.error(f"Failed to place order for session {session_id}")
            return False
    except Exception as e:
        log.error(f"Error executing session {session_id}: {str(e)}")
        return False
