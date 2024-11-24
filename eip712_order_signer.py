import time
import random
from eth_account import Account
from eth_utils import encode_hex, to_bytes
from web3 import Web3
from hashlib import sha3_256

# Define the EIP-712 Order structure
class Order:
    def __init__(self, maker, is_buy, limit_price, amount, salt, instrument, timestamp):
        self.maker = maker
        self.is_buy = is_buy
        self.limit_price = limit_price
        self.amount = amount
        self.salt = salt
        self.instrument = instrument
        self.timestamp = timestamp

# Keccak256 hash function
def keccak(data):
    return sha3_256(data).digest()

# Generate EIP-712 domain separator
def eip712_domain_separator(name, version, chain_id, verifying_contract):
    domain_type_hash = keccak(b"EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)")
    name_hash = keccak(to_bytes(text=name))
    version_hash = keccak(to_bytes(text=version))
    chain_id_bytes = chain_id.to_bytes(32, "big")
    verifying_contract_bytes = bytes.fromhex(verifying_contract[2:])

    domain_data = b"".join([
        domain_type_hash,
        name_hash,
        version_hash,
        chain_id_bytes,
        verifying_contract_bytes
    ])
    return encode_hex(keccak(domain_data))

# Hash the order struct for EIP-712 signing
def hash_order(order):
    order_type_hash = keccak(b"Order(address maker,bool isBuy,uint256 limitPrice,uint256 amount,uint256 salt,uint256 instrument,uint256 timestamp)")
    order_data = b"".join([
        order_type_hash,
        bytes.fromhex(order.maker[2:]),
        (1 if order.is_buy else 0).to_bytes(32, "big"),
        int(order.limit_price).to_bytes(32, "big"),
        int(order.amount).to_bytes(32, "big"),
        int(order.salt).to_bytes(32, "big"),
        int(order.instrument).to_bytes(32, "big"),
        int(order.timestamp).to_bytes(32, "big")
    ])
    return encode_hex(keccak(order_data))

# Sign the order using the signing key and domain separator
def sign_order_with_signing_key(order, signing_key, domain_separator):
    order_hash = hash_order(order)
    message_hash = keccak(b"\x19\x01" + bytes.fromhex(domain_separator[2:]) + bytes.fromhex(order_hash[2:]))
    
    # Create a SignableMessage object
    from eth_account.messages import encode_defunct
    signable_message = encode_defunct(message_hash)
    
    # Sign the message hash with the signing key
    signed_message = Account.sign_message(signable_message, private_key=signing_key)
    return signed_message.signature.hex()

# Example function to initialize and sign an order
def initialize_order(signing_key, wallet_address, env="testnet"):
    domain_config = {
        "testnet": {"name": "Aevo Testnet", "version": "1", "chain_id": 11155111},
        "mainnet": {"name": "Aevo Mainnet", "version": "1", "chain_id": 1},
    }

    if env not in domain_config:
        raise ValueError("Invalid environment specified. Choose 'testnet' or 'mainnet'.")

    domain = domain_config[env]
    verifying_contract = "0xcE78E39027A4A646162d3f1dcf917c7DBB69C38E"

    # Calculate the domain separator
    domain_separator = eip712_domain_separator(
        domain["name"],
        domain["version"],
        domain["chain_id"],
        verifying_contract
    )
    print(f"Domain Separator: {domain_separator}")

    # Create an example order
    order = Order(
        maker=wallet_address,
        is_buy=True,
        limit_price=int(100 * 10**18),  # Example price in wei
        amount=int(10 * 10**18),  # Example amount in wei
        salt=random.randint(1, 10**8),  # Random salt for uniqueness
        instrument=1,  # Instrument ID
        timestamp=int(time.time())
    )

    # Sign the order
    signature = sign_order_with_signing_key(order, signing_key, domain_separator)
    print(f"Order Signature: {signature}")
    return signature
