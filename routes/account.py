from flask import render_template, request, flash, redirect, url_for
from app_init import app, db
from models import User
from aevo_client import AevoClient
from forms import AccountForm
from sqlalchemy.exc import IntegrityError
import os
import requests
import json
import time
import hmac
import hashlib

def get_headers(path, method, body):
    timestamp = str(time.time_ns())
    message = f"{os.environ['AEVO_API_KEY']},{timestamp},{method.upper()},{path},{body}".encode("utf-8")
    signature = hmac.new(os.environ['AEVO_API_SECRET'].encode("utf-8"), message, hashlib.sha256).hexdigest()

    headers = {
        "AEVO-TIMESTAMP": timestamp,
        "AEVO-SIGNATURE": signature,
        "AEVO-KEY": os.environ['AEVO_API_KEY'],
        "accept": "application/json",
        "content-type": "application/json"
    }

    return headers

@app.route('/account_config', methods=['GET', 'POST'])
def account_config():
    form = AccountForm()
    user = User.query.first()  # Assuming we're working with a single user for now
    if request.method == 'POST':
        if form.validate_on_submit():
            if user:
                try:
                    # Check if the username is being changed
                    if user.username != form.username.data:
                        existing_user = User.query.filter_by(username=form.username.data).first()
                        if existing_user:
                            flash('Username already exists. Please choose a different one.', 'error')
                            return render_template('account.html', form=form, user=user)
                    
                    user.username = form.username.data
                    user.set_signing_key(form.signing_key.data)
                    user.set_wallet_address(form.wallet_address.data)
                    user.set_api_key(form.api_key.data)
                    user.set_api_secret(form.api_secret.data)
                    user.set_env(form.env.data)
                    db.session.commit()
                    flash('Your account configuration has been updated successfully.', 'success')
                    
                    # Fetch account information
                    url = "https://api.aevo.xyz/account"
                    headers = get_headers("/account", "GET", "")
                    response = requests.get(url, headers=headers)
                    if response.status_code == 200:
                        account_info = response.json()
                        flash(f'Successfully connected to Aevo. Account info: {json.dumps(account_info, indent=2)}', 'success')
                        print("Aevo connection test: Success")
                    else:
                        flash(f'Failed to connect to Aevo: {response.text}', 'error')
                        print(f"Aevo connection test: Failed - {response.text}")
                except IntegrityError:
                    db.session.rollback()
                    flash('An error occurred while updating your account. Please try again.', 'error')
                    print("Account configuration update: Failed (IntegrityError)")
                except Exception as e:
                    db.session.rollback()
                    flash(f'An error occurred: {str(e)}', 'error')
                    print(f"Account configuration update: Failed - {str(e)}")
                print(f"Account configuration update status: {'Success' if not form.errors else 'Failed'}")
                if not form.errors:
                    return redirect(url_for('dashboard'))
                return redirect(url_for('account_config'))
    
    if user:
        form.username.data = user.username
        form.signing_key.data = user.decrypt_data(user.signing_key) if user.signing_key else ''
        form.wallet_address.data = user.decrypt_data(user.wallet_address) if user.wallet_address else ''
        form.api_key.data = user.decrypt_data(user.api_key) if user.api_key else ''
        form.api_secret.data = user.decrypt_data(user.api_secret) if user.api_secret else ''
        form.env.data = user.env if user.env else ''
    
    return render_template('account.html', form=form, user=user)
