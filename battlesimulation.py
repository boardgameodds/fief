from dataclasses import dataclass
from enum import Enum
import random
import copy
import csv

# ============================================================
# Constants and bit-size calculations
# ============================================================

MAX_MEN_AT_ARMS = 13
"""Maximum number of men-at-arms allowed in an army."""

BIN_SIZE_MEN_AT_ARMS = len(bin(MAX_MEN_AT_ARMS)) - 2
"""Number of bits required to encode men-at-arms."""

MAX_KNIGHTS = 8
"""Maximum number of knights allowed in an army."""

BIN_SIZE_KNIGHTS = len(bin(MAX_KNIGHTS)) - 2
"""Number of bits required to encode knights."""


# ============================================================
# Enumerations
# ============================================================

class DamageStrategy(Enum):
    """
    Determines the order in which damage is applied to unit types.
    """
    MEN_AT_ARMS_FIRST = 0
    KNIGHTS_FIRST = 1


class DefensiveStructure(Enum):
    """
    Defensive structures provide penalties to attacking armies.
    """
    NONE = 0
    STRONGHOLD = 1
    FORTIFIED_CITY = 2


class ArmyLeader(Enum):
    """
    Represents leadership quality and special bonuses.
    """
    NONE_OR_LADY = 0
    LORD_OR_TITLED_LADY = 1
    DARC = 2


BIN_SIZE_DAMAGE_STRATEGY = len(bin(DamageStrategy.KNIGHTS_FIRST.value)) - 2
BIN_SIZE_ARMY_LEADER = len(bin(ArmyLeader.LORD_OR_TITLED_LADY.value)) - 2
BIN_SIZE_DEFENSIVE_STRUCTURE = len(bin(DefensiveStructure.FORTIFIED_CITY.value)) - 2


# ============================================================
# Army
# ============================================================

@dataclass
class Army:
    """
    Represents a single army participating in a battle.

    Attributes:
        men_at_arms (int): Light infantry (1 damage point each).
        knights (int): Heavy cavalry (3 damage points each).
        structure (DefensiveStructure): Defensive fortification.
        leader (ArmyLeader): Army leader type.
    """
    men_at_arms: int
    knights: int
    structure: DefensiveStructure = DefensiveStructure.NONE
    leader: ArmyLeader = ArmyLeader.NONE_OR_LADY

    def hash(self):
        """
        Encodes the army state into a compact integer using bit packing.

        Returns:
            int: Hash representing the army state.
        """
        if self.men_at_arms > MAX_MEN_AT_ARMS:
            raise Exception("Too many men-at-arms")
        if self.knights > MAX_KNIGHTS:
            raise Exception("Too many knights")

        h = 0
        offset = 0

        h |= self.men_at_arms << offset
        offset += BIN_SIZE_MEN_AT_ARMS

        h |= self.knights << offset
        offset += BIN_SIZE_KNIGHTS

        h |= self.structure.value << offset
        offset += BIN_SIZE_DEFENSIVE_STRUCTURE

        h |= self.leader.value << offset
        offset += BIN_SIZE_ARMY_LEADER

        return h

    def __hash__(self):
        """Allows Army to be used as a dictionary key."""
        return self.hash()

    def is_defeated(self):
        """
        Checks whether the army has no remaining units.

        Returns:
            bool: True if defeated.
        """
        return (self.knights + self.men_at_arms) <= 0

    def compute_damage_maa_first(self, damage):
        """
        Applies damage prioritizing men-at-arms.

        Args:
            damage (int): Incoming damage points.

        Returns:
            tuple: (remaining_damage, knights, men_at_arms)
        """
        d = damage
        k = self.knights
        m = self.men_at_arms

        while d >= 1 and m > 0:
            if d >= 3 and m <= 2 and k > 0:
                k -= 1
                d -= 3
                continue
            m -= 1
            d -= 1

        while d >= 3 and k > 0:
            k -= 1
            d -= 3

        return d, k, m

    def compute_damage_knights_first(self, damage):
        """
        Applies damage prioritizing knights.

        Args:
            damage (int): Incoming damage points.

        Returns:
            tuple: (remaining_damage, knights, men_at_arms)
        """
        d = damage
        k = self.knights
        m = self.men_at_arms

        while d >= 3 and k > 0:
            k -= 1
            d -= 3

        while d >= 1 and m > 0:
            m -= 1
            d -= 1

        return d, k, m

    def apply_damage(self, damage, strategy=DamageStrategy.MEN_AT_ARMS_FIRST):
        """
        Applies damage using the chosen damage strategy.

        Args:
            damage (int): Incoming damage points.
            strategy (DamageStrategy): Damage allocation rule.

        Returns:
            int: Remaining unused damage.
        """
        dk, kk, mk = self.compute_damage_knights_first(damage)
        dm, km, mm = self.compute_damage_maa_first(damage)

        if dk != dm:
            raise Exception("Illegal damage strategy")

        if strategy == DamageStrategy.KNIGHTS_FIRST:
            d, self.knights, self.men_at_arms = dk, kk, mk
        elif strategy == DamageStrategy.MEN_AT_ARMS_FIRST:
            d, self.knights, self.men_at_arms = dm, km, mm
        else:
            raise Exception("Unknown strategy")

        return d

    def army_points(self):
        """
        Computes raw combat strength.

        Returns:
            int: Total army points.
        """
        return (self.knights * 3) + self.men_at_arms

    def strength_points(self):
        """
        Computes army strength including leader bonuses.

        Returns:
            int: Strength points.
        """
        bonus = 0
        if self.leader in (ArmyLeader.LORD_OR_TITLED_LADY, ArmyLeader.DARC):
            bonus = 1
        return self.army_points() + bonus

    def dice(self, penalty=0):
        """
        Determines the number of dice rolled in combat.

        Args:
            penalty (int): Dice penalty from enemy defenses.

        Returns:
            int: Dice count (minimum 0).
        """
        if self.army_points() == 0:
            return 0

        s = self.strength_points()
        if s <= 6:
            d = 1
        elif s <= 12:
            d = 2
        else:
            d = 3

        d += penalty

        if self.leader == ArmyLeader.DARC:
            d += 1

        return max(d, 0)

    def attacker_penalty(self):
        """
        Returns dice penalties imposed on attackers.

        Returns:
            int: Penalty value.
        """
        if self.structure == DefensiveStructure.FORTIFIED_CITY:
            return -2
        if self.structure == DefensiveStructure.STRONGHOLD:
            return -1
        return 0


