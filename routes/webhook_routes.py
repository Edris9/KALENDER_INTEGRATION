from flask import Blueprint, request, jsonify
from services.google.supabase_client import supabase

webhook_bp = Blueprint("webhook", __name__)

@webhook_bp.route("/webhook/google", methods=["POST"])
def google_webhook():
    resource_id = request.headers.get("X-Goog-Resource-ID")
    resource_uri = request.headers.get("X-Goog-Resource-URI")
    
    # Google skickar bara en notis — vi måste hämta event själva
    # Det gör vi i nästa steg
    print("Google webhook received:", resource_id)
    
    return "", 200