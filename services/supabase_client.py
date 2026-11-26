from supabase import create_client
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Ambil URL dan KEY dari .env
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Buat client Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)