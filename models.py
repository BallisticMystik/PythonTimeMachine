from app_init import db
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet, InvalidToken

class Migration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    signing_key = db.Column(db.String(256), nullable=True)
    wallet_address = db.Column(db.String(256), nullable=True)
    api_key = db.Column(db.String(256), nullable=True)
    api_secret = db.Column(db.String(256), nullable=True)
    env = db.Column(db.String(10), nullable=True)
    encryption_key = db.Column(db.String(256), nullable=True)
    # balance column removed

    def __repr__(self):
        return f'<User {self.username}>'
    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        if not self.encryption_key:
            self.encryption_key = Fernet.generate_key().decode()
        self._cipher_suite = None  # Initialize _cipher_suite as None
        
    @property
    def cipher_suite(self):
        if not hasattr(self, '_cipher_suite') or self._cipher_suite is None:
            self._cipher_suite = Fernet(self.encryption_key.encode() if self.encryption_key else Fernet.generate_key())
        return self._cipher_suite

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def encrypt_data(self, data):
        if data is None:
            return None
        return self.cipher_suite.encrypt(data.encode()).decode()

    def decrypt_data(self, encrypted_data):
        if encrypted_data is None:
            return None
        try:
            return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
        except InvalidToken:
            return None

    def set_signing_key(self, signing_key):
        self.signing_key = self.encrypt_data(signing_key)

    def set_wallet_address(self, wallet_address):
        self.wallet_address = self.encrypt_data(wallet_address)

    def set_api_key(self, api_key):
        self.api_key = self.encrypt_data(api_key)

    def set_api_secret(self, api_secret):
        self.api_secret = self.encrypt_data(api_secret)

    def set_env(self, env):
        self.env = env

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    instrument_id = db.Column(db.String(50), nullable=True)
    instrument_name = db.Column(db.String(100), nullable=True)
    instrument_type = db.Column(db.String(50), nullable=True)
    amount = db.Column(db.Float, nullable=True)
    mark_price = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    account_percentage = db.Column(db.Float, nullable=True)
    leverage = db.Column(db.Integer, nullable=True)
    stoploss = db.Column(db.Float, nullable=True)
    ticker = db.Column(db.String(20), nullable=True)
    timeframe = db.Column(db.String(20), nullable=True)
    active = db.Column(db.Boolean, default=True)
    position = db.Column(db.String(10), nullable=True)
    immediate_entry = db.Column(db.Boolean, default=False)  # Added immediate_entry field
    task_id = db.Column(db.String(36), nullable=True)  # Added task_id field
    
    user = db.relationship('User', backref=db.backref('sessions', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'instrument_id': self.instrument_id,
            'instrument_name': self.instrument_name,
            'instrument_type': self.instrument_type,
            'amount': self.amount,
            'mark_price': self.mark_price,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'account_percentage': self.account_percentage,
            'leverage': self.leverage,
            'stoploss': self.stoploss,
            'ticker': self.ticker,
            'timeframe': self.timeframe,
            'active': self.active,
            'position': self.position,
            'immediate_entry': self.immediate_entry
        }