import os
import logging
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('web')

# Set up database
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# Import models after creating db to avoid circular imports
from database.models import User, Order, Payment, OrderStatus, Notification, Subscription, OrderState

# Routes
@app.route('/')
def index():
    """Render the main dashboard."""
    return render_template('index.html')

@app.route('/api/status')
def status():
    """API endpoint for bot status."""
    return jsonify({
        'status': 'online',
        'uptime': '...',
        'bot_version': '1.0.0',
        'api_version': '1.0.0'
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    logger.error(f"Server error: {error}")
    return render_template('500.html'), 500

# Initialize database and tables
with app.app_context():
    db.create_all()
    logger.info("Database tables created successfully!")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)