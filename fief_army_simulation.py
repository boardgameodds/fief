from dataclasses import dataclass
from enum import Enum

MAX_MEN_AT_ARMS = 13
BIN_SIZE_MEN_AT_ARMS = len(bin(MAX_MEN_AT_ARMS)) - 2
MAX_KNIGHTS = 8
BIN_SIZE_KNIGHTS = len(bin(MAX_KNIGHTS)) - 2

class DamageStrategy(Enum):
    MEN_AT_ARMS_FIRST = 0
    KNIGHTS_FIRST = 1

class DefensiveStructure(Enum):
    NONE = 0
    STRONGHOLD = 1
    FORTIFIED_CITY = 2

class ArmyLeader(Enum):
    NONE_OR_LADY = 0
    LORD_OR_TITLED_LADY = 1
    DARC = 2
    

BIN_SIZE_DAMAGE_STRATEGY = len(bin(DamageStrategy.KNIGHTS_FIRST.value)) - 2
BIN_SIZE_ARMY_LEADER = len(bin(ArmyLeader.LORD_OR_TITLED_LADY.value)) - 2
BIN_SIZE_DEFENSIVE_STRUCTURE = len(bin(DefensiveStructure.FORTIFIED_CITY.value)) - 2

@dataclass
class Army:
    men_at_arms: int
    knights: int
    structure: DefensiveStructure = DefensiveStructure.NONE
    leader: ArmyLeader = ArmyLeader.NONE_OR_LADY

    def hash(self):
        if self.men_at_arms > MAX_MEN_AT_ARMS:
            raise Exception()
        if self.knights > MAX_KNIGHTS:
            raise Exception()
        h = 0
        offset = 0
        
        h |= self.men_at_arms << offset
        offset += BIN_SIZE_MEN_AT_ARMS

        h |= self.knights  << offset
        offset += BIN_SIZE_KNIGHTS

        h |= self.structure.value << offset
        offset += BIN_SIZE_DEFENSIVE_STRUCTURE

        h |= self.leader.value << offset
        offset += BIN_SIZE_ARMY_LEADER

        return h

    def __hash__(self):
        return self.hash()

    def is_defeated(self):
        return (self.knights + self.men_at_arms) <= 0

    def compute_damage_maa_first(self, damage):
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

    def apply_damage(self, damage, strategy = DamageStrategy.MEN_AT_ARMS_FIRST):
        dk, kk, mk = self.compute_damage_knights_first(damage)
        dm, km, mm = self.compute_damage_maa_first(damage)
        if dk != dm:
            print(self, damage)
            raise Exception("illegal strategy")
        if strategy == DamageStrategy.KNIGHTS_FIRST:
            d, self.knights, self.men_at_arms = dk, kk, mk
        elif strategy == DamageStrategy.MEN_AT_ARMS_FIRST:                
            d, self.knights, self.men_at_arms = dm, km, mm
        else:
            raise Exception()
        return d # remainder

    def army_points(self):
        return (self.knights * 3) + self.men_at_arms

    def strength_points(self):
        bonus = 0
        if self.leader == ArmyLeader.LORD_OR_TITLED_LADY:
            bonus = 1
        elif self.leader == ArmyLeader.DARC:
            bonus = 1
        return self.army_points() + bonus

    def dice(self, penalty = 0):
        if self.army_points() == 0:
            return 0
        s = self.strength_points()
        d = 0
        if s >= 1 and s <= 6:
            d = 1
        elif s <= 12:
            d = 2
        elif s >= 13:
            d = 3
        d += penalty
        if self.leader == ArmyLeader.DARC:
            d += 1
        if d < 0:
            d = 0
        return d

    def attacker_penalty(self):
        if self.structure == DefensiveStructure.FORTIFIED_CITY:
            return -2
        if self.structure == DefensiveStructure.STRONGHOLD:
            return -1
        return 0

BIN_SIZE_ARMY = BIN_SIZE_MEN_AT_ARMS + BIN_SIZE_KNIGHTS + BIN_SIZE_DEFENSIVE_STRUCTURE + BIN_SIZE_ARMY_LEADER

import random, copy

@dataclass
class BattleDiceSet:
    dice: int = 1

    def roll(self, dice_bonus = 0):
        d = 0
        for i in range(self.dice):
            d += random.randint(1, 3)
            d += dice_bonus
        return d

DICE_SETS = {0: BattleDiceSet(0), 1: BattleDiceSet(1), 2: BattleDiceSet(2), 3: BattleDiceSet(3), 4: BattleDiceSet(4)}

class BattleStopRule(Enum):
    ANNIHILATION = 0

