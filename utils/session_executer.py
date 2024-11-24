from loguru import logger as log
from shared_resources import db, queue_handler
from models import TradingSession, WebhookAlert
from routes.api import create_order, close_position, open_position
from aevo_client_config import AevoClientConfig

def create_session(user, percentage, leverage, stop_loss, timeframe, instrument, session_start):
    new_session = TradingSession(
        user_id=user.id,
        instrument=instrument,
        leverage=leverage,
        stoploss=stop_loss,
        timeframe=timeframe,
        account_percentage=percentage
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
    # Implementation of execute_session function
    pass
