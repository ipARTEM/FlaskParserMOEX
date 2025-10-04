from flask import Blueprint, render_template, current_app

bp = Blueprint("main", __name__)

@bp.get("/")
def index():
    # Передаём динамический заголовок
    return render_template("index.html", page_title="FlaskParserMOEX — Главная")

@bp.get("/contacts")
def contacts():
    # Данные о контактах — динамически (можно взять из .env/конфига/БД)
    contact_info = {
        "author": "Artem Khimin",
        "email": "a.khimin@yandex.ru",
        "github": "https://github.com/ipARTEM",
    }
    return render_template("contacts.html",
                           page_title="Контакты",
                           contacts=contact_info)
