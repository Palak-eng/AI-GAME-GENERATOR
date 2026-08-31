"""Small helper for friendly backend status messages."""

import apiclient


def get_api_base_message(error: str | None = None) -> str:
    """Return a human-friendly hint about the configured API base URL."""
    base = apiclient.BASE_URL
    if error:
        return f"currently unreachable at {base} ({error})"
    return f"at {base}"
