from config import Config
from celery import Celery
from eip712_order_signer import eip712_domain_separator, hash_order, sign_order_with_signing_key, initialize_order
from routes.sessions import initialize_aevo_client
from websocket_controller import WebSocketController

from app_init import create_app, db
from cryptography.fernet import InvalidToken
from werkzeug.utils import secure_filename
from AlethieumAevoSDK import AevoClient
from forms import AccountForm, LoginForm, RegistrationForm
from models import User
from flask import render_template
import logging
import json
import os
import asyncio

from models import Migration
from sqlalchemy import text
import logging
import os

def run_migrations(app):
    migration_folder = os.path.join(app.root_path, 'migrations')
    if not os.path.exists(migration_folder):
        logging.info("No migrations folder found. Skipping migrations.")
        return
    with app.app_context():
        db.create_all()
        migration_files = sorted(f for f in os.listdir(migration_folder) if f.endswith('.sql'))
        for migration_file in migration_files:
            migration_record = Migration.query.filter_by(name=migration_file).first()
            if migration_record is None:
                with open(os.path.join(migration_folder, migration_file), 'r') as file:
                    migration_sql = file.read()
                logging.info(f"Running migration: {migration_file}")
                for statement in migration_sql.split(';'):
                    if statement.strip():
                        db.session.execute(text(statement.strip()))
                new_migration = Migration(name=migration_file)
                db.session.add(new_migration)
                db.session.commit()
                logging.info(f"Migration {migration_file} completed successfully.")
            else:
                logging.info(f"Migration {migration_file} already applied. Skipping.")
        logging.info("All migrations completed successfully.")

app = create_app()
app.config['UPLOAD_FOLDER'] = 'static/videos'
app.config['CELERY_BROKER_URL'] = Config.CELERY_BROKER_URL
app.config['CELERY_RESULT_BACKEND'] = Config.CELERY_RESULT_BACKEND
with app.app_context():
    db.create_all()
    run_migrations(app)
    db.session.commit()

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Import all route modules
from routes.api import api_bp
import routes.auth
app.register_blueprint(api_bp)
import routes.dashboard
import routes.account
import routes.charts
import routes.sessions
import routes.create_session

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

celery = make_celery(app)

# Add WebSocket route
@app.route('/ws')
def websocket():
    return "WebSocket endpoint"

if __name__ == "__main__":
    # Initialize EIP-712 domain separator
    from eip712_order_signer import initialize_order
    initialize_order(os.environ.get('AEVO_SIGNING_KEY'), os.environ.get('WALLET_ADDRESS'), os.environ.get('ENV', 'testnet'))
    
    # Initialize Aevo client and WebSocket connection in a background task
    async def init_websocket():
        aevo_client = initialize_aevo_client()
        await aevo_client.open_connection()
        app.config['AEVO_CLIENT'] = aevo_client
        ws_controller = WebSocketController(aevo_client)
        app.config['WS_CONTROLLER'] = ws_controller
        await ws_controller.subscribe_to_orders()
    
    # Create event loop and run websocket initialization
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(init_websocket())
    aevo_client = initialize_aevo_client()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(aevo_client.open_connection())
    app.config['AEVO_CLIENT'] = aevo_client
    
    # Initialize WebSocket controller
    ws_controller = WebSocketController(aevo_client)
    app.config['WS_CONTROLLER'] = ws_controller
    
    # Start WebSocket subscription in a background task
    asyncio.get_event_loop().create_task(ws_controller.subscribe_to_orders())
    
    # Run the Flask application
    app.run(debug=True, host='0.0.0.0', port=8080)
