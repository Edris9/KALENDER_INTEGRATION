import os
import json
from google_auth_oauthlib.flow import Flow
from config.settings import SCOPES, REDIRECT_URI

def create_flow():
    credentials_json = os.environ.get("GOOGLE_CREDENTIALS")
    
    if credentials_json:
        client_config = json.loads(credentials_json)
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
    else:
        from config.settings import CLIENT_SECRETS_FILE
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
    
    return flow