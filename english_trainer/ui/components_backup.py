# Legacy backup removed: this file is deprecated and intentionally left empty.
# To fully remove it from the repository, delete the file.

from typing import List, Dict, Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.markdown import Markdown
from rich.box import ROUNDED, DOUBLE, SQUARE

from ..core.models import TrainerState, NotebookEntry, Attempt, DailyChallenge


class ModernUI:
    """Modern, minimalist UI components."""

    def __init__(self):
        self.console = Console()
        self.theme = {
            "primary": "#4CAF50",  # Green
            "secondary": "#2196F3",  # Blue
            "success": "#4CAF50",  # Green
            "warning": "#FFC107",  # Amber
            "error": "#F44336",  # Red
            "muted": "#9E9E9E",  # Gray
            "accent": "#9C27B0",  # Purple
            "info": "#00BCD4",  # Cyan
            "dark": "#212121",  # Dark gray
            "light": "#FFFFFF",  # White
            "streak": "#FF5722",  # Orange (for streak display)
        }

    def clear(self) -> None:
        """Clear the console."""
        self.console.clear()

    def header(self, state: TrainerState) -> None:
        """Display compact header with progress."""
        self.clear()

        # Compact header on two lines
        progress_bar = self._create_progress_bar(state.level_progress)
        focus = state.current_lesson or "Général"
        theme = state.current_theme or "Aucun"

        # Line 1: Title and level
        line1 = f"[bold {self.theme['primary']}]ENGLISH TRAINER v7.0[/] • [dim]{state.level_name}[/]"

        # Line 2: Progress, XP, focus and theme
        streak_display = f"🔥 {state.streak}" if state.streak > 0 else ""
        line2 = f"{progress_bar} [dim]XP: {state.xp}[/] • [bold {self.theme['accent']}]Focus: {focus}[/] • [bold {self.theme['secondary']}]Thème: {theme}[/] {streak_display}"

        self.console.print(line1)
        self.console.print(line2)
        self.console.print()

    def _create_progress_bar(self, progress: float) -> Text:
        """Create a visual progress bar."""
        bar_length = 30
        filled = int(bar_length * progress)
        bar = "█" * filled + "░" * (bar_length - filled)
        percentage = int(progress * 100)
        return Text(f"[{bar}] {percentage}%", style=self.theme["success"])

    def main_menu(
        self,
        has_reviews: bool,
        n_reviews: int,
        has_notebook: bool,
        show_help: bool = False,
    ) -> None:
        """Display main menu with modern styling."""
        if show_help:
            commands = [
                ("⏎", "Nouvel exercice", self.theme["primary"]),
                ("c", "Choisir leçon", self.theme["secondary"]),
                ("t", "Choisir thème", self.theme["accent"]),
                ("e", "Cours interactif", self.theme["success"]),
                ("d", "Défi quotidien", self.theme["streak"]),
            ]

            if has_notebook:
                commands.append(("n", "Cahier de cours", self.theme["warning"]))

            if has_reviews:
                commands.append(("v", f"Révisions ({n_reviews})", self.theme["error"]))

            commands.extend(
                [
                    ("s", "Statistiques", self.theme["muted"]),
                    ("conv", "Conversation", self.theme["info"]),
                    ("vocab", "Vocabulaire", self.theme["accent"]),
                    ("h", "Aide", self.theme["muted"]),
                    ("q", "Quitter", self.theme["muted"]),
                ]
            )

            # Use Columns to display multiple commands per line and allow wrapping
            columns = []
            for key, desc, color in commands:
                columns.append(f"[{color}][bold]{key}[/] {desc}[/]")

            self.console.print(
                Panel(
                    Columns(columns, equal=True, expand=True),
                    title="[bold]Commandes Disponibles[/]",
                    border_style=self.theme["primary"],
                    padding=(1, 2),
                    box=ROUNDED,
                )
            )
        else:
            # When help is not requested, do not show the command banner (keeps UI minimal)
            return

    def lesson_menu(
        self, curriculum: Dict[str, List[str]], current_lesson: str
    ) -> None:
        """Display lesson selection menu."""
        self.clear()
        self.console.print(
            Panel(
                "[bold]Sélection du Focus Grammatical[/]",
                border_style=self.theme["primary"],
                box=DOUBLE,
            )
        )

        for level, lessons in curriculum.items():
            self.console.print(f"\n[bold underline {self.theme['accent']}]{level}[/]")

            # Create two-column layout for lessons
            table = Table.grid(padding=(0, 2))
            table.add_column()
            table.add_column()

            row = []
            for i, lesson in enumerate(lessons, 1):
                style = (
                    f"bold {self.theme['success']}"
                    if lesson == current_lesson
                    else "white"
                )
                prefix = "▶ " if lesson == current_lesson else f"{i}. "
                row.append(f"[{style}]{prefix}{lesson}[/]")

                if len(row) == 2:
                    table.add_row(*row)
                    row = []

            if row:
                row.append("")
                table.add_row(*row)

            self.console.print(table)

        self.console.print(
            f"\n[{self.theme['muted']}]0. Mode Général (pas de focus)[/]"
        )

    def theme_menu(self, themes: List[str], current_theme: str) -> None:
        """Display theme selection menu."""
        self.clear()
        self.console.print(
            Panel(
                "[bold]Sélection du Thème[/]",
                border_style=self.theme["secondary"],
                box=DOUBLE,
            )
        )

        columns = []
        for i, theme in enumerate(themes, 1):
            style = (
                f"bold {self.theme['accent']}" if theme == current_theme else "white"
            )
            columns.append(f"[{style}]{i}. {theme}[/]")

        self.console.print(Columns(columns, equal=True, expand=True))

    def exercise_display(self, french_text: str, notes: str = "") -> None:
        """Display exercise with modern styling."""
        content = Text(french_text, justify="center", style="bold white")

        subtitle = None
        if notes:
            subtitle = f"[italic {self.theme['muted']}]{notes}[/]"

        self.console.print(
            Panel(
                content,
                title="[bold]📝 Exercice de Traduction[/]",
                subtitle=subtitle,
                border_style=self.theme["primary"],
                padding=(2, 3),
                box=ROUNDED,
            )
        )

    def feedback_display(self, evaluation: Dict[str, Any]) -> None:
        """Display feedback with color-coded scoring."""
        score = evaluation.get("score", 0)

        # Determine color based on score
        if score >= 8:
            color = self.theme["success"]
            emoji = "🎉"
            feedback_type = "Excellent!"
        elif score >= 6:
            color = self.theme["warning"]
            emoji = "👍"
            feedback_type = "Bien!"
        else:
            color = self.theme["error"]
            emoji = "💪"
            feedback_type = "Continuez à pratiquer!"

        # Create feedback panel
        content = Table.grid(padding=(0, 1))
        content.add_column()

        # Score
        content.add_row(f"[bold {color}]{emoji} {feedback_type} Score: {score}/10[/]")
        content.add_row("")

        # Ideal translation
        ideal = evaluation.get("ideal_translation", "")
        if ideal:
            content.add_row("[bold]✅ Traduction idéale:[/]")
            content.add_row(f"[italic {self.theme['success']}]{ideal}[/]")
            content.add_row("")

        # Main error
        error = evaluation.get("main_error", "")
        if error:
            content.add_row(f"[bold {self.theme['error']}]⚠️ Point d'amélioration:[/]")
            content.add_row(f"{error}")
            content.add_row("")

        # Lesson
        lesson = evaluation.get("lesson", "")
        if lesson:
            content.add_row(f"[{self.theme['info']}]💡 Astuce: {lesson}[/]")
            content.add_row("")

        # Improvement suggestions
        suggestions = evaluation.get("improvement_suggestions", [])
        if suggestions:
            content.add_row(
                f"[{self.theme['accent']}]🎯 Suggestions d'amélioration:[/]"
            )
            for suggestion in suggestions:
                content.add_row(f"• {suggestion}")

        self.console.print(
            Panel(
                content,
                title="[bold]📊 Correction[/]",
                border_style=color,
                padding=(1, 2),
                box=ROUNDED,
            )
        )

    def lesson_content(self, content: str, title: str = "Cours") -> None:
        """Display lesson content with markdown formatting."""
        self.console.print(
            Panel(
                Markdown(content),
                title=f"[bold]📘 {title}[/]",
                border_style=self.theme["success"],
                padding=(1, 2),
                box=ROUNDED,
            )
        )

    def notebook_display(self, entries: List[NotebookEntry]) -> None:
        """Display notebook entries."""
        if not entries:
            self.console.print(
                Panel(
                    "[italic]Aucune entrée dans le cahier[/]",
                    border_style=self.theme["muted"],
                    box=SQUARE,
                )
            )
            return

        for i, entry in enumerate(entries, 1):
            favorite_icon = "⭐" if entry.favorite else ""
            tags_text = " ".join(f"#{tag}" for tag in entry.tags) if entry.tags else ""

            header = f"{favorite_icon} {entry.title}"
            if tags_text:
                header += f" [{self.theme['muted']}]{tags_text}[/]"

            self.console.print(
                Panel(
                    (
                        entry.content[:200] + "..."
                        if len(entry.content) > 200
                        else entry.content
                    ),
                    title=f"[bold]📚 {i}. {header}[/]",
                    subtitle=f"[{self.theme['muted']}]{entry.formatted_date} • {entry.topic}[/]",
                    border_style=self.theme["accent"],
                    padding=(1, 2),
                    box=ROUNDED,
                )
            )

    def statistics_display(self, state: TrainerState) -> None:
        """Display user statistics."""
        self.clear()

        # Recent performance
        recent_avg = state.recent_performance
        total_reviews = len(state.review)
        due_reviews = len(state.due_reviews)
        completed_challenges = len([c for c in state.daily_challenges if c.completed])
        total_challenges = len(state.daily_challenges)

        # Create stats table
        stats = Table(
            title="📊 Statistiques", border_style=self.theme["primary"], box=ROUNDED
        )
        stats.add_column("Métrique", style="bold")
        stats.add_column("Valeur", justify="right")

        stats.add_row("🏆 Niveau actuel", state.level_name)
        stats.add_row("⭐ XP total", str(state.xp))
        stats.add_row("📝 Exercices complétés", str(state.total_exercises))
        stats.add_row("📈 Performance récente", f"{recent_avg:.1f}/10")
        stats.add_row("🔁 Révisions en attente", f"{due_reviews}/{total_reviews}")
        stats.add_row("📘 Entrées cahier", str(len(state.notebook)))
        stats.add_row("🔥 Streak actuel", str(state.streak))
        stats.add_row(
            "🎯 Défis quotidiens", f"{completed_challenges}/{total_challenges}"
        )

        self.console.print(stats)

        # Display most common errors
        if state.most_common_errors:
            self.console.print("\n[bold]⚠️ Vos erreurs les plus fréquentes:[/]")
            error_table = Table(show_header=True, header_style="bold magenta")
            error_table.add_column("Erreur", style="red")
            error_table.add_column("Fréquence", style="yellow", justify="right")

            for error, count in state.most_common_errors[:5]:  # Top 5 errors
                error_table.add_row(error, str(count))

            self.console.print(error_table)

        # Recent attempts chart
        if state.attempts:
            self._display_progress_chart(state.attempts[-20:])

    def _display_progress_chart(self, attempts: List[Attempt]) -> None:
        """Display a simple progress chart."""
        if not attempts:
            return

        self.console.print("\n[bold]📈 Progression récente:[/]")

        chart_line = ""
        for attempt in attempts:
            if attempt.score >= 8:
                chart_line += "🟢"
            elif attempt.score >= 6:
                chart_line += "🟡"
            else:
                chart_line += "🔴"

        self.console.print(f"  {chart_line}")
        self.console.print("  🟢 Excellent (8-10)  🟡 Bien (6-7)  🔴 À améliorer (0-5)")

    def daily_challenge_display(self, challenge: DailyChallenge) -> None:
        """Display daily challenge."""
        status = (
            "[bold green]COMPLÉTÉ[/]"
            if challenge.completed
            else "[bold yellow]EN COURS[/]"
        )

        content = Table.grid(padding=(0, 1))
        content.add_column()

        content.add_row(f"[bold]📅 {challenge.title} ({status})[/]")
        content.add_row("")
        content.add_row(f"{challenge.description}")
        content.add_row("")
        content.add_row(f"[bold]Instructions:[/] {challenge.instructions}")
        content.add_row("")
        content.add_row(f"[bold]Exemple:[/] {challenge.example}")
        content.add_row("")

        if challenge.tips:
            content.add_row(f"[bold {self.theme['info']}]💡 Conseils:[/]")
            for tip in challenge.tips:
                content.add_row(f"• {tip}")
            content.add_row("")

        content.add_row(
            f"[bold {self.theme['success']}]⭐ Récompense: {challenge.xp_reward} XP[/]"
        )

        self.console.print(
            Panel(
                content,
                title="[bold]🎯 Défi Quotidien[/]",
                border_style=self.theme["streak"],
                padding=(1, 2),
                box=ROUNDED,
            )
        )

    def loading(self, message: str = "Chargement...") -> None:
        """Display loading message."""
        self.console.print(f"[{self.theme['muted']}]⏳ {message}[/]")

    def success(self, message: str) -> None:
        """Display success message."""
        self.console.print(f"[{self.theme['success']}]✅ {message}[/]")

    def error(self, message: str) -> None:
        """Display error message."""
        self.console.print(
            Panel(
                f"[bold {self.theme['error']}]❌ Erreur[/]\n{message}",
                border_style=self.theme["error"],
                box=ROUNDED,
            )
        )

    def info(self, message: str) -> None:
        """Display info message."""
        self.console.print(f"[{self.theme['muted']}]ℹ️  {message}[/]")

    def prompt_continue(
        self, message: str = "Appuyez sur Entrée pour continuer..."
    ) -> None:
        """Display continue prompt."""
        self.console.print(f"\n[{self.theme['muted']}] {message}[/]")
