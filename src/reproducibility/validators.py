import os
import re
import html
from typing import Dict, Any, List, Union

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and unsafe character issues.
    """
    if not filename:
        return "unnamed_export"
    # Remove directory separators and path traversal attempts
    cleaned = os.path.basename(filename)
    cleaned = re.sub(r'[\/\\:\*\?"<>\|]', '_', cleaned)
    cleaned = re.sub(r'\.\.+', '.', cleaned)
    cleaned = cleaned.strip('. ')
    return cleaned or "unnamed_export"

def validate_safe_path(base_dir: str, target_path: str) -> bool:
    """
    Ensure target_path stays strictly within base_dir to prevent path traversal.
    """
    base_abs = os.path.abspath(base_dir)
    target_abs = os.path.abspath(target_path)
    return target_abs.startswith(base_abs)

def escape_html_value(val: Any) -> str:
    """
    Safely escape a value for inclusion in HTML documents to prevent XSS.
    """
    if val is None:
        return ""
    return html.escape(str(val))

def filter_secrets(data: Union[Dict[str, Any], List[Any], str, int, float, bool, None]) -> Any:
    """
    Recursively remove secret key patterns (API keys, credentials, tokens, local machine paths) from data.
    """
    SECRET_KEYS = {"ncbi_api_key", "api_key", "password", "secret", "token", "auth"}
    
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            if any(s in k.lower() for s in SECRET_KEYS):
                cleaned[k] = "[REDACTED_SECRET]"
            else:
                cleaned[k] = filter_secrets(v)
        return cleaned
    elif isinstance(data, list):
        return [filter_secrets(item) for item in data]
    else:
        return data