BIN_SIZE_ARMY = (
    BIN_SIZE_MEN_AT_ARMS
    + BIN_SIZE_KNIGHTS
    + BIN_SIZE_DEFENSIVE_STRUCTURE
    + BIN_SIZE_ARMY_LEADER
)


# ============================================================
# Dice mechanics
# ============================================================

@dataclass
class BattleDiceSet:
    """
    Represents a set of dice rolled during battle.
    """
    dice: int = 1

    def roll(self, dice_bonus=0):
        """
        Rolls all dice and sums results.

        Args:
            dice_bonus (int): Bonus added per die.

        Returns:
            int: Total roll value.
        """
        total = 0
        for _ in range(self.dice):
            total += random.randint(1, 3)
            total += dice_bonus
        return total


DICE_SETS = {
    0: BattleDiceSet(0),
    1: BattleDiceSet(1),
    2: BattleDiceSet(2),
    3: BattleDiceSet(3),
    4: BattleDiceSet(4),
}


# ============================================================
# Battle
# ============================================================

class BattleStopRule(Enum):
    """
    Determines when a battle stops.
    """
    ANNIHILATION = 0


@dataclass
class Battle:
    """
    Represents a battle between two armies.
    """
    a: Army
    b: Army
    a_strategy: DamageStrategy = DamageStrategy.MEN_AT_ARMS_FIRST
    b_strategy: DamageStrategy = DamageStrategy.MEN_AT_ARMS_FIRST
    cavalcade: bool = False

    def hash(self):
        """
        Encodes the full battle state into a compact integer.

        Returns:
            int: Hash value.
        """
        h = 0
        offset = 0

        h |= self.a.hash() << offset
        offset += BIN_SIZE_ARMY

        h |= self.a_strategy.value << offset
        offset += BIN_SIZE_DAMAGE_STRATEGY

        h |= self.b.hash() << offset
        offset += BIN_SIZE_ARMY

        h |= self.b_strategy.value << offset
        offset += BIN_SIZE_DAMAGE_STRATEGY

        h |= (1 if self.cavalcade else 0) << offset
        offset += 1

        return h

    def __hash__(self):
        """Allows Battle to be cached."""
        return self.hash()