@dataclass
class Battle:
    a: Army
    b: Army
    a_strategy: DamageStrategy = DamageStrategy.MEN_AT_ARMS_FIRST
    b_strategy: DamageStrategy = DamageStrategy.MEN_AT_ARMS_FIRST
    cavalcade: bool = False

    def hash(self):
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
        return self.hash()

    def battle_status(self):
        ai = self.a
        bi = self.b
        penaltyA = bi.attacker_penalty()
        penaltyB = ai.attacker_penalty()
        dcA = ai.dice(penaltyA)
        dcB = bi.dice(penaltyB)
        if dcA == 0 or dcB == 0:
            if dcA == 0 and dcB == 0:
                return "resolved", "mutual destruction", 0
            elif dcA == 0:
                return "resolved", "success", -1
            elif dcB == 0:
                return "resolved", "failure", 1
        if ai.is_defeated() or bi.is_defeated():
            if ai.is_defeated() and bi.is_defeated():
                return "resolved", "mutual destruction", 0
            elif ai.is_defeated():
                return "resolved", "success", -1
            elif bi.is_defeated():
                return "resolved", "failure", 1
        return "ongoing", ai.army_points(), bi.army_points()

    def battle_iterator(self):
        while True:
            ai = self.a
            bi = self.b
            astrat = self.a_strategy
            bstrat = self.b_strategy
            penaltyA = bi.attacker_penalty()
            penaltyB = ai.attacker_penalty()
            dcA = ai.dice(penaltyA)
            dcB = bi.dice(penaltyB)
            if dcA == 0 or dcB == 0:
                if dcA == 0 and dcB == 0:
                    yield "resolved", "mutual destruction", 0
                elif dcA == 0:
                    yield "resolved", "success", -1
                elif dcB == 0:
                    yield "resolved", "failure", 1
                break
            dA = DICE_SETS[dcA].roll()
            dB = DICE_SETS[dcB].roll(1 if self.cavalcade else 0)
            ai.apply_damage(dB, astrat)
            bi.apply_damage(dA, bstrat)
            if ai.is_defeated() or bi.is_defeated():
                if ai.is_defeated() and bi.is_defeated():
                    yield "resolved", "mutual destruction", 0
                elif ai.is_defeated():
                    yield "resolved", "success", -1
                elif bi.is_defeated():
                    yield "resolved", "failure", 1
                break
            yield "ongoing", ai.army_points(), bi.army_points()

    def resolve(self):
        result = None
        for step in self.battle_iterator():
            result = step
        return result

class BattleCache:

    def __init__(self):
        self.db = {}

    def probability(self, battle: Battle):
        w, t, l, s = self.db.get(battle, (0, 0, 0, 0))
        return w / s, l / s, t / s, s

    def resolve(self, battle: Battle):
        w, t, l, s = self.db.get(battle, (0, 0, 0, 0))
        if s < 1000: #reliability number
            b = copy.deepcopy(battle)
            status, res, indicator = b.battle_status()
            if status == "resolved":
                if indicator == 1:
                    w += 1
                    s += 1
                elif indicator == 0:
                    t += 1
                    s += 1
                elif indicator == -1:
                    l += 1
                    s += 1
                else:
                    raise Exception()
                self.db[battle] = w, t, l, s
                return indicator
            next(b.battle_iterator())
            indicator = self.resolve(b)
            if indicator == 1:
                w += 1
                s += 1
            elif indicator == 0:
                t += 1
                s += 1
            elif indicator == -1:
                l += 1
                s += 1
            else:
                raise Exception(b, indicator)
            self.db[battle] = w, t, l, s
            return indicator
        # if more than 1000 times simulated, return rng based result
        return random.sample(population=[1, 0, -1], k=1, counts=[w, t, l])[0]

    def populate(self, report_iteration = 1000):
        iteration = 0
        for a_lord in range(2, -1, -1):
            for a_kn in range(8, -1, -1):
                for a_maa in range(13, -1, -1):
                    for b_lord in range(2, -1, -1):
                        for b_defensive in range(2, -1, -1):
                            for b_kn in range(8, -1, -1):
                                for b_maa in range(13, -1, -1):
                                    if iteration % report_iteration == 0:
                                        print(f"iteration: {iteration}", end='\r')
                                    iteration += 1
                                    a, b = Army(a_maa, a_kn, DefensiveStructure.NONE, ArmyLeader(a_lord)), Army(b_maa, b_kn, DefensiveStructure(b_defensive), ArmyLeader(b_lord))
                                    self.resolve(Battle(a, b))

    def complete(self, limit = 1000, reverse = False, report_iteration = 1000):
        from datetime import datetime
        previous = datetime.now()
        items = sorted(self.db.items(), key=lambda x: x[1][3], reverse=reverse)
        battles = list(battle for battle, data in items)
        iteration = 0
        for i, battle in enumerate(battles):
            if iteration % report_iteration == 0:
                now = datetime.now()
                x = (now - previous).total_seconds()
                previous = now
                print(f"battles completed: {i} in {x} seconds", end='\n')
            iteration += 1
            data = self.db[battle]
            w, t, l, s = data
            for i in range(limit - s):
                self.resolve(battle)

    def serialize(self, path: str = "battle_odds.csv"):
        with open(path, 'w', newline='', encoding='ascii') as f:
            writer = csv.writer(f)
            headers = ["a_men", "a_knights", "a_leader", "a_strength", "a_structure", "b_men", "b_knights", "b_leader", "b_strength", "b_structure", "a_win_rate", "b_win_rate", "tie_rate"]
            writer.writerow(headers)

            for battle, data in self.db.items():
                w, t, l, s = data
                wa = w / s
                ti = t / s
                wb = l / s
                a = battle.a
                b = battle.b
                
                writer.writerow([a.men_at_arms, a.knights, a.leader.name, a.strength_points(), a.structure.name, b.men_at_arms, b.knights, b.leader.name, b.strength_points(), b.structure.name, wa, wb, ti])

