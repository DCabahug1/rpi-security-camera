"""Environment and Supabase client."""

import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

_url = os.environ.get("SUPABASE_URL")
_key = os.environ.get("SUPABASE_PUBLISHABLE_KEY")
supabase: Client | None = create_client(_url, _key) if _url and _key else None
