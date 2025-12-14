"""Curriculum and learning content definitions."""

from typing import Dict, List


class Curriculum:
    """English learning curriculum organized by CEFR levels."""
    
    LEVELS: Dict[str, List[str]] = {
        "A1 (Débutant)": [
            "Présent Simple (to be)",
            "Présent Simple (verbes d'action)",
            "Articles et Pluriels",
            "Pronoms Possessifs",
            "Questions simples (Do/Does)",
            "Il y a (There is/are)",
            "Prépositions de lieu",
            "Nombres et dates"
        ],
        "A2 (Élémentaire)": [
            "Présent Continu (be + ing)",
            "Prétérit Simple (réguliers)",
            "Prétérit Simple (irréguliers)",
            "Comparatifs et Superlatifs",
            "Futur proche (going to)",
            "Modaux simples (can, must, should)",
            "Quantificateurs (some, any, much, many)",
            "Prépositions de temps"
        ],
        "B1 (Intermédiaire)": [
            "Present Perfect Simple",
            "Past Continuous",
            "Futur Simple (will)",
            "Conditionnel Type 1 (If... will)",
            "Voix Passive (présent/passé)",
            "Gérondif vs Infinitif",
            "Modaux de probabilité",
            "Discours indirect (base)"
        ],
        "B2 (Intermédiaire Sup)": [
            "Present Perfect Continuous",
            "Past Perfect",
            "Conditionnel Type 2 & 3",
            "Discours Indirect (avancé)",
            "Modaux de déduction",
            "Connecteurs logiques",
            "Voix Passive (temps complexes)",
            "Relatives complexes"
        ],
        "C1 (Avancé)": [
            "Inversion (Had I known...)",
            "Subjonctif et structures formelles",
            "Phrasal Verbs avancés",
            "Structures emphatiques",
            "Nuances lexicales",
            "Style indirect libre",
            "Ellipse et substitution",
            "Registres de langue"
        ],
        "C2 (Maîtrise)": [
            "Style académique et formel",
            "Idiomes et expressions figées",
            "Archaïsmes et style littéraire",
            "Ironie et sous-entendus",
            "Variations dialectales",
            "Jeux de mots et calembours",
            "Rhétorique et argumentation",
            "Créativité linguistique"
        ]
    }
    
    @classmethod
    def get_all_lessons(cls) -> List[str]:
        """Get all lessons across all levels."""
        lessons = []
        for level_lessons in cls.LEVELS.values():
            lessons.extend(level_lessons)
        return lessons
    
    @classmethod
    def get_lessons_for_level(cls, level_name: str) -> List[str]:
        """Get lessons for a specific level."""
        return cls.LEVELS.get(level_name, [])
    
    @classmethod
    def find_lesson_level(cls, lesson: str) -> str:
        """Find which level a lesson belongs to."""
        for level, lessons in cls.LEVELS.items():
            if lesson in lessons:
                return level
        return "Unknown"


class Themes:
    """Thematic contexts for exercises."""
    
    AVAILABLE: List[str] = [
        "Aléatoire (Aucun)",
        "Voyage & Aventure",
        "Business & Travail",
        "Technologie & IA",
        "Cuisine & Restauration",
        "Cinéma & Culture",
        "Science & Nature",
        "Politique & Société",
        "Philosophie & Psychologie",
        "Sport & Santé",
        "Famille & Relations",
        "Éducation & Apprentissage",
        "Art & Créativité",
        "Environnement & Écologie",
        "Histoire & Géographie",
        "Actualités & Médias",
        "Littérature & Écriture"
    ]
    
    @classmethod
    def get_random_theme(cls) -> str:
        """Get a random theme (excluding 'Aléatoire')."""
        import random
        themes = [t for t in cls.AVAILABLE if not t.startswith("Aléatoire")]
        return random.choice(themes)
    
    @classmethod
    def is_valid_theme(cls, theme: str) -> bool:
        """Check if theme is valid."""
        return theme in cls.AVAILABLE


class DifficultyLevels:
    """Difficulty level mappings."""
    
    CEFR_TO_NUMERIC = {
        "A1": 1,
        "A2": 2,
        "B1": 3,
        "B2": 4,
        "C1": 5,
        "C2": 6
    }
    
    NUMERIC_TO_CEFR = {v: k for k, v in CEFR_TO_NUMERIC.items()}
    
    @classmethod
    def get_numeric_level(cls, cefr_level: str) -> int:
        """Convert CEFR level to numeric."""
        # Extract just the level part (e.g., "A1" from "A1 (Débutant)")
        level_code = cefr_level.split()[0] if " " in cefr_level else cefr_level
        return cls.CEFR_TO_NUMERIC.get(level_code, 1)
    
    @classmethod
    def get_cefr_level(cls, numeric_level: int) -> str:
        """Convert numeric level to CEFR."""
        return cls.NUMERIC_TO_CEFR.get(numeric_level, "A1")