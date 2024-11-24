import asyncio
import json
import logging
import ssl
import websockets
from datetime import datetime
from app_init import app, db
from models import Session

logger = logging.getLogger(__name__)

class WebSocketController:
    def __init__(self, aevo_client):
        self.aevo_client = aevo_client
        self.connection_status = "Disconnected"
        self.last_update = None
        self.connection = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5  # seconds
        self.subscriptions = []

    async def connect(self):
        """Establish WebSocket connection with automatic reconnection."""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached")
            return False

        try:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            ws_url = f"wss://{'ws' if self.aevo_client.env == 'mainnet' else 'ws-testnet'}.aevo.xyz"
            self.connection = await websockets.connect(
                ws_url,
                ssl=ssl_context,
                ping_interval=30,
                ping_timeout=10
            )

            # Authenticate
            auth_message = {
                "op": "auth",
                "data": {
                    "key": self.aevo_client.api_key,
                    "secret": self.aevo_client.api_secret
                }
            }
            await self.connection.send(json.dumps(auth_message))
            
            # Resubscribe to previous subscriptions
            for subscription in self.subscriptions:
                await self.subscribe(subscription)

            self.connection_status = "Connected"
            self.reconnect_attempts = 0
            logger.info("WebSocket connected successfully")
            return True

        except Exception as e:
            logger.error(f"WebSocket connection error: {str(e)}")
            self.connection_status = "Disconnected"
            self.reconnect_attempts += 1
            await asyncio.sleep(self.reconnect_delay)
            return False

    async def subscribe(self, channel):
        """Subscribe to a specific channel."""
        if channel not in self.subscriptions:
            self.subscriptions.append(channel)

        if self.connection and self.connection.open:
            message = {
                "op": "subscribe",
                "data": [channel]
            }
            await self.connection.send(json.dumps(message))
            logger.info(f"Subscribed to channel: {channel}")

    async def handle_message(self, message):
        """Process incoming WebSocket messages."""
        try:
            data = json.loads(message)
            if data.get("channel") == "orders":
                await self.handle_order_update(data)
            elif data.get("channel") == "account":
                await self.handle_account_update(data)
            
            self.last_update = datetime.now()
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")

    async def handle_order_update(self, data):
        """Handle order updates."""
        try:
            orders = data.get("data", {}).get("orders", [])
            for order in orders:
                session = Session.query.filter_by(
                    instrument_name=order.get("instrument_name")
                ).first()
                
                if session:
                    session.updated_at = datetime.now()
                    if order.get("order_status") == "filled":
                        session.active = False
                    db.session.commit()
        except Exception as e:
            logger.error(f"Error handling order update: {str(e)}")

    async def handle_account_update(self, data):
        """Handle account updates."""
        try:
            account_data = data.get("data", {})
            # Process account updates (balance, margin, etc.)
            logger.info(f"Account update received: {account_data}")
        except Exception as e:
            logger.error(f"Error handling account update: {str(e)}")

    async def start(self):
        """Start WebSocket connection and message handling."""
        while True:
            if not self.connection or not self.connection.open:
                connected = await self.connect()
                if not connected:
                    continue

            try:
                async for message in self.connection:
                    await self.handle_message(message)
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed")
                self.connection_status = "Disconnected"
                continue
            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}")
                await asyncio.sleep(self.reconnect_delay)

    def get_connection_status(self):
        """Get current connection status."""
        return {
            "status": self.connection_status,
            "last_update": self.last_update.isoformat() if self.last_update else "Never"
        }