BATTLE_CACHE = BattleCache()

def battle(a: Army, b: Army, stop_rule = BattleStopRule.ANNIHILATION):
    iterations = 1000
    resultsA = [0] * iterations
    resultsB = [0] * iterations
    penaltyA = b.attacker_penalty()
    penaltyB = a.attacker_penalty()

    winA = 0
    ties = 0
    winB = 0

    for i in range(iterations):
        ai = copy.copy(a)
        bi = copy.copy(b)
        while True:
            dcA = ai.dice(penaltyA)
            dcB = bi.dice(penaltyB)
            if dcA == 0 or dcB == 0:
                if dcA == 0 and dcB == 0:
                    ties += 1
                elif dcA == 0:
                    winB += 1
                elif dcB == 0:
                    winA += 1
                break
            dA = DICE_SETS[dcA].roll()
            dB = DICE_SETS[dcB].roll()
            ai.apply_damage(dB, DamageStrategy.MEN_AT_ARMS_FIRST)
            bi.apply_damage(dA, DamageStrategy.MEN_AT_ARMS_FIRST)
            resultsA[i], resultsB[i] = ai.army_points(), bi.army_points()
            if ai.is_defeated() or bi.is_defeated():
                if ai.is_defeated() and bi.is_defeated():
                    ties += 1
                elif ai.is_defeated():
                    winB += 1
                elif bi.is_defeated():
                    winA += 1
                break

    return winA / iterations, ties / iterations, winB / iterations

import csv

def write_csv(combinations):
    with open("odds.csv", 'w', newline='', encoding='ascii') as f:
        writer = csv.writer(f)
        headers = ["a_men", "a_knights", "a_leader", "a_structure", "b_men", "b_knights", "b_leader", "b_structure", "a_win_rate", "b_win_rate", "tie_rate"]
        writer.writerow(headers)

    
        for i in range(len(combinations)):
            if combinations[i].structure.value > 0:
                continue # cannot attack from a structure
            
            #losing = False
            for j in range(i, len(combinations)):
                #if losing:
                    #break
                a, b = combinations[i], combinations[j]
                if a.strength_points() < b.strength_points():
                    continue # players will never consider attacking such an opponent
                wa, ti, wb = battle(a, b)
                writer.writerow([a.men_at_arms, a.knights, a.leader.name, a.structure.name, b.men_at_arms, b.knights, b.leader.name, b.structure.name, wa, wb, ti])
                #if wa >= 0.95:
                #    losing = True # effectively all lower evaluated battles will be pointless to evaluate

def evaluate_b_combinations(a):
    for lord in range(1, -1, -1):
        for defensive in range(2, -1, -1):
            for kn in range(8, -1, -1):
                for maa in range(13, -1, -1):
                    b = Army(maa, kn, DefensiveStructure(defensive), ArmyLeader(lord))
                    if a.strength_points() < b.strength_points():
                        break
                    wa, ti, wb = battle(a, b)
                    yield a, b, wa, ti, wb
                    if wa >= 0.95:
                        break
    
def write_combinations():
    with open("odds.csv", 'w', newline='', encoding='ascii') as f:
        writer = csv.writer(f)
        headers = ["a_men", "a_knights", "a_leader", "a_structure", "b_men", "b_knights", "b_leader", "b_structure", "a_win_rate", "b_win_rate", "tie_rate"]
        writer.writerow(headers)    

        for lord in range(1, -1, -1):
            for kn in range(8, -1, -1):
                for maa in range(13, -1, -1):
                    for a, b, wa, ti, wb in evaluate_b_combinations(Army(maa, kn, DefensiveStructure.NONE, ArmyLeader(lord))):
                        writer.writerow([a.men_at_arms, a.knights, a.leader.name, a.structure.name, b.men_at_arms, b.knights, b.leader.name, b.structure.name, wa, wb, ti])
                            #if wb >= 0.95:
                                #break
                
#write_combinations()


