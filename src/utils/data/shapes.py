from dataclasses import dataclass
from enum import Enum


class Rarity(str, Enum):
    N = "N"
    R = "R"
    SR = "SR"
    SSR = "SSR"


class Category(Enum):
    CHARACTER_EXP_GROWTH = "CharacterExpGrowth"  # Activity Report
    COIN = "Coin"
    COLLECTIBLE = "Collectible"
    CONSUMABLE = "Consumable"
    FAVOR = "Favor"  # Gift
    MATERIAL = "Material"
    SECRET_STONE = "SecretStone"  # Eleph


class SubCategory(Enum):
    ARTIFACT = "Artifact"
    BOOK_ITEM = "BookItem"  # Tech Notes
    CD_ITEM = "CDItem"  # Tactical Training Blu-ray


@dataclass
class Item:
    id: int
    category: Category
    rarity: Rarity
    icon: str
    name: str
    sub_category: SubCategory | None
    tags: list[str]


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


@dataclass
class Currency:
    id: int
    rarity: Rarity
    icon: str
    name: str
    desc: str
