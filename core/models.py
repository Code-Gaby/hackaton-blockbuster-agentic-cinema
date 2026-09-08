from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

@dataclass
class CharacterDNA:
    courage: int = 75
    intelligence: int = 80
    empathy: int = 65
    trust: int = 50
    ambition: int = 85
    aggression: int = 40
    creativity: int = 90
    resilience: int = 70

    def to_dict(self) -> Dict[str, int]:
        return {
            "courage": self.courage,
            "intelligence": self.intelligence,
            "empathy": self.empathy,
            "trust": self.trust,
            "ambition": self.ambition,
            "aggression": self.aggression,
            "creativity": self.creativity,
            "resilience": self.resilience
        }

@dataclass
class Relationship:
    target_character_id: str
    target_character_name: str
    rel_type: str  # LOVE, FRIENDSHIP, CONFLICT, FAMILY, RIVALRY, MENTORSHIP, BETRAYAL
    strength: int  # 1-100
    history: str
    key_scenes: List[int] = field(default_factory=list)
    status: str = "Active"

@dataclass
class Character:
    id: str
    name: str
    age: int
    role: str  # Protagonist, Antagonist, Supporting, Mentor, Foil
    archetype: str  # The Rebel, The Sage, The Hero, The Visionary
    occupation: str
    personality: str
    motivation: str
    fears: str
    strengths: str
    weaknesses: str
    arc: Dict[str, str] = field(default_factory=dict)  # {"Act I": "...", "Act II": "...", "Act III": "..."}
    emotional_state: str = "Neutral"
    wardrobe: str = ""
    props: List[str] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    dna: CharacterDNA = field(default_factory=CharacterDNA)
    avatar_url: str = ""

@dataclass
class Scene:
    scene_number: int
    title: str
    slugline: str  # EXT. WAREHOUSE - NIGHT
    location: str
    interior_exterior: str  # INT or EXT
    day_night: str  # DAY or NIGHT
    summary: str
    script_text: str
    characters: List[str] = field(default_factory=list)
    props: List[str] = field(default_factory=list)
    wardrobe: List[str] = field(default_factory=list)
    makeup: List[str] = field(default_factory=list)
    vehicles: List[str] = field(default_factory=list)
    animals: List[str] = field(default_factory=list)
    stunts: List[str] = field(default_factory=list)
    vfx: List[str] = field(default_factory=list)
    sfx: List[str] = field(default_factory=list)
    special_equipment: List[str] = field(default_factory=list)
    complexity: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    risk_score: int = 35  # 0 - 100
    estimated_cost: float = 1500.0

@dataclass
class BudgetDriver:
    category: str  # VFX, Locations, Night shoots, Extras, Stunts
    amount: float
    description: str

@dataclass
class BudgetOptimizationOption:
    id: str
    title: str
    description: str
    estimated_savings: float
    impact_level: str  # Minor, Moderate, Major
    affected_scenes: List[int]
    status: str = "Available"  # Available, Applied

@dataclass
class ContinuityAlert:
    id: str
    scene_number: int
    character_name: str
    issue_type: str  # Wardrobe, Prop, Location, Relationship, Injury, Fact
    description: str
    suggested_fix: str
    status: str = "Pending"  # Pending, Resolved (KEEP), Fixed (FIX), Ignored (IGNORE)

@dataclass
class HealthScores:
    creative_score: int = 88
    production_score: int = 76
    budget_score: int = 82
    continuity_score: int = 94
    risk_score: int = 70

    @property
    def overall(self) -> int:
        return int((self.creative_score + self.production_score + self.budget_score + self.continuity_score + (100 - self.risk_score)) / 5)

@dataclass
class Project:
    id: str
    title: str
    tagline: str
    genre: str
    format: str  # FILM, THEATRE, SERIES
    runtime_minutes: int
    tone: str
    target_audience: str
    status: str  # CONCEPT, SCRIPTING, PRE-PRODUCTION, PRODUCTION, POST-PRODUCTION
    progress_percentage: int
    target_budget: float
    estimated_budget: float
    shooting_days: int
    crew_count: int
    available_locations: int
    synopsis: str
    logline: str
    visual_aesthetic: str
    characters: List[Character] = field(default_factory=list)
    scenes: List[Scene] = field(default_factory=list)
    budget_drivers: List[BudgetDriver] = field(default_factory=list)
    budget_options: List[BudgetOptimizationOption] = field(default_factory=list)
    continuity_alerts: List[ContinuityAlert] = field(default_factory=list)
    health_scores: HealthScores = field(default_factory=HealthScores)
    eco_impact_score: int = 82  # 0 - 100
    age_rating: str = "PG-13"
    content_advisories: List[str] = field(default_factory=list)
    history_logs: List[Dict[str, Any]] = field(default_factory=list)
