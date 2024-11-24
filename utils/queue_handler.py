from loguru import logger as log
from models import TradingSession

class QueueHandler:
    def __init__(self):
        self.queued_sessions = []

    def add_to_queue(self, session_id):
        self.queued_sessions.append(session_id)

    def process_queue(self, instrument, order_action):
        from utils.session_handler import execute_session  # Import here to avoid circular import
        for session_id in self.queued_sessions[:]:
            session = TradingSession.query.get(session_id)
            if session and session.instrument == instrument:
                execute_session(session_id, None)
                self.queued_sessions.remove(session_id)
                log.info(f"Queued session {session_id} executed for {instrument}")

    def get_queued_sessions(self):
        return [TradingSession.query.get(session_id) for session_id in self.queued_sessions]

queue_handler = QueueHandler()