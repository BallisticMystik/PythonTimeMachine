import time
import random
import requests
import hmac
import hashlib
import asyncio
import websockets
from eth_account import Account
from eip712_order_signer import eip712_domain_separator, hash_order, sign_order_with_signing_key
from web3 import Web3

class AevoClient:
    def __init__(self, signing_key, wallet_address, api_key, api_secret, env='testnet'):
        self.signing_key = signing_key
        self.wallet_address = wallet_address
        self.api_key = api_key
        self.api_secret = api_secret
        self.env = env
        self.base_url = "https://api.aevo.xyz" if env == "mainnet" else "https://api-testnet.aevo.xyz"
        self.connection = None

    def get_markets(self, asset):
        """Fetch market data for the specified asset."""
        try:
            url = f"{self.base_url}/markets?asset={asset}"
            headers = self._headers()
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching markets: {e}")
            return None

    def get_current_price(self, instrument_id):
        """Fetch the current market price for the specified instrument."""
        try:
            response = requests.get(f"{self.base_url}/markets", headers=self._headers())
            response.raise_for_status()
            markets = response.json()
            for market in markets:
                if market['instrument_id'] == instrument_id:
                    return int(float(market['mark_price']) * 10**6)  # Convert to 6-decimal fixed-point
            raise ValueError(f"Instrument with ID {instrument_id} not found.")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching current price: {e}")
            return None

    def create_order_payload(self, instrument, is_buy, amount, stop_type=None, trigger_price=None, close_position=False):
        """Create and sign the order payload."""
        limit_price = self.get_current_price(instrument)
        if limit_price is None:
            raise ValueError("Could not fetch current price for market order.")

        order = {
            "instrument": instrument,
            "maker": self.wallet_address,
            "isBuy": is_buy,
            "limitPrice": limit_price,
            "amount": amount,
            "salt": random.randint(1, 10**8),
            "timestamp": int(time.time()),
        }

        if stop_type:
            order["stop"] = stop_type
        if trigger_price:
            order["trigger"] = trigger_price
        order["closePosition"] = close_position

        domain_separator = eip712_domain_separator(
            name="Aevo Mainnet" if self.env == "mainnet" else "Aevo Testnet",
            version="1",
            chain_id=1 if self.env == "mainnet" else 11155111,
            verifying_contract=self.wallet_address
        )

        # Generate signature
        signature = sign_order_with_signing_key(order, self.signing_key, domain_separator)
        order["signature"] = signature

        return order

    def post_order(self, order_payload):
        """Send the signed order to Aevo API."""
        headers = self._headers()
        try:
            response = requests.post(f"{self.base_url}/orders", json=order_payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error posting order: {e}")
            return {"error": str(e)}

    def set_leverage(self, instrument_id, leverage):
        """Set leverage for a specified instrument."""
        leverage_url = f"{self.base_url}/account/leverage"
        payload = {"instrument": instrument_id, "leverage": leverage}
        headers = self._headers()

        try:
            response = requests.post(leverage_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error setting leverage: {e}")
            return {"error": str(e)}

    def _headers(self):
        """Generate secure headers with HMAC signature."""
        timestamp = str(int(time.time() * 1000))
        message = f"{self.api_key},{timestamp},GET,/markets,".encode("utf-8")
        signature = hmac.new(self.api_secret.encode("utf-8"), message, hashlib.sha256).hexdigest()

        return {
            "AEVO-KEY": self.api_key,
            "AEVO-SECRET": self.api_secret,
            "AEVO-TIMESTAMP": timestamp,
            "AEVO-SIGNATURE": signature,
            "accept": "application/json",
            "content-type": "application/json"
        }

    async def open_connection(self):
        """Open WebSocket connection and keep it alive."""
        try:
            self.connection = await websockets.connect(f"wss://{'ws' if self.env == 'mainnet' else 'ws-testnet'}.aevo.xyz")
            print("WebSocket connection opened")
            asyncio.create_task(self._keep_alive())
        except Exception as e:
            print(f"Error opening WebSocket connection: {e}")

    async def _keep_alive(self):
        """Maintain the WebSocket connection."""
        while True:
            try:
                await self.connection.ping()
                await asyncio.sleep(30)
            except Exception as e:
                print(f"Error in keep_alive: {e}")
                await self.open_connection()

    async def close_connection(self):
        """Close WebSocket connection."""
        if self.connection:
            await self.connection.close()
            print("WebSocket connection closed")

# Initialize Web3 instance (optional, based on project needs)
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
