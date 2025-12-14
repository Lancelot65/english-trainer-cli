"""Enhanced error handling and recovery utilities."""

import logging
import traceback
from functools import wraps
from typing import Callable, Any, Optional
from pathlib import Path


class ErrorHandler:
    """Centralized error handling and recovery."""

    def __init__(self):
        self.setup_logging()

    def setup_logging(self) -> None:
        """Setup logging configuration."""
        log_dir = Path.home() / ".english_trainer_logs"
        log_dir.mkdir(exist_ok=True)

        # Configure root logger
        logging.basicConfig(
            level=logging.WARNING,  # Reduce verbosity
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_dir / "english_trainer.log"),
                logging.StreamHandler(),
            ],
        )

        # Set specific loggers to reduce noise
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("openai").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

        # Our logger can be more verbose
        self.logger = logging.getLogger("english_trainer")
        self.logger.setLevel(logging.INFO)

    def log_error(self, error: Exception, context: str = "") -> None:
        """Log an error with context."""
        error_msg = f"Error in {context}: {str(error)}"
        self.logger.error(error_msg)
        self.logger.debug(traceback.format_exc())

    def handle_ai_error(self, error: Exception) -> str:
        """Handle AI-related errors with user-friendly messages."""
        error_str = str(error).lower()

        if "timeout" in error_str:
            return "⏱️ Délai d'attente dépassé. Vérifiez votre connexion et réessayez."
        if "connection" in error_str or "network" in error_str:
            return "🌐 Problème de connexion. Vérifiez que votre serveur IA est accessible."
        if "unauthorized" in error_str or "401" in error_str:
            return "🔑 Erreur d'authentification. Vérifiez votre clé API."
        if "rate limit" in error_str or "429" in error_str:
            return "🚦 Limite de taux atteinte. Attendez quelques secondes et réessayez."
        if "model" in error_str:
            return "🤖 Modèle non disponible. Vérifiez le nom du modèle dans la configuration."
        if "json" in error_str:
            return "📄 Réponse IA malformée. Réessayez avec un prompt différent."

        return f"🔧 Erreur IA: {str(error)}"

    def handle_file_error(self, error: Exception) -> str:
        """Handle file-related errors."""
        error_str = str(error).lower()

        if "permission" in error_str:
            return "🔒 Permissions insuffisantes. Vérifiez les droits d'accès au fichier."
        if "not found" in error_str:
            return "📁 Fichier non trouvé. Le fichier sera créé automatiquement."
        if "disk" in error_str or "space" in error_str:
            return "💾 Espace disque insuffisant. Libérez de l'espace et réessayez."

        return f"📄 Erreur fichier: {str(error)}"

    def handle_validation_error(self, error: Exception) -> str:
        """Handle validation errors."""
        return f"✏️ Données invalides: {str(error)}"

    def get_recovery_suggestion(self, error: Exception) -> Optional[str]:
        """Get recovery suggestions for common errors."""
        error_str = str(error).lower()

        if "connection" in error_str:
            return (
                "💡 Suggestions:\n• Vérifiez que votre serveur IA est démarré\n"
                "• Testez l'URL avec curl\n• Vérifiez les variables d'environnement"
            )
        if "timeout" in error_str:
            return (
                "💡 Suggestions:\n• Augmentez le timeout dans la configuration\n"
                "• Vérifiez la charge du serveur\n• Essayez un modèle plus rapide"
            )
        if "json" in error_str:
            return (
                "💡 Suggestions:\n• Réessayez l'opération\n• Modifiez légèrement votre demande\n"
                "• Vérifiez les prompts système"
            )

        return None


def with_error_handling(
    error_types: tuple = (Exception,),
    fallback_value: Any = None,
    show_traceback: bool = False,
):
    """Decorator for automatic error handling."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except error_types as e:
                error_handler.log_error(e, func.__name__)

                if show_traceback:
                    print(f"🐛 Traceback pour débogage:\n{traceback.format_exc()}")

                return fallback_value

        return wrapper

    return decorator


def safe_execute(
    func: Callable,
    *args,
    fallback: Any = None,
    error_message: str = "Opération échouée",
    **kwargs,
) -> Any:
    """Safely execute a function with error handling."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_handler.log_error(e, func.__name__)
        print(f"❌ {error_message}: {str(e)}")
        return fallback


class RetryHandler:
    """Handle retry logic for operations."""

    @staticmethod
    def with_retry(
        max_attempts: int = 3,
        delay: float = 1.0,
        backoff_factor: float = 2.0,
        exceptions: tuple = (Exception,),
    ):
        """Decorator for retry logic."""

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                import time

                last_exception = None
                current_delay = delay

                for attempt in range(max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        error_handler.log_error(
                            e, f"{func.__name__} (attempt {attempt + 1})"
                        )

                        if attempt < max_attempts - 1:
                            time.sleep(current_delay)
                            current_delay *= backoff_factor
                        else:
                            raise last_exception from e

                if last_exception is not None:
                    raise last_exception
                raise RuntimeError("Retry failed without exception")

            return wrapper

        return decorator


class ValidationError(Exception):
    """Custom validation error."""



class ConfigurationError(Exception):
    """Custom configuration error."""



class AIServiceError(Exception):
    """Custom AI service error."""



# Global error handler instance
error_handler = ErrorHandler()
