# middleware/auth.py
from functools import wraps
from flask import session, redirect, jsonify, request

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        print("🔒 admin_required triggered", session.get("is_admin"))  # ← lägg till
        if not session.get("is_admin"):
            # API-anrop → JSON, sidanrop → redirect
            if request.is_json or request.path.startswith("/admin/clients") or \
               request.path.startswith("/admin/availability") or \
               request.path.startswith("/admin/book"):
                return jsonify({"error": "Unauthorized"}), 401
            return redirect("/admin/login")
        return f(*args, **kwargs)
    return decorated