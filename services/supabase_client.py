import os
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://nyhxkzjcxhljtzrwujde.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im55aHhrempjeGhsanR6cnd1amRlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMwMDY1NTYsImV4cCI6MjA4ODU4MjU1Nn0.MR0CzPl8nQiADYmFrBr7WNDh7vU_Thyvq8Nm5ilPwGE")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)