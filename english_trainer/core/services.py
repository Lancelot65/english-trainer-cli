"""Core services for English Trainer functionality."""

import time
from typing import Dict, List, Any, Optional
from functools import lru_cache

from .ai_client import ai_client, AIClientError
from .models import TrainerState, ReviewItem, NotebookEntry
from ..data.storage import storage
from ..prompts.templates import PromptTemplates
from ..utils.json_utils import clamp_int
from ..utils.error_handler import error_handler


class ExerciseService:
    """Service for generating and evaluating exercises."""

    @staticmethod
    @lru_cache(maxsize=256)  # Increased cache size for better performance
    def _cached_generate_exercise_prompt(
        level: str,
        focus: str,
        theme: str,
        avoid_phrases_hash: str,
        common_errors_hash: str,
    ) -> str:
        """Cache exercise prompts to avoid regenerating identical prompts."""
        # We can't directly pass lists to lru_cache, so we pass hashes instead
        # The actual prompt generation with lists happens in the calling function
        return f"level:{level}|focus:{focus}|theme:{theme}"

    @staticmethod
    def generate_exercise(state: TrainerState) -> Dict[str, Any]:
        """
        Generate a new translation exercise.

        Args:
            state: Current trainer state

        Returns:
            Exercise data with French text and notes

        Raises:
            AIClientError: If exercise generation fails
        """
        try:
            # Get user's most common errors to inform exercise generation
            common_errors = [error for error, _ in state.most_common_errors]

            # Get recent phrases to avoid repetition
            recent_phrases = state.recent_phrases

            # Use enhanced prompt generation with error and repetition avoidance
            prompt = PromptTemplates.get_exercise_prompt(
                level=state.level_name,
                focus=state.current_lesson,
                theme=state.current_theme,
                avoid_phrases=recent_phrases,
                common_errors=common_errors,
            )

            response = ai_client.call_json(
                system=prompt,
                user_msg="Génère un exercice de traduction adapté.",
                temperature=state.settings.temperature,
                model=state.settings.model,
            )

            # Debug logging
            error_handler.logger.debug("AI response type: %s", type(response))
            error_handler.logger.debug("AI response content: %s", response)

            if not response:
                raise AIClientError("No response from AI")

            if not isinstance(response, dict):
                raise AIClientError(
                    f"Invalid response type: {type(response)}. Expected dict."
                )

            if "paragraph_fr" not in response:
                available_keys = (
                    list(response.keys()) if isinstance(response, dict) else "N/A"
                )
                raise AIClientError(
                    f"Missing 'paragraph_fr' in response. Available keys: {available_keys}"
                )

            paragraph_fr = response.get("paragraph_fr", "").strip()
            if not paragraph_fr:
                raise AIClientError("Exercise generation returned empty text")

            return {
                "paragraph_fr": paragraph_fr,
                "notes": response.get("notes", "").strip(),
            }

        except Exception as e:
            error_handler.log_error(e, "ExerciseService.generate_exercise")

            # Fallback: try with a simpler prompt
            try:
                simple_prompt = 'Generate a simple French sentence for English translation. Respond with JSON: {"paragraph_fr": "your sentence", "notes": ""}'
                fallback_response = ai_client.call_json(
                    system=simple_prompt,
                    user_msg=f"Level: {state.level_name}",
                    temperature=0.5,
                    model=state.settings.model,
                )

                if fallback_response and "paragraph_fr" in fallback_response:
                    error_handler.logger.info("Used fallback exercise generation")
                    return {
                        "paragraph_fr": fallback_response["paragraph_fr"],
                        "notes": "Exercice de secours",
                    }
            except Exception as fallback_exc:
                error_handler.log_error(fallback_exc, "ExerciseService.generate_exercise fallback")

            # Ultimate fallback: predefined exercises
            fallback_exercises = [
                {
                    "paragraph_fr": "Je vais au marché ce matin.",
                    "notes": "Futur proche",
                },
                {
                    "paragraph_fr": "Elle a mangé une pomme hier.",
                    "notes": "Passé composé",
                },
                {
                    "paragraph_fr": "Nous sommes en train de travailler.",
                    "notes": "Présent continu",
                },
                {
                    "paragraph_fr": "Il faut que tu viennes demain.",
                    "notes": "Subjonctif",
                },
                {
                    "paragraph_fr": "Si j'avais de l'argent, j'achèterais une voiture.",
                    "notes": "Conditionnel",
                },
            ]

            import random

            fallback = random.choice(fallback_exercises)
            error_handler.logger.warning("Used predefined fallback exercise")

            return {
                "paragraph_fr": fallback["paragraph_fr"],
                "notes": f"{fallback['notes']} (exercice de secours)",
            }

    @staticmethod
    def evaluate_translation(
        french_text: str, translation: str, settings
    ) -> Dict[str, Any]:
        """
        Evaluate a translation attempt.

        Args:
            french_text: Original French text
            translation: Student's translation
            settings: User settings

        Returns:
            Evaluation results with score and feedback

        Raises:
            AIClientError: If evaluation fails
        """
        try:
            prompt = PromptTemplates.get_evaluation_prompt(french_text, translation)

            response = ai_client.call_json(
                system=prompt,
                user_msg="Évalue cette traduction.",
                temperature=0.2,  # Lower temperature for consistent evaluation
                model=settings.model,
            )

            # Debug logging
            error_handler.logger.debug("Evaluation response type: %s", type(response))
            error_handler.logger.debug("Evaluation response content: %s", response)

            if not response:
                raise AIClientError("No response from AI")

            if not isinstance(response, dict):
                raise AIClientError(
                    f"Invalid response type: {type(response)}. Expected dict."
                )

            # Validate required fields
            required_fields = [
                "score",
                "ideal_translation",
                "main_error",
                "lesson",
                "improvement_suggestions",
            ]
            for field in required_fields:
                if field not in response:
                    available_keys = (
                        list(response.keys()) if isinstance(response, dict) else "N/A"
                    )
                    raise AIClientError(
                        f"Missing '{field}' in response. Available keys: {available_keys}"
                    )

            # Validate and clamp score
            response["score"] = clamp_int(response.get("score", 0), 0, 10, 0)
            response.setdefault("ideal_translation", "")
            response.setdefault("main_error", "")
            response.setdefault("lesson", "")
            response.setdefault("improvement_suggestions", [])

            return response

        except Exception as e:
            error_handler.log_error(e, "ExerciseService.evaluate_translation")

            # Fallback: try with a simpler prompt
            try:
                simple_prompt = 'Evaluate this translation from French to English. Respond with JSON: {"score": 7, "ideal_translation": "your ideal translation", "main_error": "main issue", "lesson": "grammar tip", "improvement_suggestions": ["Suggestion 1", "Suggestion 2"]}'
                fallback_response = ai_client.call_json(
                    system=simple_prompt,
                    user_msg=f"French: {french_text}\nTranslation: {translation}",
                    temperature=0.1,
                    model=settings.model,
                )

                if fallback_response and "score" in fallback_response:
                    error_handler.logger.info("Used fallback evaluation")
                    fallback_response["score"] = clamp_int(
                        fallback_response.get("score", 0), 0, 10, 0
                    )
                    fallback_response.setdefault("ideal_translation", "")
                    fallback_response.setdefault("main_error", "Évaluation de secours")
                    fallback_response.setdefault("lesson", "")
                    fallback_response.setdefault(
                        "improvement_suggestions",
                        ["Améliorez votre grammaire", "Pratiquez davantage"],
                    )
                    return fallback_response
            except Exception as fallback_exc:
                error_handler.log_error(fallback_exc, "ExerciseService.evaluate_translation fallback")

            # Ultimate fallback: basic evaluation based on length and similarity
            error_handler.logger.warning("Used basic fallback evaluation")

            # Simple heuristic evaluation
            french_words = len(french_text.split())
            translation_words = len(translation.split())

            # Basic scoring based on length similarity and presence of content
            if not translation.strip():
                score = 0
            elif abs(french_words - translation_words) > french_words:
                score = 3  # Very different length
            elif translation.lower() == french_text.lower():
                score = 1  # Just copied French
            else:
                score = 5  # Reasonable attempt

            return {
                "score": score,
                "ideal_translation": f"[Traduction idéale non disponible pour: {french_text}]",
                "main_error": "Évaluation automatique - serveur IA indisponible",
                "lesson": "Vérifiez votre connexion IA pour une évaluation détaillée",
                "improvement_suggestions": [
                    "Vérifiez votre connexion Internet",
                    "Essayez à nouveau plus tard",
                ],
            }


