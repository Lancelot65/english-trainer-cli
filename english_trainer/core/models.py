"""Data models for English Trainer."""

import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
from collections import Counter

from .config import config


@dataclass
class Attempt:
    """Represents a translation attempt."""

    ts: float
    paragraph_fr: str
    translation_en: str
    score: int
    main_error: str = ""
    lesson_focus: str = ""
    theme: str = ""

    @property
    def formatted_date(self) -> str:
        """Return formatted date string."""
        return time.strftime("%Y-%m-%d %H:%M", time.localtime(self.ts))


@dataclass
class ReviewItem:
    """Represents an item for spaced repetition review."""

    paragraph_fr: str
    due_ts: float
    interval_days: int = 0
    difficulty: float = 1.0  # 1.0 = normal, >1.0 = harder

    @property
    def is_due(self) -> bool:
        """Check if review is due."""
        return self.due_ts <= time.time()

    @property
    def days_until_due(self) -> int:
        """Days until review is due (negative if overdue)."""
        return int((self.due_ts - time.time()) / 86400)


@dataclass
class NotebookEntry:
    """Represents a saved lesson in the notebook."""

    title: str
    content: str
    topic: str
    created_ts: float
    tags: List[str] = field(default_factory=list)
    favorite: bool = False

    @property
    def formatted_date(self) -> str:
        """Return formatted creation date."""
        return time.strftime("%Y-%m-%d %H:%M", time.localtime(self.created_ts))


@dataclass
class DailyChallenge:
    """Represents a daily challenge."""

    date: str  # YYYY-MM-DD
    challenge_type: str
    title: str
    description: str
    instructions: str
    example: str
    tips: List[str] = field(default_factory=list)
    xp_reward: int = 10
    completed: bool = False
    completion_date: Optional[float] = None

    def mark_completed(self) -> None:
        """Mark challenge as completed."""
        self.completed = True
        self.completion_date = time.time()


@dataclass
class Settings:
    """User settings."""

    model: str = "gpt-5-mini"
    temperature: float = 0.7
    auto_save_lessons: bool = True
    show_detailed_feedback: bool = True
    difficulty_preference: str = "adaptive"  # "easy", "normal", "hard", "adaptive"
    ui_theme: str = "modern"  # "classic", "modern", "minimal"
    custom_theme: Dict[str, str] = field(default_factory=dict)


@dataclass
class TrainerState:
    """Main application state."""

    xp: int = 0
    total_exercises: int = 0
    current_lesson: str = ""
    current_theme: str = ""
    attempts: List[Attempt] = field(default_factory=list)
    review: List[ReviewItem] = field(default_factory=list)
    notebook: List[NotebookEntry] = field(default_factory=list)
    settings: Settings = field(default_factory=Settings)

    # New fields for enhanced features
    daily_challenges: List[DailyChallenge] = field(default_factory=list)
    # Achievements removed — kept state minimal

    # Error tracking and phrase history
    error_frequency: Dict[str, int] = field(default_factory=dict)
    recent_phrases: List[str] = field(default_factory=list)

    @property
    def level_num(self) -> int:
        """Current level number."""
        return 1 + (self.xp // 100)

    @property
    def level_name(self) -> str:
        """Current level name."""
        level = self.level_num
        if level <= 2:
            return "A1 - Débutant"
        if level <= 5:
            return "A2 - Élémentaire"
        if level <= 10:
            return "B1 - Intermédiaire"
        if level <= 15:
            return "B2 - Avancé"
        if level <= 20:
            return "C1 - Autonome"

        return "C2 - Maîtrise"

    @property
    def level_progress(self) -> float:
        """Progress within current level (0.0 to 1.0)."""
        prev_level_xp = (self.level_num - 1) * 100
        progress = self.xp - prev_level_xp
        return max(0.0, min(1.0, progress / 100.0))

    @property
    def recent_performance(self) -> float:
        """Average score of last 10 attempts."""
        if not self.attempts:
            return 0.0
        recent = self.attempts[-10:]
        return sum(a.score for a in recent) / len(recent)

    @property
    def due_reviews(self) -> List[ReviewItem]:
        """Get all due reviews sorted by urgency."""
        due = [r for r in self.review if r.is_due]
        return sorted(due, key=lambda x: x.due_ts)

    @property
    def today_challenge(self) -> Optional[DailyChallenge]:
        """Get today's challenge if it exists."""
        today = datetime.now().strftime("%Y-%m-%d")
        for challenge in self.daily_challenges:
            if challenge.date == today:
                return challenge
        return None

    @property
    def pending_challenges(self) -> List[DailyChallenge]:
        """Get all pending (uncompleted) challenges."""
        return [c for c in self.daily_challenges if not c.completed]

    @property
    def most_common_errors(self) -> List[Tuple[str, int]]:
        """Get most common errors, sorted by frequency."""
        return Counter(self.error_frequency).most_common(config.max_error_tracking)

    def add_attempt(self, attempt: Attempt) -> None:
        """Add a new attempt and maintain history limit."""
        self.attempts.append(attempt)
        if len(self.attempts) > config.max_attempts_history:
            self.attempts = self.attempts[-config.max_attempts_history :]

        # Track errors
        if attempt.main_error:
            error_key = attempt.main_error.strip().lower()
            self.error_frequency[error_key] = self.error_frequency.get(error_key, 0) + 1

        # Track recent phrases
        self.recent_phrases.append(attempt.paragraph_fr)
        if len(self.recent_phrases) > config.max_recent_phrases:
            self.recent_phrases = self.recent_phrases[-config.max_recent_phrases :]

    def add_notebook_entry(self, entry: NotebookEntry) -> None:
        """Add a new notebook entry."""
        self.notebook.append(entry)

    def get_notebook_by_topic(self, topic: str) -> List[NotebookEntry]:
        """Get notebook entries filtered by topic."""
        return [
            entry for entry in self.notebook if entry.topic.lower() == topic.lower()
        ]

    def search_notebook(self, query: str) -> List[NotebookEntry]:
        """Search notebook entries by title, content, or tags."""
        query = query.lower()
        results = []
        for entry in self.notebook:
            if (
                query in entry.title.lower()
                or query in entry.content.lower()
                or any(query in tag.lower() for tag in entry.tags)
            ):
                results.append(entry)
        return results

    def add_daily_challenge(self, challenge: DailyChallenge) -> None:
        """Add a daily challenge."""
        # Check if challenge for this date already exists
        for existing in self.daily_challenges:
            if existing.date == challenge.date:
                # Update existing challenge
                existing.challenge_type = challenge.challenge_type
                existing.title = challenge.title
                existing.description = challenge.description
                existing.instructions = challenge.instructions
                existing.example = challenge.example
                existing.tips = challenge.tips
                existing.xp_reward = challenge.xp_reward
                return

        # Add new challenge
        self.daily_challenges.append(challenge)

    def complete_today_challenge(self) -> bool:
        """Complete today's challenge and return XP reward."""
        today = datetime.now().strftime("%Y-%m-%d")
        for challenge in self.daily_challenges:
            if challenge.date == today and not challenge.completed:
                challenge.mark_completed()
                self.xp += challenge.xp_reward
                return True
        return False
