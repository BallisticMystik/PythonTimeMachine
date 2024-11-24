from flask import render_template
from app_init import app

@app.route('/charts')
def charts():
    return render_template('charts.html')