from app import create_app

# Точка входа. 
app = create_app()

if __name__ == "__main__":
    # Порт 8088 
    app.run(host="0.0.0.0", port=8088, debug=True)
