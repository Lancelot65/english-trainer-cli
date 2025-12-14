# English Trainer - Agent Guidelines

## Build/Test Commands
- **Run application**: `python run.py` or `python english_trainer/main.py`
- **Check dependencies**: `python -c "import openai, rich, prompt_toolkit"`
- **Install dependencies**: `pip install -r requirements.txt` (if exists)
- **No formal test suite** - Manual testing through the CLI interface

## Code Style Guidelines

### Imports & Structure
- Use absolute imports from project root: `from english_trainer.core.app import main`
- Group imports: standard library, third-party, local modules
- Use `from __future__ import annotations` for type hints when needed
- All modules use `__init__.py` for proper package structure

### Type System
- Use dataclasses for data models (`@dataclass`)
- Type hints required for all function signatures
- Use `Optional[T]` for nullable types
- Use `List[T]`, `Dict[K, V]` from typing module
- Properties should have return type hints

### Naming Conventions
- Classes: `PascalCase` (e.g., `EnglishTrainerApp`, `AIClient`)
- Functions/variables: `snake_case` (e.g., `generate_exercise`, `current_lesson`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `XP_PER_LEVEL`)
- Private methods: prefix with underscore (`_method_name`)
- File names: `snake_case.py`

### Error Handling
- Use custom exceptions from `utils.error_handler`
- Wrap API calls with `@RetryHandler.with_retry`
- Use `error_handler.log_error()` for consistent logging
- Provide user-friendly error messages with emojis
- Handle specific error types (connection, timeout, auth)

### Configuration
- Environment variables for API settings: `ENGLISH_RPG_*`
- Central config in `core/config.py` using dataclass
- File paths use `Path` objects from pathlib
- Default values should be sensible

### UI/UX Patterns
- Use `ModernUI` class for all console output
- Loading states with `ui.loading("message")`
- User input via `ModernInputHandler`
- Consistent emoji usage for feedback (✅ ❌ ⚠️ 💡)
- Clear section headers and menus

### Service Layer
- Business logic in `core/services.py`
- Separate concerns: exercise, lesson, notebook, conversation services
- Use dependency injection pattern
- Return structured data (dicts, dataclasses)

### Data Management
- State management via `TrainerState` dataclass
- JSON serialization for persistence
- File locking for concurrent access protection
- History limits to prevent memory bloat (300 attempts max)

### Performance
- Use `@lru_cache` for expensive operations
- Lazy initialization for clients (AI client)
- Context managers for resource management
- Timeout configurations for external calls
 