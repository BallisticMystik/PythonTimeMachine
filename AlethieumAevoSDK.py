from eip712_order_signer import eip712_domain_separator, hash_order, sign_order_with_signing_key, initialize_order
import asyncio
import json
import hmac
import hashlib
import random
import traceback
import ssl
import time

import requests
import websockets
from eth_account import Account
from web3.auto import w3
from loguru import logger
from web3 import Web3

w3 = Web3(
    Web3.HTTPProvider("http://127.0.0.1:8545")
)  # This URL doesn"t actually do anything, we just need a web3 instance

CONFIG = {
    "testnet": {
        "rest_url": "https://api-testnet.aevo.xyz",
        "ws_url": "wss://ws-testnet.aevo.xyz",
        "signing_domain": {
            "name": "Aevo Testnet",
            "version": "1",
            "chainId": "11155111",
        },
    },
    "mainnet": {
        "rest_url": "https://api.aevo.xyz",
        "ws_url": "wss://ws.aevo.xyz",
        "signing_domain": {
            "name": "Aevo Mainnet",
            "version": "1",
            "chainId": "1",
        },
    },
}

from eth_abi.packed import encode_packed
from eth_utils import to_bytes, keccak

class Order:
    def __init__(self, maker, isBuy, limitPrice, amount, salt, instrument, timestamp):
        self.maker = to_bytes(hexstr=maker)
        self.isBuy = isBuy  # True for long (buy) order, False for short (sell) order
        self.limitPrice = limitPrice
        self.amount = amount
        self.salt = salt
        self.instrument = instrument
        self.timestamp = timestamp

    def hash_struct(self):
        return b''  # Placeholder, replace with actual implementation

