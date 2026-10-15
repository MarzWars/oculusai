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
        "nvidia/nemotron-3.5-lightning:free",                       # PAID - fast, cheap, unmoderated
        "thinkingmachines/inkling-small:free"
        "nvidia/nemotron-3-super-120b-a12b",                         # PAID - fast, cheap, moderated
        "cohere/north-mini-code:free",                         # PAID - balanced, moderated
        "nvidia/nemotron-3-ultra-550b-a55b:free",                      # PAID - powerful, unmoderated
        "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",  # FREE - Venice uncensored
        "nvidia/nemotron-3-super-120b-a12b:free",                         # FREE fallback
        "meta-llama/llama-3.3-70b-instruct:free",
        "liquid/lfm-2.5-2.6b:free",                         # FREE fallback
        "nousresearch/hermes-3-llama-3.1-405b:free",                      # FREE fallback
    ]

    # Models shown in manual switcher UI
    MODEL_OPTIONS = [
        {"id": "nvidia/nemotron-3.5-lightning:free",   "name": "Nemo",          "tag": "Free"},
        {"id": "thinkingmachines/inkling-small:free",   "name": "Inkling",          "tag": "Free"},
        {"id": "liquid/lfm-2.5-2.6b:free",   "name": "Liquid",          "tag": "Uncensored · Free"},
        {"id": "nvidia/nemotron-3-super-120b-a12b",    "name": "Nemotron 3 Super 120B", "tag": "Moderated · Fast · Cheap"},
        {"id": "cohere/north-mini-code:free",    "name": "North",         "tag": "Free"},
        {"id": "nvidia/nemotron-3-ultra-550b-a55b:free", "name": "Nemo Ultra",          "tag": "Free · Powerful"},
        {"id": "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
                                                       "name": "Dolphin Mistral 24B",    "tag": "Uncensored · Free"},
    ]
    
    DEFAULT_MODEL = "liquid/lfm-2.5-2.6b:free"
    OR_TIMEOUT = 45  # seconds
    
    VERBATIM_TURNS = 6
    SUMMARISE_AFTER = 10
