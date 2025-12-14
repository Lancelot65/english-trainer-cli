"""Enhanced input handling with history and validation."""

from pathlib import Path
from typing import Optional, List, Callable

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.styles import Style as PTStyle
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.validation import Validator, ValidationError

    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False


class InputValidator(Validator):
    """Custom input validator."""

    def __init__(
        self,
        validation_func: Optional[Callable[[str], bool]] = None,
        error_message: str = "Invalid input",
    ):
        self.validation_func = validation_func
        self.error_message = error_message

    def validate(self, document) -> None:
        text = document.text.strip()
        if self.validation_func and not self.validation_func(text):
            raise ValidationError(message=self.error_message)


class ModernInputHandler:
    """Modern input handler with enhanced features."""

    def __init__(self, history_file: Path):
        self.history_file = history_file
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        # Typed attributes; may be None if prompt_toolkit is not available
        self.session: Optional["PromptSession"] = None
        self.style: Optional["PTStyle"] = None

        if PROMPT_TOOLKIT_AVAILABLE:
            self.session = PromptSession(history=FileHistory(str(history_file)))
            self.style = PTStyle.from_dict(
                {
                    "prompt": "bold cyan",
                    "input": "white",
                }
            )

    def prompt(
        self,
        message: str = "> ",
        default: str = "",
        completions: Optional[List[str]] = None,
        validator: Optional[Callable[[str], bool]] = None,
        error_message: str = "Invalid input",
    ) -> str:  # pylint: disable=too-many-arguments,too-many-positional-arguments
        """
        Enhanced prompt with completion and validation.

        Args:
            message: Prompt message
            default: Default value
            completions: List of completion options
            validator: Validation function
            error_message: Error message for validation

        Returns:
            User input string
        """
        if not PROMPT_TOOLKIT_AVAILABLE:
            return self._fallback_prompt(message, default)

        try:
            completer = WordCompleter(completions) if completions else None
            input_validator = (
                InputValidator(validator, error_message) if validator else None
            )

            # session is non-None if PROMPT_TOOLKIT_AVAILABLE
            assert self.session is not None
            return self.session.prompt(
                HTML(f"<prompt>{message}</prompt>"),
                default=default,
                style=self.style,
                completer=completer,
                validator=input_validator,
            ).strip()

        except (KeyboardInterrupt, EOFError):
            return "q"
        except Exception:
            return self._fallback_prompt(message, default)

    def _fallback_prompt(self, message: str, default: str) -> str:
        """Fallback prompt without prompt_toolkit."""
        try:
            result = input(f"{message}").strip()
            return result if result else default
        except (KeyboardInterrupt, EOFError):
            return "q"

    def prompt_choice(self, message: str, choices: List[str], default: str = "") -> str:
        """
        Prompt for choice from a list.

        Args:
            message: Prompt message
            choices: List of valid choices
            default: Default choice

        Returns:
            Selected choice
        """

        def validate_choice(text: str) -> bool:
            return text.lower() in [c.lower() for c in choices] or text == default

        return self.prompt(
            message=message,
            default=default,
            completions=choices,
            validator=validate_choice,
            error_message=f"Please choose from: {', '.join(choices)}",
        )

    def prompt_number(
        self,
        message: str,
        min_val: Optional[int] = None,
        max_val: Optional[int] = None,
        default: Optional[int] = None,
    ) -> Optional[int]:
        """
        Prompt for a number with validation.

        Args:
            message: Prompt message
            min_val: Minimum value
            max_val: Maximum value
            default: Default value

        Returns:
            Integer value or None if cancelled
        """

        def validate_number(text: str) -> bool:
            if not text and default is not None:
                return True
            try:
                num = int(text)
                if min_val is not None and num < min_val:
                    return False
                if max_val is not None and num > max_val:
                    return False
                return True
            except ValueError:
                return False

        range_info = ""
        if min_val is not None and max_val is not None:
            range_info = f" ({min_val}-{max_val})"
        elif min_val is not None:
            range_info = f" (min: {min_val})"
        elif max_val is not None:
            range_info = f" (max: {max_val})"

        default_str = str(default) if default is not None else ""
        result = self.prompt(
            message=f"{message}{range_info}: ",
            default=default_str,
            validator=validate_number,
            error_message=f"Please enter a valid number{range_info}",
        )

        if result == "q":
            return None

        if not result and default is not None:
            return default

        try:
            return int(result)
        except ValueError:
            return None

    def prompt_multiline(self, message: str) -> str:
        """
        Prompt for multiline input.

        Args:
            message: Prompt message

        Returns:
            Multiline input string
        """
        print(f"{message} (Ctrl+D ou ligne vide pour terminer):")
        lines = []

        try:
            while True:
                line = input()
                if not line.strip():
                    break
                lines.append(line)
        except (KeyboardInterrupt, EOFError):
            pass

        return "\n".join(lines)

    def confirm(self, message: str, default: bool = False) -> bool:
        """
        Prompt for yes/no confirmation.

        Args:
            message: Confirmation message
            default: Default value

        Returns:
            Boolean confirmation
        """
        default_str = "O/n" if default else "o/N"
        result = self.prompt(f"{message} ({default_str}): ")

        if not result:
            return default

        return result.lower() in ["o", "oui", "y", "yes"]
