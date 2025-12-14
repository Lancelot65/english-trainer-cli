"""Data storage and persistence management."""

import time
from dataclasses import asdict
from typing import Dict, List, Any

from ..core.config import config
from ..core.models import (
    TrainerState,
    Attempt,
    ReviewItem,
    NotebookEntry,
    Settings,
    DailyChallenge,
)
from ..utils.file_utils import atomic_write_json, safe_read_json
from ..utils.json_utils import clamp_int


class StorageManager:
    """Manages data persistence for the application."""

    @staticmethod
    def save_state(state: TrainerState) -> None:
        """Save trainer state to file."""
        try:
            data = asdict(state)
            atomic_write_json(config.save_file, data)
        except Exception as e:
            raise RuntimeError(f"Failed to save state: {e}")

    @staticmethod
    def load_state() -> TrainerState:
        """Load trainer state from file."""
        try:
            data = safe_read_json(config.save_file)
            return StorageManager._deserialize_state(data)
        except Exception:
            # Return default state if loading fails
            return TrainerState()

    @staticmethod
    def _deserialize_state(data: Dict[str, Any]) -> TrainerState:
        """Deserialize state data with validation."""
        state = TrainerState(
            xp=clamp_int(data.get("xp", 0), 0, 10**9, 0),
            total_exercises=clamp_int(data.get("total_exercises", 0), 0, 10**9, 0),
            current_lesson=str(data.get("current_lesson", "") or ""),
            current_theme=str(data.get("current_theme", "") or ""),
            # error_frequency and recent_phrases initialization moved here
            error_frequency=dict(data.get("error_frequency", {})),
            recent_phrases=list(data.get("recent_phrases", [])),
        )

        # Load settings
        settings_data = data.get("settings", {})
        if isinstance(settings_data, dict):
            state.settings = Settings(
                model=str(settings_data.get("model", config.model) or config.model),
                temperature=float(settings_data.get("temperature", 0.7) or 0.7),
                auto_save_lessons=bool(settings_data.get("auto_save_lessons", True)),
                show_detailed_feedback=bool(
                    settings_data.get("show_detailed_feedback", True)
                ),
                difficulty_preference=str(
                    settings_data.get("difficulty_preference", "adaptive")
                ),
                ui_theme=str(settings_data.get("ui_theme", "modern")),
                custom_theme=dict(settings_data.get("custom_theme", {})),
            )

        # Load attempts
        attempts_data = data.get("attempts", [])
        if isinstance(attempts_data, list):
            # Respect the configured history limit
            for attempt_data in attempts_data[-config.max_attempts_history :]:
                if isinstance(attempt_data, dict):
                    try:
                        state.attempts.append(
                            Attempt(
                                ts=float(attempt_data.get("ts", time.time())),
                                paragraph_fr=str(attempt_data.get("paragraph_fr", "")),
                                translation_en=str(
                                    attempt_data.get("translation_en", "")
                                ),
                                score=clamp_int(attempt_data.get("score", 0), 0, 10, 0),
                                main_error=str(
                                    attempt_data.get("main_error", "") or ""
                                ),
                                lesson_focus=str(
                                    attempt_data.get("lesson_focus", "") or ""
                                ),
                                theme=str(attempt_data.get("theme", "") or ""),
                            )
                        )
                    except (ValueError, TypeError):
                        continue

        # Load review items
        review_data = data.get("review", [])
        if isinstance(review_data, list):
            for review_item_data in review_data:
                if isinstance(review_item_data, dict):
                    try:
                        state.review.append(
                            ReviewItem(
                                paragraph_fr=str(
                                    review_item_data.get("paragraph_fr", "")
                                ),
                                due_ts=float(
                                    review_item_data.get("due_ts", time.time())
                                ),
                                interval_days=clamp_int(
                                    review_item_data.get("interval_days", 0), 0, 3650, 0
                                ),
                                difficulty=float(
                                    review_item_data.get("difficulty", 1.0)
                                ),
                            )
                        )
                    except (ValueError, TypeError):
                        continue

        # Load notebook entries
        notebook_data = data.get("notebook", [])
        if isinstance(notebook_data, list):
            for entry_data in notebook_data:
  w              if isinstance(entry_data, dict):
                    try:
                        state.notebook.append(
                            NotebookEntry(
                                title=str(entry_data.get("title", "")),
                                content=str(entry_data.get("content", "")),
                                topic=str(entry_data.get("topic", "")),
                                created_ts=float(
                                    entry_data.get("created_ts", time.time())
                                ),
                                tags=list(entry_data.get("tags", [])),
                                favorite=bool(entry_data.get("favorite", False)),
                            )
                        )
                    except (ValueError, TypeError):
                        continue

        # Load daily challenges
        challenges_data = data.get("daily_challenges", [])
        if isinstance(challenges_data, list):
            for challenge_data in challenges_data:
                if isinstance(challenge_data, dict):
                    try:
                        challenge = DailyChallenge(
                            date=str(challenge_data.get("date", "")),
                            challenge_type=str(
                                challenge_data.get("challenge_type", "")
                            ),
                            title=str(challenge_data.get("title", "")),
                            description=str(challenge_data.get("description", "")),
                            instructions=str(challenge_data.get("instructions", "")),
                            example=str(challenge_data.get("example", "")),
                            tips=list(challenge_data.get("tips", [])),
                            xp_reward=clamp_int(
                                challenge_data.get("xp_reward", 10), 0, 1000, 10
                            ),
                            completed=bool(challenge_data.get("completed", False)),
                        )
                        # Handle optional completion date
                        completion_date = challenge_data.get("completion_date")
                        if completion_date is not None:
                            challenge.completion_date = float(completion_date)
                        state.daily_challenges.append(challenge)
                    except (ValueError, TypeError):
                        continue

        # Deduplicate and sort review items
        state.review = StorageManager._deduplicate_reviews(state.review)

        # Apply configuration limits to recent phrases and error tracking
        if len(state.recent_phrases) > config.max_recent_phrases:
            state.recent_phrases = state.recent_phrases[-config.max_recent_phrases :]

        # Limit error tracking to configured maximum
        if len(state.error_frequency) > config.max_error_tracking:
            # Keep the most frequent errors
            sorted_errors = sorted(
                state.error_frequency.items(), key=lambda x: x[1], reverse=True
            )
            state.error_frequency = dict(sorted_errors[: config.max_error_tracking])

        return state

    @staticmethod
    def _deduplicate_reviews(reviews: List[ReviewItem]) -> List[ReviewItem]:
        """Remove duplicate review items, keeping the most urgent."""
        best_reviews: Dict[str, ReviewItem] = {}

        for review in reviews:
            key = review.paragraph_fr.strip()
            if not key:
                continue

            if key not in best_reviews:
                best_reviews[key] = review
            else:
                # Keep the more urgent one (earlier due time)
                if review.due_ts < best_reviews[key].due_ts:
                    best_reviews[key] = review

        # Sort by due time
        result = list(best_reviews.values())
        result.sort(key=lambda x: x.due_ts)

        return result

    @staticmethod
    def add_to_review(state: TrainerState, paragraph_fr: str, due_ts: float) -> None:
        """Add item to review with deduplication."""
        paragraph_fr = paragraph_fr.strip()
        if not paragraph_fr:
            return

        # Check if already exists
        for item in state.review:
            if item.paragraph_fr.strip() == paragraph_fr:
                # Make it more urgent
                item.due_ts = min(item.due_ts, due_ts)
                item.interval_days = min(item.interval_days, 0)
                break
        else:
            # Add new item
            state.review.append(
                ReviewItem(paragraph_fr=paragraph_fr, due_ts=due_ts, interval_days=0)
            )

        # Deduplicate and sort
        state.review = StorageManager._deduplicate_reviews(state.review)

    @staticmethod
    def backup_data() -> str:
        """Create a backup of current data."""
        # Backup helper removed — use external backup tools or the storage file directly.
        raise NotImplementedError(
            "backup_data() has been removed; please copy the save file manually"
        )


# Global storage manager instance
storage = StorageManager()