class AevoClient:
    def __init__(
        self,
        signing_key="",
        wallet_address="",
        api_key="",
        api_secret="",
        env="testnet",
        rest_headers={},
    ):
        self.signing_key = signing_key
        self.wallet_address = wallet_address
        self.api_key = api_key
        self.api_secret = api_secret
        self.connection = None
        self.client = requests
        self.rest_headers = {
            "AEVO-KEY": api_key,
            "AEVO-SECRET": api_secret,
        }
        self.extra_headers = None
        self.rest_headers.update(rest_headers)

        if (env != "testnet") and (env != "mainnet"):
            raise ValueError("env must either be 'testnet' or 'mainnet'")
        self.env = env

    @property
    def address(self):
        return w3.eth.account.from_key(self.signing_key).address

    @property
    def rest_url(self):
        return CONFIG[self.env]["rest_url"]

    @property
    def ws_url(self):
        return CONFIG[self.env]["ws_url"]

    @property
    def signing_domain(self):
        return CONFIG[self.env]["signing_domain"]

    def get_auth_payload(self, op, data):
        timestamp = str(time.time_ns())
        concat = f"{self.api_key},{timestamp},ws,{op},{data}".encode("utf-8")
        signature = hmac.new(self.api_secret.encode("utf-8"), concat, hashlib.sha256).hexdigest()
        return {
            "timestamp": timestamp,
            "signature": signature,
            "key": self.api_key,
        }

    async def open_connection(self, extra_headers={}):
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        try:
            logger.info("Opening Aevo websocket connection...")

            self.connection = await websockets.connect(
                self.ws_url,
                ssl=ssl_context,
                ping_interval=1,
                ping_timeout=None,
                extra_headers=extra_headers,
            )
            if not self.extra_headers:
                self.extra_headers = extra_headers

            if self.api_key and self.wallet_address:
                logger.debug(f"Connecting to {self.ws_url}...")
                await self.connection.send(
                    json.dumps(
                        {
                            "id": 1,
                            "op": "auth",
                            "data": {
                                "key": self.api_key,
                                "secret": self.api_secret,
                            },
                        }
                    )
                )

            await asyncio.sleep(1)
        except Exception as e:
            logger.error("Error thrown when opening connection")
            logger.error(e)
            logger.error(traceback.format_exc())
            await asyncio.sleep(10)

    async def reconnect(self):
        logger.info("Trying to reconnect Aevo websocket...")
        await self.close_connection()
        await self.open_connection(self.extra_headers)

    async def close_connection(self):
        try:
            logger.info("Closing connection...")
            await self.connection.close()
            logger.info("Connection closed")
        except Exception as e:
            logger.error("Error thrown when closing connection")
            logger.error(e)
            logger.error(traceback.format_exc())

    async def read_messages(self, read_timeout=0.1, backoff=0.1, on_disconnect=None):
        while True:
            try:
                message = await asyncio.wait_for(
                    self.connection.recv(), timeout=read_timeout
                )
                yield message
            except (
                websockets.exceptions.ConnectionClosedError,
                websockets.exceptions.ConnectionClosedOK,
            ) as e:
                if on_disconnect:
                    on_disconnect()
                logger.error("Aevo websocket connection close")
                logger.error(e)
                logger.error(traceback.format_exc())
                await self.reconnect()
            except asyncio.TimeoutError:
                await asyncio.sleep(backoff)
            except Exception as e:
                logger.error(e)
                logger.error(traceback.format_exc())
                await asyncio.sleep(1)

    async def send(self, op, data=""):
        try:
            auth_payload = self.get_auth_payload(op, data)
            message = json.dumps({"op": op, "auth": auth_payload, "data": data})
            await self.connection.send(message)
        except websockets.exceptions.ConnectionClosedError as e:
            logger.debug("Restarted Aevo websocket connection")
            await self.reconnect()
            await self.connection.send(message)

    def get_index(self, asset):
        req = self.client.get(f"{self.rest_url}/index?asset={asset}")
        data = req.json()
        return data

    def get_markets(self, asset):
        req = self.client.get(f"{self.rest_url}/markets?asset={asset}")
        data = req.json()
        return data

    def get_orderbook(self, instrument_name):
        req = self.client.get(
            f"{self.rest_url}/orderbook?instrument_name={instrument_name}"
        )
        data = req.json()
        return data

    def rest_create_order(
        self, instrument_id, is_buy, limit_price, quantity, post_only=True
    ):
        data = self.create_order_rest_json(
            int(instrument_id), is_buy, limit_price, quantity, post_only
        )
        req = self.client.post(
            f"{self.rest_url}/orders", json=data, headers=self.rest_headers
        )
        return req.json()

    def rest_create_market_order(self, instrument_id, is_buy, quantity):
        limit_price = 0
        if is_buy:
            limit_price = 2**256 - 1

        data = self.create_order_rest_json(
            int(instrument_id),
            is_buy,
            limit_price,
            quantity,
            decimals=1,
            post_only=False,
        )

        req = self.client.post(
            f"{self.rest_url}/orders", json=data, headers=self.rest_headers
        )
        return req.json()

    def rest_cancel_order(self, order_id):
        req = self.client.delete(
            f"{self.rest_url}/orders/{order_id}", headers=self.rest_headers
        )
        logger.info(req.json())
        return req.json()

    def rest_get_account(self):
        req = self.client.get(f"{self.rest_url}/account", headers=self.rest_headers)
        return req.json()

    def rest_get_apikey(self):
        req = self.client.get(f"{self.rest_url}/account", headers=self.rest_headers)
        data = req.json()
        api_keys = data.get('api_keys', [])
        for api_key_info in api_keys:
            return api_key_info.get('api_key')
        return None

    def rest_get_portfolio(self):
        req = self.client.get(f"{self.rest_url}/portfolio", headers=self.rest_headers)
        return req.json()

    def rest_get_open_orders(self):
        req = self.client.get(
            f"{self.rest_url}/orders", json={}, headers=self.rest_headers
        )
        return req.json()

    def rest_cancel_all_orders(
        self,
        instrument_type=None,
        asset=None,
    ):
        body = {}
        if instrument_type:
            body["instrument_type"] = instrument_type

        if asset:
            body["asset"] = asset

        req = self.client.delete(
            f"{self.rest_url}/orders-all", json=body, headers=self.rest_headers
        )
        return req.json()

    async def subscribe_tickers(self, asset):
        await self.send(
            json.dumps(
                {
                    "op": "subscribe",
                    "data": [f"ticker:{asset}:OPTION"],
                }
            )
        )

    async def subscribe_ticker(self, channel):
        msg = json.dumps(
            {
                "op": "subscribe",
                "data": [channel],
            }
        )
        await self.send(msg)

    async def subscribe_markprice(self, asset):
        await self.send(
            json.dumps(
                {
                    "op": "subscribe",
                    "data": [f"markprice:{asset}:OPTION"],
                }
            )
        )

    async def subscribe_orderbook(self, instrument_name):
        await self.send(
            json.dumps(
                {
                    "op": "subscribe",
                    "data": [f"orderbook:{instrument_name}"],
                }
            )
        )

    async def subscribe_trades(self, instrument_name):
        await self.send(
            json.dumps(
                {
                    "op": "subscribe",
                    "data": [f"trades:{instrument_name}"],
                }
            )
        )

    async def subscribe_index(self, asset):
        await self.send(json.dumps({"op": "subscribe", "data": [f"index:{asset}"]}))

    async def subscribe_orders(self):
        payload = {
            "op": "subscribe",
            "data": ["orders"],
        }
        await self.send(json.dumps(payload))

    async def subscribe_fills(self):
        payload = {
            "op": "subscribe",
            "data": ["fills"],
        }
        await self.send(json.dumps(payload))

    def create_order_ws_json(
        self,
        instrument_id,
        is_buy,
        limit_price,
        quantity,
        post_only=True,
    ):
        salt, signature = self.sign_order(instrument_id, is_buy, limit_price, quantity)
        return {
            "instrument": instrument_id,
            "maker": self.wallet_address,
            "is_buy": is_buy,
            "amount": str(int(round(quantity * 10**6, is_buy))),
            "limit_price": str(int(round(limit_price * 10**6, is_buy))),
            "salt": str(salt),
            "signature": signature,
            "post_only": post_only,
            "timestamp": int(time.time()),
        }

    def create_order_rest_json(
        self,
        instrument_id,
        is_buy,
        limit_price,
        quantity,
        post_only=True,
        decimals=10**6,
    ):
        salt, signature = self.sign_order(
            instrument_id, is_buy, limit_price, quantity, decimals=decimals
        )
        return {
            "maker": self.wallet_address,
            "is_buy": is_buy,
            "instrument": instrument_id,
            "limit_price": str(int(round(limit_price * decimals, is_buy))),
            "amount": str(int(round(quantity * 10**6, is_buy))),
            "salt": str(salt),
            "signature": signature,
            "post_only": post_only,
            "timestamp": int(time.time()),
        }

    async def create_order(
        self, instrument_id, is_buy, limit_price, quantity, post_only=True, id=None
    ):
        data = self.create_order_ws_json(
            int(instrument_id), is_buy, limit_price, quantity, post_only
        )
        payload = {"op": "create_order", "data": data}
        if id:
            payload["id"] = id

        logger.info(payload)
        await self.send(json.dumps(payload))

    async def edit_order(
        self,
        order_id,
        instrument_id,
        is_buy,
        limit_price,
        quantity,
        id=None,
        post_only=True,
    ):
        instrument_id = int(instrument_id)
        salt, signature = self.sign_order(instrument_id, is_buy, limit_price, quantity)
        payload = {
            "op": "edit_order",
            "data": {
                "order_id": order_id,
                "instrument": instrument_id,
                "maker": self.wallet_address,
                "is_buy": is_buy,
                "amount": str(int(round(quantity * 10**6, is_buy))),
                "limit_price": str(int(round(limit_price * 10**6, is_buy))),
                "salt": str(salt),
                "signature": signature,
                "post_only": post_only,
            },
        }

        if id:
            payload["id"] = id

        await self.send(json.dumps(payload))

    async def cancel_order(self, order_id):
        payload = {"op": "cancel_order", "data": {"order_id": order_id}}
        await self.send(json.dumps(payload))

    async def cancel_all_orders(self):
        payload = {"op": "cancel_all_orders", "data": {}}
        await self.send(json.dumps(payload))

    def sign_order(
        self, instrument_id, is_buy, limit_price, quantity, decimals=10**6
    ):
        salt = random.randint(0, 10**10)

        order_struct = Order(
            maker=self.wallet_address,
            isBuy=is_buy,  # True for long (buy) order, False for short (sell) order
            limitPrice=int(round(limit_price * decimals, is_buy)),
            amount=int(round(quantity * 10**6, is_buy)),
            salt=salt,
            instrument=instrument_id,
            timestamp=int(time.time()),
        )

        domain_separator = eip712_domain_separator(
            name=self.signing_domain['name'],
            version=self.signing_domain['version'],
            chain_id=int(self.signing_domain['chainId']),
            verifying_contract=self.wallet_address
        )

        signable_bytes = Web3.keccak(domain_separator + order_struct.hash_struct())
        signature = Account._sign_hash(signable_bytes, self.signing_key).signature.hex()
        
        return salt, signature
        signable_bytes = Web3.keccak(domain_separator + order_struct.hash_struct())
        return (
            salt,
            Account._sign_hash(signable_bytes, self.signing_key).signature.hex(),
        )

    def sign_transaction(
        self, decimals=10**6
    ):
        salt = random.randint(0, 10**10)

        transaction_struct = Order(
            maker=self.wallet_address,
            salt=salt,
            timestamp=int(time.time()),
        )

        domain_separator = eip712_domain_separator(**self.signing_domain)
        signable_bytes = Web3.keccak(domain_separator + transaction_struct.hash_struct())
        return (
            salt,
            Account._sign_hash(signable_bytes, self.signing_key).signature.hex(),
        )

async def main():
    aevo = AevoClient(
        signing_key="",
        wallet_address="",
        api_key="",
        api_secret="",
        env="mainnet",
    )

    markets = aevo.get_markets("ETH")
    logger.info(markets)

    await aevo.open_connection()
    await aevo.subscribe_ticker("ticker:ETH:PERPETUAL")

    async for msg in aevo.read_messages():
        logger.info(msg)

def initialize():
    asyncio.run(main())