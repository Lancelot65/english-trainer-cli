"""Achievements system for English Trainer."""

from typing import List, Dict, Callable
from datetime import datetime
from .models import TrainerState


class Achievement:
    """Represents an achievement that can be unlocked by the user."""
    
    def __init__(self, name: str, description: str, condition: Callable[[TrainerState], bool]):
        self.name = name
        self.description = description
        self.condition = condition
        self.unlocked = False
        self.unlock_date: str = ""


class AchievementService:
    """Service for managing user achievements."""
    
    def __init__(self):
        self.achievements: List[Achievement] = [
            Achievement(
                "Premiers pas",
                "Complétez votre premier exercice",
                lambda state: state.total_exercises >= 1
            ),
            Achievement(
                "Débutant assidu",
                "Complétez 10 exercices",
                lambda state: state.total_exercises >= 10
            ),
            Achievement(
                "Élève studieux",
                "Complétez 50 exercices",
                lambda state: state.total_exercises >= 50
            ),
            Achievement(
                "Champion de la traduction",
                "Complétez 100 exercices",
                lambda state: state.total_exercises >= 100
            ),
            Achievement(
                "Perfectionniste",
                "Obtenez un score de 10 sur un exercice",
                lambda state: any(attempt.score == 10 for attempt in state.attempts)
            ),
            Achievement(
                "Expert des révisions",
                "Complétez 20 révisions",
                lambda state: len([r for r in state.review if hasattr(r, 'completed') and r.completed]) >= 20
            ),
            Achievement(
                "Collectionneur de leçons",
                "Sauvegardez 5 leçons dans votre cahier",
                lambda state: len(state.notebook) >= 5
            ),
            Achievement(
                "Polyglotte en herbe",
                "Atteignez le niveau B1",
                lambda state: state.level_num >= 3
            ),
            Achievement(
                "Motivé",
                "Maintenez une série de 7 jours",
                lambda state: state.streak >= 7
            ),
            Achievement(
                "Déterminé",
                "Maintenez une série de 30 jours",
                lambda state: state.streak >= 30
            ),
            Achievement(
                "Défi accepté",
                "Relevez 5 défis quotidiens",
                lambda state: len([c for c in state.daily_challenges if c.completed]) >= 5
            ),
            Achievement(
                "Explorateur",
                "Essayez tous les thèmes disponibles",
                lambda state: len(set(attempt.theme for attempt in state.attempts if attempt.theme)) >= 10
            ),
        ]
    
    def check_achievements(self, state: TrainerState) -> List[str]:
        """
        Check for newly unlocked achievements.
        
        Args:
            state: Current trainer state
            
        Returns:
            List of newly unlocked achievement names
        """
        newly_unlocked = []
        
        for achievement in self.achievements:
            if not achievement.unlocked and achievement.condition(state):
                achievement.unlocked = True
                achievement.unlock_date = datetime.now().strftime("%Y-%m-%d")
                newly_unlocked.append(achievement.name)
                
                # Add to state achievements if not already there
                if achievement.name not in state.achievements:
                    state.achievements.append(achievement.name)
        
        return newly_unlocked
    
    def get_unlocked_achievements(self) -> List[Achievement]:
        """Get all unlocked achievements."""
        return [a for a in self.achievements if a.unlocked]
    
    def get_locked_achievements(self) -> List[Achievement]:
        """Get all locked achievements."""
        return [a for a in self.achievements if not a.unlocked]


# Global achievement service instance
achievement_service = AchievementService()