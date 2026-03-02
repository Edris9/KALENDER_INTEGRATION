from google_auth_oauthlib.flow import Flow
from config.settings import CLIENT_SECRETS_FILE, SCOPES, REDIRECT_URI

def create_flow():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    # Lägg till denna rad för att stänga av kravet på code_verifier
    flow.code_challenge_method = None 
    return flow