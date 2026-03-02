from flask import Flask
from routes.auth_routes import auth_bp
from routes.calendar_routes import calendar_bp

app = Flask(__name__)
app.secret_key = "showcase_secret_key"

# Registrera routes
app.register_blueprint(auth_bp)
app.register_blueprint(calendar_bp)

if __name__ == "__main__":
    app.run(debug=True, port=5000)