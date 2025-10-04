from flask import Flask
from .config import Config
from .extensions import cache
from .blueprints.main import bp as main_bp
from .blueprints.market import bp as market_bp

def create_app() -> Flask:
    """
    Фабрика Flask-приложения.
    Настраивает конфиг, расширения и блюпринты.
    """
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    # Инициализация расширений
    cache.init_app(app)

    # Регистрация blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(market_bp, url_prefix="/market")

    return app
