import os

# Load .env manually if present
if os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-in-production")
    
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    
    TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

    # Unmoderated/general models fallback list
    OR_MODELS = [
        "nousresearch/hermes-3-llama-3.1-70b",                       # PAID - fast, cheap, unmoderated
        "openrouter/owl-alpha"
        "nvidia/nemotron-3-super-120b-a12b",                         # PAID - fast, cheap, moderated
        "meta-llama/llama-3.3-70b-instruct",                         # PAID - balanced, moderated
        "nousresearch/hermes-3-llama-3.1-405b",                      # PAID - powerful, unmoderated
        "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",  # FREE - Venice uncensored
        "nvidia/nemotron-3-super-120b-a12b:free",                         # FREE fallback
        "meta-llama/llama-3.3-70b-instruct:free",                         # FREE fallback
        "nousresearch/hermes-3-llama-3.1-405b:free",                      # FREE fallback
    ]

    # Models shown in manual switcher UI
    MODEL_OPTIONS = [
        {"id": "nousresearch/hermes-3-llama-3.1-70b",   "name": "Hermes 3 70B",          "tag": "Unmoderated · Fast · Cheap"},
        {"id": "openrouter/owl-alpha",   "name": "Owl Alpha",          "tag": "Testing"},
        {"id": "nvidia/nemotron-3-super-120b-a12b",    "name": "Nemotron 3 Super 120B", "tag": "Moderated · Fast · Cheap"},
        {"id": "meta-llama/llama-3.3-70b-instruct",    "name": "Llama 3.3 70B",         "tag": "Moderated · Balanced"},
        {"id": "nousresearch/hermes-3-llama-3.1-405b", "name": "Hermes 3 405B",          "tag": "Unmoderated · Powerful"},
        {"id": "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
                                                       "name": "Dolphin Mistral 24B",    "tag": "Uncensored · Free"},
    ]
    
    DEFAULT_MODEL = "openrouter/owl-alpha"
    OR_TIMEOUT = 45  # seconds
    
    VERBATIM_TURNS = 6
    SUMMARISE_AFTER = 10
