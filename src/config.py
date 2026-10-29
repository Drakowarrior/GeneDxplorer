import os
import logging

class ConfigError(ValueError):
    """Exception raised for invalid runtime configuration."""
    pass

class Settings:
    """
    Centralized, environment-driven application configuration.
    Validates environment settings at startup.
    """
    def __init__():
        pass

def get_env_str(key: str, default: str) -> str:
    return os.environ.get(key, default).strip()

def get_env_int(key: str, default: int) -> int:
    val_str = os.environ.get(key, str(default)).strip()
    try:
        val = int(val_str)
        if val < 0:
            raise ConfigError(f"Configuration key '{key}' must be a non-negative integer. Got: {val}")
        return val
    except ValueError as e:
        if isinstance(e, ConfigError):
            raise
        raise ConfigError(f"Configuration key '{key}' must be a valid integer. Got: '{val_str}'")

def get_env_float(key: str, default: float) -> float:
    val_str = os.environ.get(key, str(default)).strip()
    try:
        val = float(val_str)
        if val < 0:
            raise ConfigError(f"Configuration key '{key}' must be a non-negative float. Got: {val}")
        return val
    except ValueError as e:
        if isinstance(e, ConfigError):
            raise
        raise ConfigError(f"Configuration key '{key}' must be a valid float. Got: '{val_str}'")


class AppConfig:
    def __init__(self):
        self.GENEDXPLORER_VERSION = get_env_str("GENEDXPLORER_VERSION", "1.1.0")
        self.ANALYSIS_SCHEMA_VERSION = get_env_int("ANALYSIS_SCHEMA_VERSION", 1)
        self.SNAPSHOT_SCHEMA_VERSION = get_env_int("SNAPSHOT_SCHEMA_VERSION", 1)
        
        # NCBI Entrez Credentials & Pacing
        self.NCBI_EMAIL = get_env_str("NCBI_EMAIL", "genedxplorer.user@ncbi.nlm.nih.gov")
        self.NCBI_API_KEY = get_env_str("NCBI_API_KEY", "")
        self.NCBI_BATCH_SIZE = get_env_int("NCBI_BATCH_SIZE", 100)
        self.NCBI_REQUEST_DELAY = get_env_float("NCBI_REQUEST_DELAY", 0.2)
        
        # Retrieval & Analysis Limit
        self.ANALYSIS_LIMIT = get_env_int("ANALYSIS_LIMIT", 500)
        if self.ANALYSIS_LIMIT == 0:
            raise ConfigError("ANALYSIS_LIMIT must be greater than 0.")

        # Caching
        self.CACHE_TTL = get_env_int("CACHE_TTL", 3600)
        
        # Logging
        self.LOG_LEVEL = get_env_str("LOG_LEVEL", "INFO").upper()
        if self.LOG_LEVEL not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ConfigError(f"Invalid LOG_LEVEL: '{self.LOG_LEVEL}'. Must be one of DEBUG, INFO, WARNING, ERROR, CRITICAL.")

        # Server & Security
        self.API_HOST = get_env_str("API_HOST", "127.0.0.1")
        self.API_PORT = get_env_int("API_PORT", 8000)
        if not (1 <= self.API_PORT <= 65535):
            raise ConfigError(f"API_PORT must be between 1 and 65535. Got: {self.API_PORT}")

        raw_origins = get_env_str("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://127.0.0.1:5174")
        self.ALLOWED_ORIGINS = [o.strip() for o in raw_origins.split(",") if o.strip()]

        # Evidence Providers Configuration
        raw_providers = get_env_str("EVIDENCE_PROVIDERS", "medgen,clinvar")
        self.EVIDENCE_PROVIDERS = [p.strip().lower() for p in raw_providers.split(",") if p.strip()]

        # Knowledge Graph Exploration Configuration
        self.GRAPH_MAX_NODES = get_env_int("GRAPH_MAX_NODES", 50)
        if self.GRAPH_MAX_NODES < 5:
            raise ConfigError("GRAPH_MAX_NODES must be at least 5.")

        self.GRAPH_MAX_EDGES = get_env_int("GRAPH_MAX_EDGES", 100)
        if self.GRAPH_MAX_EDGES < 5:
            raise ConfigError("GRAPH_MAX_EDGES must be at least 5.")

        self.GRAPH_MAX_HOPS = get_env_int("GRAPH_MAX_HOPS", 2)
        if not (1 <= self.GRAPH_MAX_HOPS <= 5):
            raise ConfigError("GRAPH_MAX_HOPS must be between 1 and 5.")



    def validate_production(self):
        """Strict validation for production deployments."""
        if "*" in self.ALLOWED_ORIGINS:
            logging.warning("SECURITY WARNING: Wildcard ALLOWED_ORIGINS '*' is configured. Avoid this in production.")
        if self.NCBI_EMAIL == "genedxplorer.user@ncbi.nlm.nih.gov":
            logging.info("Using default fallback email for NCBI. Consider providing your specific NCBI_EMAIL.")

# Global Singleton Config Instance
config = AppConfig()
