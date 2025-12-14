"""Configuration management for English Trainer."""

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    """Application configuration."""
    
    # API Configuration
    base_url: str = os.getenv("ENGLISH_RPG_BASE_URL", "http://localhost:3000/v1")
    api_key: str = os.getenv("ENGLISH_RPG_API_KEY", "dummy-key")
    model: str = os.getenv("ENGLISH_RPG_MODEL", "gpt-4o-mini")
    timeout: int = int(os.getenv("ENGLISH_RPG_TIMEOUT", "60"))
    
    # File paths
    save_file: Path = Path.home() / ".english_trainer_data.json"
    history_file: Path = Path.home() / ".english_trainer_history"
    notebook_file: Path = Path.home() / ".english_trainer_notebook.json"
    lock_file: Path = Path(tempfile.gettempdir()) / "english_trainer.lock"
    
    # UI Configuration
    max_context_chars: int = 6000
    max_attempts_history: int = 300
    max_reviews_display: int = 50
    
    # Learning Configuration
    xp_per_level: int = 100
    review_threshold_score: int = 6
    max_retry_attempts: int = 3
    
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
        


# Global configuration instance
config = Config.load()