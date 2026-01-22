# fief
Odds calculator for the Fief boardgame

---

## Overview

This repo implements a **probabilistic battle simulator**.
It models armies composed of *men-at-arms* and *knights*, applies combat rules using dice rolls, resolves battles iteratively, and caches outcomes to estimate win/tie/loss probabilities efficiently.

The system supports:

* Damage strategies (who dies first)
* Leaders and defensive structures
* Dice-based combat resolution
* Hashable battle states for memoization
* Monte Carlo simulation with caching

---

## Constants and Bit Packing

### Unit Limits

```python
MAX_MEN_AT_ARMS = 13
MAX_KNIGHTS = 8
```

These define the **maximum allowed units** per army. They are enforced during hashing to ensure predictable bit sizes.

### Binary Sizes

```python
BIN_SIZE_MEN_AT_ARMS
BIN_SIZE_KNIGHTS
BIN_SIZE_DAMAGE_STRATEGY
BIN_SIZE_ARMY_LEADER
BIN_SIZE_DEFENSIVE_STRUCTURE
```

These constants define how many bits are needed to store each field when packing objects into integers.

**Purpose:**
They enable **compact, deterministic hashing** of `Army` and `Battle` objects so they can be used as dictionary keys.

---

## Enumerations

### `DamageStrategy`

Defines how damage is allocated:

* `MEN_AT_ARMS_FIRST`: cheaper units die first
* `KNIGHTS_FIRST`: expensive units die first

Used to model different tactical doctrines.

---

### `DefensiveStructure`

Represents fortifications of the defending army:

* `NONE`
* `STRONGHOLD` (–1 attacker dice)
* `FORTIFIED_CITY` (–2 attacker dice)

---

### `ArmyLeader`

Represents command quality:

* `NONE_OR_LADY`
* `LORD_OR_TITLED_LADY`
* `DARC` (special leader with extra dice bonus)

---

## `Army` Class

Represents a single army state.

### Attributes

* `men_at_arms`: Light infantry (1 HP each)
* `knights`: Heavy cavalry (3 HP each)
* `structure`: DefensiveStructure
* `leader`: ArmyLeader

---

### Hashing

```python
Army.hash()
```

Encodes the army into a compact integer using bit shifts.

**Why:**

* Enables use as dictionary keys
* Guarantees uniqueness within defined limits
* Faster than tuple hashing

`__hash__` delegates to this method.

---

### Combat State Methods

#### `is_defeated()`

Returns `True` if the army has no remaining units.

---

#### Damage Computation

Damage is measured in **points**:

* Men-at-arms absorb **1**
* Knights absorb **3**

##### `compute_damage_maa_first(damage)`

Applies damage prioritizing men-at-arms unless doing so would waste damage.

##### `compute_damage_knights_first(damage)`

Applies damage prioritizing knights.

Both return:

```python
(remaining_damage, remaining_knights, remaining_men)
```

---

#### `apply_damage(damage, strategy)`

* Applies damage using the chosen strategy
* Verifies both strategies consume the same total damage
* Updates army state
* Returns leftover damage

---

### Scoring

#### `army_points()`

Raw strength:

```text
knights × 3 + men_at_arms
```

#### `strength_points()`

Army points + leader bonus:

* +1 for `LORD_OR_TITLED_LADY`
* +1 for `DARC`

---

### Dice Mechanics

#### `dice(penalty=0)`

Returns number of dice rolled:

* 1–6 strength → 1 die
* 7–12 → 2 dice
* 13+ → 3 dice
* `DARC` grants +1 die
* Penalties may reduce dice to zero

---

### Attacker Penalty

#### `attacker_penalty()`

Returns dice penalties based on defender’s structure:

* Fortified city: –2
* Stronghold: –1
* None: 0

---

## `BattleDiceSet`

Encapsulates dice rolling behavior.

* Each die rolls **1–3**
* Optional flat bonus per die

Used via the `DICE_SETS` lookup table.

---

## `Battle` Class

Represents a full battle state.

### Attributes

* `a`, `b`: Armies
* `a_strategy`, `b_strategy`: DamageStrategy
* `cavalcade`: Grants defender bonus damage

---

### Hashing

Encodes the entire battle state (armies, strategies, flags) into a single integer.

Used as a cache key.

---

### Battle Resolution

#### `battle_status()`

Checks if the battle is already resolved *without rolling dice*:

* Zero dice on either side
* One or both armies defeated

Returns:

```text
(status, description, indicator)
```

Indicator:

* `1` → A wins
* `0` → Tie
* `-1` → B wins

---

#### `battle_iterator()`

Generator that:

* Rolls dice
* Applies damage
* Yields intermediate states
* Stops on resolution

Used for recursive simulation.

---

#### `resolve()`

Runs the battle iterator to completion and returns the final result.

---

## `BattleCache`

Caches Monte Carlo battle outcomes.

### Stored Data

Each battle maps to:

```text
(wins, ties, losses, samples)
```

---

### `probability(battle)`

Returns:

```python
(win_rate, loss_rate, tie_rate, samples)
```

---

### `resolve(battle)`

* Runs simulations recursively
* Stops once enough samples are collected
* Uses RNG sampling when sufficiently populated

**Purpose:**
Dramatically reduces recomputation for identical battles.

---

### Bulk Operations

* `populate()`: brute-force exploration
* `complete()`: fills under-sampled battles
* `serialize()`: exports results to CSV

---

## Standalone Battle Simulation

### `battle(a, b)`

Runs **1000 Monte Carlo battles** without caching.

Returns:

```python
(a_win_rate, tie_rate, b_win_rate)
```

Used for CSV generation and sanity checks.

---

## CSV Output Utilities

* `write_csv()`
* `write_combinations()`
* `evaluate_b_combinations()`

These functions:

* Enumerate army matchups
* Skip irrational attacks
* Stop early when victory becomes overwhelming
* Export odds tables

---


