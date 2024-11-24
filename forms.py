from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, EqualTo, Email, ValidationError, Length, Regexp
from wtforms import StringField, PasswordField, SubmitField, SelectField, FloatField, IntegerField, BooleanField
from wtforms.validators import DataRequired, EqualTo, Email, ValidationError
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()], render_kw={"placeholder": "Email"})
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, message="Password must be at least 8 characters long")])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already in use. Please choose a different one.')

class AccountForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    signing_key = StringField('Signing Key', validators=[DataRequired()])
    wallet_address = StringField('Wallet Address', validators=[DataRequired()])
    api_key = StringField('API Key', validators=[DataRequired()])
    api_secret = StringField('API Secret', validators=[DataRequired()])
    env = SelectField('Environment', choices=[('mainnet', 'Mainnet'), ('testnet', 'Testnet')])
    submit = SubmitField('Update Configuration')

class CreateSessionForm(FlaskForm):
    account_percentage = FloatField('Account Percentage', validators=[DataRequired()])
    leverage = SelectField('Leverage', choices=[(0, '0x'), (2, '2x'), (5, '5x'), (10, '10x'), (20, '20x')], coerce=int, validators=[DataRequired()])
    stoploss = FloatField('Stop Loss', validators=[DataRequired()])
    ticker = SelectField('Ticker', choices=[('BTC-PERP', 'BTC-PERP'), ('SOL-PERP', 'SOL-PERP'), ('ETH-PERP', 'ETH-PERP')], validators=[DataRequired()])
    timeframe = SelectField('Timeframe', choices=[('1min', '1min'), ('5min', '5min'), ('15min', '15min'), ('1h', '1h'), ('4h', '4h'), ('1d', '1d')], validators=[DataRequired()])
    position = SelectField('Position', choices=[('long', 'Long'), ('short', 'Short')], validators=[DataRequired()])
    immediate_entry = BooleanField('Immediate Entry')
    submit = SubmitField('Create Session')
    submit = SubmitField('Create Session')