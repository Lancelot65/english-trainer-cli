"""Main application controller for English Trainer."""

import time
from typing import Dict, List, Optional
from datetime import datetime

from .config import config
from .models import TrainerState, Attempt, DailyChallenge
from .services import (
    exercise_service,
    lesson_service,
    notebook_service,
    conversation_service,
    vocabulary_service,
    review_service,
    daily_challenge_service,
)
from .achievements import achievement_service
from ..data.curriculum import Curriculum, Themes
from ..data.storage import storage
from ..ui.components import ModernUI
from ..ui.input_handler import ModernInputHandler


class EnglishTrainerApp:
    """Main application controller."""

    def __init__(self):
        self.ui = ModernUI()
        self.input_handler = ModernInputHandler(config.history_file)
        self.state: TrainerState = TrainerState()  # Default state
        self.running = True

    def run(self) -> int:
        """
        Run the main application loop.

        Returns:
            Exit code (0 for success)
        """
        try:
            loaded_state = storage.load_state()
            self.state = loaded_state if loaded_state is not None else TrainerState()
            self.ui.info("English Trainer v7.0 - Chargé avec succès!")

            while self.running:
                # Check for new achievements
                new_achievements = achievement_service.check_achievements(self.state)
                if new_achievements:
                    for achievement in new_achievements:
                        self.ui.success(f"🏆 Nouveau succès débloqué: {achievement}")
                    storage.save_state(self.state)
                
                self._main_menu_loop()

            storage.save_state(self.state)
            self.ui.success("Données sauvegardées. À bientôt!")
            return 0

        except KeyboardInterrupt:
            self.ui.info("\nAu revoir!")
            return 0
        except Exception as e:
            self.ui.error(f"Erreur fatale: {e}")
            return 1

    def _main_menu_loop(self) -> None:
        """Main menu interaction loop."""
        self.ui.header(self.state)

        due_reviews = self.state.due_reviews
        has_notebook = len(self.state.notebook) > 0

        self.ui.main_menu(
            has_reviews=len(due_reviews) > 0,
            n_reviews=len(due_reviews),
            has_notebook=has_notebook,
            show_help=False,
        )

        command = self.input_handler.prompt().lower().strip()

        try:
            if command == "q":
                self.running = False
            elif command == "h":
                # Show help menu
                self.ui.clear()
                self.ui.header(self.state)
                self.ui.main_menu(
                    has_reviews=len(due_reviews) > 0,
                    n_reviews=len(due_reviews),
                    has_notebook=has_notebook,
                    show_help=True,
                )
                self.input_handler.prompt("Appuyez sur Entrée pour continuer...")
            elif command == "c":
                self._lesson_selection()
            elif command == "t":
                self._theme_selection()
            elif command == "e":
                self._interactive_lesson()
            elif command == "n":
                self._notebook_menu()
            elif command == "v" and due_reviews:
                self._review_session()
            elif command == "s":
                self._show_statistics()
            elif command == "conv":
                self._conversation_practice()
            elif command == "vocab":
                self._vocabulary_practice()
            elif command == "d":
                self._daily_challenge()
            else:
                # Default: new exercise
                self._exercise_session()

        except Exception as e:
            self.ui.error(f"Erreur: {e}")
            self.input_handler.prompt("Appuyez sur Entrée pour continuer...")

    def _lesson_selection(self) -> None:
        """Handle lesson focus selection."""
        self.ui.lesson_menu(Curriculum.LEVELS, self.state.current_lesson)

        # Create mapping for selection
        mapping = {}
        i = 1
        for lessons in Curriculum.LEVELS.values():
            for lesson in lessons:
                mapping[str(i)] = lesson
                i += 1

        choice = self.input_handler.prompt("Choix # : ")

        if choice == "0":
            self.state.current_lesson = ""
            self.ui.success("Focus désactivé (mode général)")
        elif choice in mapping:
            self.state.current_lesson = mapping[choice]
            self.ui.success(f"Focus: {self.state.current_lesson}")

        storage.save_state(self.state)
        self.input_handler.prompt()

    def _theme_selection(self) -> None:
        """Handle theme selection."""
        self.ui.theme_menu(Themes.AVAILABLE, self.state.current_theme)

        mapping = {str(i): theme for i, theme in enumerate(Themes.AVAILABLE, 1)}
        choice = self.input_handler.prompt("Choix # : ")

        if choice in mapping:
            selected_theme = mapping[choice]
            if selected_theme.startswith("Aléatoire"):
                self.state.current_theme = ""
            else:
                self.state.current_theme = selected_theme

            theme_name = self.state.current_theme or "Aucun"
            self.ui.success(f"Thème: {theme_name}")
            storage.save_state(self.state)

        self.input_handler.prompt()

    def _exercise_session(self) -> None:
        """Handle a single exercise session."""
        try:
            self.ui.loading("Génération de l'exercice...")
            exercise = exercise_service.generate_exercise(self.state)

            french_text = exercise["paragraph_fr"]
            notes = exercise.get("notes", "")

            self.ui.exercise_display(french_text, notes)

            translation = self.input_handler.prompt("Votre traduction : ")
            if translation.lower() in {"q", "quit", "exit"}:
                return

            if not translation.strip():
                return

            self.ui.loading("Correction en cours...")
            evaluation = exercise_service.evaluate_translation(
                french_text, translation, self.state.settings
            )

            score = evaluation["score"]

            # Update state
            attempt = Attempt(
                ts=time.time(),
                paragraph_fr=french_text,
                translation_en=translation,
                score=score,
                main_error=evaluation.get("main_error", ""),
                lesson_focus=self.state.current_lesson,
                theme=self.state.current_theme,
            )

            self.state.add_attempt(attempt)
            self.state.xp += score
            self.state.total_exercises += 1

            # Add to review if needed
            review_service.add_to_review(self.state, french_text, score)
            
            # Check for new achievements
            new_achievements = achievement_service.check_achievements(self.state)
            if new_achievements:
                for achievement in new_achievements:
                    self.ui.success(f"🏆 Nouveau succès débloqué: {achievement}")

            self.ui.feedback_display(evaluation)
            storage.save_state(self.state)

            self.input_handler.prompt("Appuyez sur Entrée pour continuer...")

        except Exception as e:
            self.ui.error(f"Erreur lors de l'exercice: {e}")
            self.input_handler.prompt()

    def _interactive_lesson(self) -> None:
        """Handle interactive lesson mode."""
        topic = self.state.current_lesson
        if not topic:
            topic = self.input_handler.prompt("Sujet à expliquer : ")

        if not topic:
            return

        try:
            self.ui.loading("Génération du cours...")
            lesson_content = lesson_service.generate_lesson(
                topic, self.state.level_name, self.state.settings
            )

            self.ui.lesson_content(lesson_content, f"Cours: {topic}")

            # Offer to save to notebook
            if self.input_handler.confirm("Sauvegarder ce cours dans le cahier?", True):
                title = self.input_handler.prompt(
                    "Titre du cours : ", default=f"Cours: {topic}"
                )
                tags = self.input_handler.prompt(
                    "Tags (séparés par des espaces) : "
                ).split()

                notebook_service.save_lesson(
                    self.state, title, lesson_content, topic, tags
                )
                self.ui.success("Cours sauvegardé dans le cahier!")
                
                # Check for achievements
                new_achievements = achievement_service.check_achievements(self.state)
                if new_achievements:
                    for achievement in new_achievements:
                        self.ui.success(f"🏆 Nouveau succès débloqué: {achievement}")
                storage.save_state(self.state)

            # Interactive Q&A
            self.ui.info(
                "Mode Q&A interactif - Posez vos questions (Entrée vide pour quitter)"
            )
            context = f"Leçon: {topic}\n{lesson_content}"

            while True:
                question = self.input_handler.prompt("Votre question ? ")
                if not question or question.lower() == "q":
                    break

                try:
                    self.ui.loading("Réflexion...")
                    answer = lesson_service.answer_question(
                        question,
                        context[-config.max_context_chars :],
                        self.state.settings,
                    )

                    self.ui.lesson_content(answer, "Réponse")
                    context += f"\nQ: {question}\nR: {answer}"

                except Exception as e:
                    self.ui.error(f"Erreur: {e}")

        except Exception as e:
            self.ui.error(f"Erreur lors du cours: {e}")
            self.input_handler.prompt()

    def _notebook_menu(self) -> None:
        """Handle notebook management."""
        while True:
            self.ui.clear()
            self.ui.notebook_display(self.state.notebook[-10:])  # Show last 10 entries

            print("\n[bold]Cahier de Cours[/]")
            print("1. Voir toutes les entrées")
            print("2. Rechercher")
            print("3. Filtrer par sujet")
            print("4. Marquer/démarquer favori")
            print("5. Supprimer une entrée")
            print("6. Voir les succès")
            print("0. Retour")

            choice = self.input_handler.prompt("Choix : ")

            if choice == "0":
                break
            elif choice == "1":
                self._show_all_notebook_entries()
            elif choice == "2":
                self._search_notebook()
            elif choice == "3":
                self._filter_notebook_by_topic()
            elif choice == "4":
                self._toggle_notebook_favorite()
            elif choice == "5":
                self._delete_notebook_entry()
            elif choice == "6":
                self._show_achievements()

    def _show_all_notebook_entries(self) -> None:
        """Show all notebook entries."""
        self.ui.clear()
        self.ui.notebook_display(self.state.notebook)
        self.input_handler.prompt()

    def _search_notebook(self) -> None:
        """Search notebook entries."""
        query = self.input_handler.prompt("Recherche : ")
        if query:
            results = notebook_service.search_notebook(self.state, query)
            self.ui.clear()
            self.ui.notebook_display(results)
            self.input_handler.prompt()

    def _filter_notebook_by_topic(self) -> None:
        """Filter notebook by topic."""
        topics = list(set(entry.topic for entry in self.state.notebook))
        if not topics:
            self.ui.info("Aucun sujet disponible")
            return

        print("Sujets disponibles:")
        for i, topic in enumerate(topics, 1):
            print(f"{i}. {topic}")

        choice = self.input_handler.prompt_number("Choix : ", 1, len(topics))
        if choice:
            topic = topics[choice - 1]
            results = notebook_service.get_by_topic(self.state, topic)
            self.ui.clear()
            self.ui.notebook_display(results)
            self.input_handler.prompt()

    def _toggle_notebook_favorite(self) -> None:
        """Toggle favorite status of notebook entry."""
        if not self.state.notebook:
            self.ui.info("Cahier vide")
            return

        index = self.input_handler.prompt_number(
            "Numéro de l'entrée : ", 1, len(self.state.notebook)
        )
        if index:
            if notebook_service.toggle_favorite(self.state, index - 1):
                self.ui.success("Statut favori modifié!")
            else:
                self.ui.error("Entrée non trouvée")

    def _delete_notebook_entry(self) -> None:
        """Delete a notebook entry."""
        if not self.state.notebook:
            self.ui.info("Cahier vide")
            return

        index = self.input_handler.prompt_number(
            "Numéro de l'entrée à supprimer : ", 1, len(self.state.notebook)
        )
        if index and self.input_handler.confirm("Confirmer la suppression?"):
            del self.state.notebook[index - 1]
            storage.save_state(self.state)
            self.ui.success("Entrée supprimée!")

    def _review_session(self) -> None:
        """Handle spaced repetition review session."""
        due_reviews = self.state.due_reviews
        if not due_reviews:
            self.ui.info("Aucune révision en attente")
            return

        for review_item in due_reviews[:5]:  # Limit to 5 reviews per session
            self.ui.clear()
            self.ui.exercise_display(review_item.paragraph_fr, "RÉVISION")

            translation = self.input_handler.prompt("Traduction : ")
            if not translation or translation.lower() == "q":
                break

            try:
                self.ui.loading("Correction...")
                evaluation = exercise_service.evaluate_translation(
                    review_item.paragraph_fr, translation, self.state.settings
                )

                score = evaluation["score"]
                self.ui.feedback_display(evaluation)

                # Update review schedule
                review_service.process_review_result(self.state, review_item, score)
                
                # Check for achievements
                new_achievements = achievement_service.check_achievements(self.state)
                if new_achievements:
                    for achievement in new_achievements:
                        self.ui.success(f"🏆 Nouveau succès débloqué: {achievement}")

                if score >= 8:
                    self.ui.success(
                        f"Excellent! Revu dans {review_item.interval_days} jours."
                    )
                else:
                    self.ui.info("À revoir prochainement.")

                self.input_handler.prompt()

            except Exception as e:
                self.ui.error(f"Erreur: {e}")
                break

    def _show_statistics(self) -> None:
        """Show user statistics."""
        self.ui.statistics_display(self.state)
        self.input_handler.prompt()

    def _conversation_practice(self) -> None:
        """Handle conversation practice mode."""
        topic = self.input_handler.prompt("Sujet de conversation : ")
        if not topic:
            return

        try:
            self.ui.loading("Démarrage de la conversation...")
            opening = conversation_service.start_conversation(
                topic, self.state.level_name, self.state.settings
            )

            context = f"Topic: {topic}\n{opening}"
            self.ui.lesson_content(opening, "Conversation")

            while True:
                message = self.input_handler.prompt("Vous : ")
                if not message or message.lower() == "q":
                    break

                try:
                    response = conversation_service.continue_conversation(
                        message,
                        context[-config.max_context_chars :],
                        self.state.settings,
                    )

                    self.ui.lesson_content(response, "Partenaire")
                    context += f"\nVous: {message}\nPartenaire: {response}"

                except Exception as e:
                    self.ui.error(f"Erreur: {e}")
                    break

        except Exception as e:
            self.ui.error(f"Erreur: {e}")
            self.input_handler.prompt()

    def _vocabulary_practice(self) -> None:
        """Handle vocabulary practice mode."""
        theme = self.input_handler.prompt("Thème vocabulaire : ")
        if not theme:
            return

        count = self.input_handler.prompt_number("Nombre de mots : ", 5, 20, 10)
        if not count:
            return

        try:
            self.ui.loading("Génération du vocabulaire...")
            vocab_set = vocabulary_service.generate_vocabulary_set(
                theme, self.state.level_name, count, self.state.settings
            )

            # Display vocabulary (implementation depends on vocab_set structure)
            self.ui.lesson_content(str(vocab_set), f"Vocabulaire: {theme}")
            self.input_handler.prompt()

        except Exception as e:
            self.ui.error(f"Erreur: {e}")
            self.input_handler.prompt()

    def _daily_challenge(self) -> None:
        """Handle daily challenge."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get or create today's challenge
        challenge = self.state.today_challenge
        if not challenge:
            # Generate new challenge
            self.ui.loading("Génération du défi quotidien...")
            challenge_data = daily_challenge_service.get_daily_challenge(today)
            challenge = DailyChallenge(
                date=today,
                challenge_type=challenge_data["challenge_type"],
                title=challenge_data["title"],
                description=challenge_data["description"],
                instructions=challenge_data["instructions"],
                example=challenge_data["example"],
                tips=challenge_data.get("tips", []),
                xp_reward=challenge_data.get("xp_reward", 10)
            )
            self.state.add_daily_challenge(challenge)
            storage.save_state(self.state)
        
        # Display challenge
        self.ui.daily_challenge_display(challenge)
        
        # If not completed, allow user to attempt it
        if not challenge.completed:
            if self.input_handler.confirm("Voulez-vous relever ce défi ?"):
                self.ui.info(challenge.instructions)
                self.ui.info(f"Exemple: {challenge.example}")
                
                # Challenge-specific handling based on type
                if challenge.challenge_type == "translation":
                    user_input = self.input_handler.prompt("Votre traduction : ")
                elif challenge.challenge_type == "writing":
                    user_input = self.input_handler.prompt_multiline("Votre texte : ")
                else:
                    user_input = self.input_handler.prompt("Votre réponse : ")
                
                if user_input and user_input.lower() != "q":
                    # For now, we'll just mark it as completed
                    # In a more advanced version, we could evaluate the response
                    if self.state.complete_today_challenge():
                        self.ui.success(f"Défi relevé ! Vous gagnez {challenge.xp_reward} XP !")
                        
                        # Check for achievements
                        new_achievements = achievement_service.check_achievements(self.state)
                        if new_achievements:
                            for achievement in new_achievements:
                                self.ui.success(f"🏆 Nouveau succès débloqué: {achievement}")
                        
                        self.ui.header(self.state)  # Update header to show new XP
                    else:
                        self.ui.info("Défi déjà complété.")
        else:
            self.ui.success("Vous avez déjà relevé aujourd'hui !")
        
        self.input_handler.prompt()

    def _show_achievements(self) -> None:
        """Show user achievements."""
        self.ui.clear()
        self.ui.achievements_display(self.state.achievements)
        self.input_handler.prompt()


def main() -> int:
    """Main entry point."""
    app = EnglishTrainerApp()
    return app.run()


if __name__ == "__main__":
    exit(main())
