"""Configuration management for English Trainer."""

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    """Application configuration."""

    # API Configuration
    base_url: str = os.getenv("ENGLISH_RPG_BASE_URL", "http://localhost:3000/v1")
    api_key: str = os.getenv("ENGLISH_RPG_API_KEY", "dummy-key")
    model: str = os.getenv("ENGLISH_RPG_MODEL", "gpt-5-mini")
    timeout: int = int(os.getenv("ENGLISH_RPG_TIMEOUT", "60"))

    # Performance Configuration
    max_parallel_requests: int = int(os.getenv("ENGLISH_RPG_MAX_PARALLEL", "5"))
    cache_enabled: bool = (
        os.getenv("ENGLISH_RPG_CACHE_ENABLED", "true").lower() == "true"
    )
    cache_size: int = int(os.getenv("ENGLISH_RPG_CACHE_SIZE", "256"))

    # File paths
    save_file: Path = Path.home() / ".english_trainer_data.json"
    history_file: Path = Path.home() / ".english_trainer_history"
    notebook_file: Path = Path.home() / ".english_trainer_notebook.json"
    lock_file: Path = Path(tempfile.gettempdir()) / "english_trainer.lock"

    # UI Configuration
    max_context_chars: int = 6000
    max_attempts_history: int = 100  # Reduced from 300 to save memory
    max_reviews_display: int = 50

    # Learning Configuration
    xp_per_level: int = 100
    review_threshold_score: int = 6
    max_retry_attempts: int = 3
    max_recent_phrases: int = 20  # Track last 20 phrases to avoid repetition
    max_error_tracking: int = 50  # Track up to 50 most common errors

    @classmethod
    def load(cls) -> "Config":
        """Load configuration with environment variable overrides."""
        return cls()

    def validate(self) -> None:
        """Validate configuration values."""
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        if self.xp_per_level <= 0:
            raise ValueError("XP per level must be positive")
        if not self.base_url:
            raise ValueError("Base URL cannot be empty")
        if self.max_parallel_requests <= 0:
            raise ValueError("Max parallel requests must be positive")
        if self.cache_size <= 0:
            raise ValueError("Cache size must be positive")
        if self.max_attempts_history <= 0:
            raise ValueError("Max attempts history must be positive")
        if self.max_recent_phrases <= 0:
            raise ValueError("Max recent phrases must be positive")
        if self.max_error_tracking <= 0:
            raise ValueError("Max error tracking must be positive")


# Global configuration instance
config = Config.load()
