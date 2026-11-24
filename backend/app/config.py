"""Configuration management for MiroFish."""
import os
from dotenv import load_dotenv

project_root_env = os.path.join(os.path.dirname(__file__), "../../.env")
if os.path.exists(project_root_env):
    load_dotenv(project_root_env, override=True)
else:
    load_dotenv(override=True)


class Config:
    """Flask configuration loaded from environment variables."""

    # No insecure built-in fallback. Set a unique random value in deployment.
    SECRET_KEY = os.environ.get("SECRET_KEY")
    DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() == "true"

    # API protection: keep this value server-side. Never place it in VITE_*.
    API_AUTH_TOKEN = os.environ.get("API_AUTH_TOKEN")
    ALLOW_INSECURE_LOCAL_DEV = os.environ.get("ALLOW_INSECURE_LOCAL_DEV", "false").lower() == "true"
    CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "")
    API_RATE_LIMIT_PER_MINUTE = int(os.environ.get("API_RATE_LIMIT_PER_MINUTE", "60"))
    API_EXPENSIVE_RATE_LIMIT_PER_MINUTE = int(os.environ.get("API_EXPENSIVE_RATE_LIMIT_PER_MINUTE", "5"))
    API_EXPENSIVE_PATH_PREFIXES = (
        "/api/graph/ontology",
        "/api/graph/build",
        "/api/simulation",
        "/api/report",
    )

    JSON_AS_ASCII = False
    LLM_API_KEY = os.environ.get("LLM_API_KEY")
    LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
    LLM_MODEL_NAME = os.environ.get("LLM_MODEL_NAME", "gpt-4o-mini")
    ZEP_API_KEY = os.environ.get("ZEP_API_KEY")

    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "../uploads")
    ALLOWED_EXTENSIONS = {"pdf", "md", "txt", "markdown"}

    DEFAULT_CHUNK_SIZE = 500
    DEFAULT_CHUNK_OVERLAP = 50
    OASIS_DEFAULT_MAX_ROUNDS = int(os.environ.get("OASIS_DEFAULT_MAX_ROUNDS", "10"))
    OASIS_SIMULATION_DATA_DIR = os.path.join(os.path.dirname(__file__), "../uploads/simulations")

    OASIS_TWITTER_ACTIONS = [
        "CREATE_POST", "LIKE_POST", "REPOST", "FOLLOW", "DO_NOTHING", "QUOTE_POST"
    ]
    OASIS_REDDIT_ACTIONS = [
        "LIKE_POST", "DISLIKE_POST", "CREATE_POST", "CREATE_COMMENT",
        "LIKE_COMMENT", "DISLIKE_COMMENT", "SEARCH_POSTS", "SEARCH_USER",
        "TREND", "REFRESH", "DO_NOTHING", "FOLLOW", "MUTE"
    ]

    REPORT_AGENT_MAX_TOOL_CALLS = int(os.environ.get("REPORT_AGENT_MAX_TOOL_CALLS", "5"))
    REPORT_AGENT_MAX_REFLECTION_ROUNDS = int(os.environ.get("REPORT_AGENT_MAX_REFLECTION_ROUNDS", "2"))
    REPORT_AGENT_TEMPERATURE = float(os.environ.get("REPORT_AGENT_TEMPERATURE", "0.5"))

    @classmethod
    def validate(cls) -> list[str]:
        errors: list[str] = []
        if not cls.LLM_API_KEY:
            errors.append("LLM_API_KEY not configured")
        if not cls.ZEP_API_KEY:
            errors.append("ZEP_API_KEY not configured")
        if not cls.API_AUTH_TOKEN and not cls.ALLOW_INSECURE_LOCAL_DEV:
            errors.append("API_AUTH_TOKEN must be configured (or explicitly enable local-only development bypass)")
        if not cls.SECRET_KEY or len(cls.SECRET_KEY) < 32:
            errors.append("SECRET_KEY must be set to a random value of at least 32 characters")
        if os.environ.get("ZEP_API_URL"):
            errors.append("ZEP_API_URL is unsupported; MiroFish connects to Zep Cloud only")
        if cls.DEBUG:
            import warnings
            warnings.warn("Flask DEBUG mode is enabled. Do not use in production.", RuntimeWarning)
        return errors
