"""Environment and Supabase client (service role — trusted device only, bypasses RLS)."""

import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

_url = os.environ.get("SUPABASE_URL")
_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client | None = create_client(_url, _key) if _url and _key else None
