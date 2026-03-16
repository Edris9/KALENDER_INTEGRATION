from dotenv import load_dotenv
load_dotenv()
from flask import Flask
from flask import session, redirect
from routes.auth_routes import auth_bp
from routes.calendar_routes import calendar_bp
from flask import render_template
import os
from routes.admin_routes import admin_bp

from routes.microsoft_routes import ms_bp



os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
app = Flask(__name__)
app.secret_key = "super_hemlig_nyckel_123"

app.register_blueprint(admin_bp)

app.route("/admin_login")
def admin_login():
    return render_template("admin_login.html")

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/logout")
def logout():
    session.clear()
    return '''
    <script>
        document.cookie.split(";").forEach(function(c) { 
            document.cookie = c.replace(/^ +/, "")
            .replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/"); 
        });
        window.location.href = "/";
    </script>
    '''

# Registrera routes
app.register_blueprint(auth_bp)
app.register_blueprint(calendar_bp)
app.register_blueprint(ms_bp)
app.secret_key = "showcase_secret_key"
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False

if __name__ == "__main__":
    app.run(debug=False, port=5000)