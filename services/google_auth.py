from google_auth_oauthlib.flow import Flow
from config.settings import CLIENT_SECRETS_FILE, SCOPES, REDIRECT_URI

def create_flow():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    return flow