class LessonService:
    """Service for interactive lessons and teaching."""

    @staticmethod
    def generate_lesson(topic: str, level: str, settings) -> str:
        """
        Generate a comprehensive lesson on a topic.

        Args:
            topic: Lesson topic
            level: Student level
            settings: User settings

        Returns:
            Lesson content in Markdown format

        Raises:
            AIClientError: If lesson generation fails
        """
        try:
            prompt = PromptTemplates.get_lesson_prompt(topic, level)

            return ai_client.call(
                system=prompt,
                user_msg=f"Crée une leçon complète sur: {topic}",
                temperature=0.6,
                model=settings.model,
            )

        except Exception as e:
            raise AIClientError(f"Failed to generate lesson: {e}") from e

    @staticmethod
    def answer_question(question: str, context: str, settings) -> str:
        """
        Answer a student question about a lesson.

        Args:
            question: Student's question
            context: Lesson context
            settings: User settings

        Returns:
            Answer in Markdown format

        Raises:
            AIClientError: If answer generation fails
        """
        try:
            prompt = f"{PromptTemplates.LESSON_TEACHER}\n\nCONTEXTE:\n{context}"

            return ai_client.call(
                system=prompt,
                user_msg=f"L'élève demande: {question}\n\nRéponds de manière précise avec des exemples.",
                temperature=0.5,
                model=settings.model,
            )

        except Exception as e:
            raise AIClientError(f"Failed to answer question: {e}") from e


