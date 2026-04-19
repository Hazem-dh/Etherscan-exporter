"""
core/state.py
Global application state shared across all UI modules.
"""


class AppState:
    _api_key: str = ""

    @classmethod
    def set_api_key(cls, key: str) -> None:
        cls._api_key = key.strip()

    @classmethod
    def get_api_key(cls) -> str:
        return cls._api_key

    @classmethod
    def has_api_key(cls) -> bool:
        return bool(cls._api_key)
