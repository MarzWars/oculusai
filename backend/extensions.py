from config import Config
from supabase import create_client
from tavily import TavilyClient

# Validate configuration variables
if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
    raise Exception("Missing SUPABASE_URL or SUPABASE_KEY environment variables")

if not Config.TAVILY_API_KEY:
    raise Exception("Missing TAVILY_API_KEY environment variable")

if not Config.OPENROUTER_API_KEY:
    raise Exception("Missing OPENROUTER_API_KEY environment variable")

# Instantiate shared API clients
supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
tavily = TavilyClient(api_key=Config.TAVILY_API_KEY)