class NotebookService:
    """Service for managing the lesson notebook."""

    @staticmethod
    def save_lesson(
        state: TrainerState,
        title: str,
        content: str,
        topic: str,
        tags: Optional[List[str]] = None,
    ) -> None:
        """
        Save a lesson to the notebook.

        Args:
            state: Current trainer state
            title: Lesson title
            content: Lesson content
            topic: Lesson topic
            tags: Optional tags
        """
        entry = NotebookEntry(
            title=title.strip(),
            content=content.strip(),
            topic=topic.strip(),
            created_ts=time.time(),
            tags=tags or [],
            favorite=False,
        )

        state.add_notebook_entry(entry)
        storage.save_state(state)

    @staticmethod
    def search_notebook(state: TrainerState, query: str) -> List[NotebookEntry]:
        """
        Search notebook entries.

        Args:
            state: Current trainer state
            query: Search query

        Returns:
            List of matching entries
        """
        return state.search_notebook(query)

    @staticmethod
    def get_by_topic(state: TrainerState, topic: str) -> List[NotebookEntry]:
        """
        Get notebook entries by topic.

        Args:
            state: Current trainer state
            topic: Topic to filter by

        Returns:
            List of entries for the topic
        """
        return state.get_notebook_by_topic(topic)

    @staticmethod
    def toggle_favorite(state: TrainerState, entry_index: int) -> bool:
        """
        Toggle favorite status of a notebook entry.

        Args:
            state: Current trainer state
            entry_index: Index of entry to toggle

        Returns:
            True if successful, False otherwise
        """
        if 0 <= entry_index < len(state.notebook):
            state.notebook[entry_index].favorite = not state.notebook[
                entry_index
            ].favorite
            storage.save_state(state)
            return True
        return False


class ConversationService:
    """Service for conversation practice."""

    @staticmethod
    def start_conversation(topic: str, level: str, settings) -> str:
        """
        Start a conversation on a topic.

        Args:
            topic: Conversation topic
            level: Student level
            settings: User settings

        Returns:
            Opening message
        """
        try:
            prompt = PromptTemplates.get_conversation_prompt(
                f"Topic: {topic}, Level: {level}"
            )

            return ai_client.call(
                system=prompt,
                user_msg=f"Start a conversation about {topic}. Keep it appropriate for {level} level.",
                temperature=0.8,
                model=settings.model,
            )

        except Exception as e:
            raise AIClientError(f"Failed to start conversation: {e}") from e

    @staticmethod
    def continue_conversation(message: str, context: str, settings) -> str:
        """
        Continue a conversation.

        Args:
            message: Student's message
            context: Conversation context
            settings: User settings

        Returns:
            AI response
        """
        try:
            prompt = PromptTemplates.get_conversation_prompt()
            full_context = (
                f"Conversation context:\n{context}\n\nStudent says: {message}"
            )

            return ai_client.call(
                system=prompt,
                user_msg=full_context,
                temperature=0.8,
                model=settings.model,
            )

        except Exception as e:
            raise AIClientError(f"Failed to continue conversation: {e}") from e


