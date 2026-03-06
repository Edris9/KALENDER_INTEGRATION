from flask import Flask
from flask import session, redirect
from routes.auth_routes import auth_bp
from routes.calendar_routes import calendar_bp
from flask import render_template
import os

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
app = Flask(__name__)
app.secret_key = "super_hemlig_nyckel_123"

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

if __name__ == "__main__":
    app.run(debug=False, port=5000)