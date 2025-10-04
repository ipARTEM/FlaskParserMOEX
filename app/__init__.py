# app/__init__.py
from flask import Flask
from .config import Config
from .extensions import cache

# ИМПОРТИРУЕМ ТОЛЬКО ИЗ routes
from .blueprints.main.routes import bp as main_bp
from .blueprints.market.routes import bp as market_bp

def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    cache.init_app(app)

    app.register_blueprint(main_bp)
    app.register_blueprint(market_bp, url_prefix="/market")
    return app