class VocabularyService:
    """Service for vocabulary building."""

    @staticmethod
    def generate_vocabulary_set(
        theme: str, level: str, count: int, settings
    ) -> Dict[str, Any]:
        """
        Generate a vocabulary set for a theme.

        Args:
            theme: Vocabulary theme
            level: Student level
            count: Number of words to generate
            settings: User settings

        Returns:
            Vocabulary set data
        """
        try:
            prompt = f"{PromptTemplates.VOCABULARY_BUILDER}\n\nGenerate {count} vocabulary words for theme '{theme}' at {level} level."

            return ai_client.call_json(
                system=prompt,
                user_msg=f"Create vocabulary set: {theme} ({count} words)",
                temperature=0.6,
                model=settings.model,
            )

        except Exception as e:
            raise AIClientError(f"Failed to generate vocabulary: {e}") from e


class ReviewService:
    """Service for spaced repetition reviews."""

    @staticmethod
    def process_review_result(
        state: TrainerState, review_item: ReviewItem, score: int
    ) -> None:
        """
        Process the result of a review attempt.

        Args:
            state: Current trainer state
            review_item: The reviewed item
            score: Score achieved (0-10)
        """
        now = time.time()

        if score >= 8:
            # Good performance - increase interval
            if review_item.interval_days == 0:
                review_item.interval_days = 1
            else:
                review_item.interval_days = min(365, review_item.interval_days * 2)

            review_item.due_ts = now + (review_item.interval_days * 86400)
            review_item.difficulty = max(0.5, review_item.difficulty * 0.9)

        elif score >= 6:
            # Moderate performance - slight increase
            review_item.interval_days = max(1, review_item.interval_days)
            review_item.due_ts = now + (review_item.interval_days * 86400)

        else:
            # Poor performance - reset to immediate review
            review_item.interval_days = 0
            review_item.due_ts = now
            review_item.difficulty = min(2.0, review_item.difficulty * 1.1)

        storage.save_state(state)

    @staticmethod
    def add_to_review(state: TrainerState, french_text: str, score: int) -> None:
        """
        Add an item to review if score is below threshold.

        Args:
            state: Current trainer state
            french_text: French text to review
            score: Score achieved
        """
        if score < 6:  # Below threshold
            storage.add_to_review(state, french_text, time.time())


class DailyChallengeService:
    """Service for daily challenges."""

    @staticmethod
    @lru_cache(maxsize=7)  # Cache for a week
    def get_daily_challenge(date_str: str) -> Dict[str, Any]:
        """
        Get or generate a daily challenge for a specific date.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Challenge data
        """
        try:
            prompt = PromptTemplates.get_daily_challenge_prompt()

            response = ai_client.call_json(
                system=prompt,
                user_msg=f"Génère un défi quotidien pour la date: {date_str}",
                temperature=0.7,
                model="gpt-5-mini",  # Use a consistent model for challenges
            )

            return response
        except Exception as e:
            error_handler.log_error(e, "DailyChallengeService.get_daily_challenge")
            # Fallback challenge
            return {
                "challenge_type": "translation",
                "title": "Défi de traduction du jour",
                "description": "Traduisez cette phrase courante en anglais",
                "instructions": "Traduisez la phrase suivante en anglais",
                "example": "Bonjour, comment allez-vous aujourd'hui?",
                "tips": [
                    "Concentrez-vous sur le temps verbal",
                    "Pensez aux formules de politesse",
                ],
                "xp_reward": 10,
            }


# Global service instances
exercise_service = ExerciseService()
lesson_service = LessonService()
notebook_service = NotebookService()
conversation_service = ConversationService()
vocabulary_service = VocabularyService()
review_service = ReviewService()
daily_challenge_service = DailyChallengeService()
