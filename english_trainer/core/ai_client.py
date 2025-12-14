"""AI client for interacting with LLM APIs."""

from typing import Dict, List, Optional, Any

from openai import OpenAI

from .config import config
from ..utils.file_utils import file_lock
from ..utils.json_utils import parse_json
from ..utils.error_handler import error_handler, RetryHandler


class AIClientError(Exception):
    """Base exception for AI client errors."""



class AIClient:
    """Client for interacting with LLM APIs."""

    def __init__(self):
        self._client: Optional[OpenAI] = None

    @property
    def client(self) -> OpenAI:
        """Get or create OpenAI client."""
        if self._client is None:
            self._client = OpenAI(base_url=config.base_url, api_key=config.api_key)
        return self._client

    def _prepare_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Prepare messages for API call.
        Some backends handle system messages poorly, so we merge them into user messages.
        """
        msgs = [dict(m) for m in messages]
        systems = [
            m["content"] for m in msgs if m.get("role") == "system" and m.get("content")
        ]

        if not systems:
            return msgs

        system_text = "\n\n".join(systems).strip()
        msgs = [m for m in msgs if m.get("role") != "system"]

        # Add system content to first user message
        for i, m in enumerate(msgs):
            if m.get("role") == "user":
                msgs[i]["content"] = f"{system_text}\n\n{msgs[i].get('content', '')}"
                break
        else:
            # No user message found, create one
            msgs.insert(0, {"role": "user", "content": system_text})

        return msgs

    @RetryHandler.with_retry(max_attempts=3, delay=0.5, exceptions=(Exception,))
    def call(
        self,
        system: str,
        user_msg: str,
        *,
        temperature: float = 0.7,
        model: Optional[str] = None,
        retries: int = 3,
    ) -> str:  # pylint: disable=too-many-arguments,too-many-positional-arguments
        """
        Make an AI API call with retry logic.

        Args:
            system: System prompt
            user_msg: User message
            temperature: Sampling temperature
            model: Model to use (defaults to config.model)
            retries: Number of retry attempts

        Returns:
            AI response text

        Raises:
            AIClientError: If all retries fail
        """
        if model is None:
            model = config.model

        messages = self._prepare_messages(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ]
        )

        # 'retries' is accepted for API compatibility; it's unused here on purpose
        del retries

        try:
            with file_lock(config.lock_file, timeout=config.timeout):
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,  # type: ignore
                    timeout=config.timeout,
                    temperature=temperature,
                )

            content = response.choices[0].message.content
            if content is None:
                raise AIClientError("Empty response from AI")

            return content.strip()

        except Exception as e:
            error_handler.log_error(e, "AI API call")
            raise AIClientError(error_handler.handle_ai_error(e)) from e

    def call_json(
        self,
        system: str,
        user_msg: str,
        *,
        temperature: float = 0.7,
        model: Optional[str] = None,
        retries: int = 3,
    ) -> Dict[str, Any]:  # pylint: disable=too-many-arguments,too-many-positional-arguments
        """
        Make an AI API call expecting JSON response.

        Args:
            system: System prompt
            user_msg: User message
            temperature: Sampling temperature
            model: Model to use
            retries: Number of retry attempts

        Returns:
            Parsed JSON response

        Raises:
            AIClientError: If call fails or response is not valid JSON
        """
        response = self.call(
            system=system,
            user_msg=user_msg,
            temperature=temperature,
            model=model,
            retries=retries,
        )

        # Log raw response for debugging
        error_handler.logger.debug("Raw AI response: %s", repr(response))

        parsed = parse_json(response)
        if parsed is None:
            # Try to give more helpful error message
            response_preview = (
                response[:200] + "..." if len(response) > 200 else response
            )
            error_handler.log_error(
                Exception(f"JSON parsing failed for response: {response_preview}"),
                "AIClient.call_json",
            )
            raise AIClientError(
                f"Invalid JSON response. Response preview: {response_preview}"
            )

        return parsed


# Global AI client instance
ai_client = AIClient()
