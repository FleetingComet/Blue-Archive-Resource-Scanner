from dataclasses import dataclass
from enum import Enum


class Rarity(str, Enum):
    N = "N"
    R = "R"
    SR = "SR"
    SSR = "SSR"


@dataclass
class Item:
    id: int
    name: str
    rarity: Rarity
    icon: str


@dataclass
class Student:
    id: int
    name: str
    # icon: str
    DefaultOrder: int
    # Striker ("Main") or Special ("Support")
    SquadType: str
    # Group them
    BulletType: str
    ArmorType: str
    School: str
    Club: str
    hasBondGear: bool = False
    StarGrade: int = 1  # lowest rarity

    # For Dual Style Characters
    StyleId: int | None = None
    LinkedCharacterId: int | None = None


@dataclass
class Equipment:
    id: int
    category: str
    rarity: Rarity
    tier: int
    icon: str
    name: str
