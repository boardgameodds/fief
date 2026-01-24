const { useState } = React;

const SIMULATIONS = 100000;

const MAX_MEN_AT_ARMS = 13;
const MAX_KNIGHTS = 8;

const DamageStrategy = {
  MEN_AT_ARMS_FIRST: 0,
  KNIGHTS_FIRST: 1
};

const DefensiveStructure = {
  NONE: 0,
  STRONGHOLD: 1,
  FORTIFIED_CITY: 2
};

const ArmyLeader = {
  NONE_OR_LADY: 0,
  LORD_OR_TITLED_LADY: 1,
  DARC: 2
};

class Army {
  constructor(menAtArms, knights, structure = DefensiveStructure.NONE, leader = ArmyLeader.NONE_OR_LADY) {
    this.menAtArms = menAtArms;
    this.knights = knights;
    this.structure = structure;
    this.leader = leader;
  }

  copy() {
    return new Army(this.menAtArms, this.knights, this.structure, this.leader);
  }

  isDefeated() {
    return (this.knights + this.menAtArms) <= 0;
  }

  computeDamageMaaFirst(damage) {
    let d = damage;
    let k = this.knights;
    let m = this.menAtArms;
    
    while (d >= 1 && m > 0) {
      if (d >= 3 && m <= 2 && k > 0) {
        k -= 1;
        d -= 3;
        continue;
      }
      m -= 1;
      d -= 1;
    }
    while (d >= 3 && k > 0) {
      k -= 1;
      d -= 3;
    }
    return [d, k, m];
  }

  computeDamageKnightsFirst(damage) {
    let d = damage;
    let k = this.knights;
    let m = this.menAtArms;
    
    while (d >= 3 && k > 0) {
      k -= 1;
      d -= 3;
    }
    while (d >= 1 && m > 0) {
      m -= 1;
      d -= 1;
    }
    return [d, k, m];
  }

  applyDamage(damage, strategy = DamageStrategy.MEN_AT_ARMS_FIRST) {
    const [dk, kk, mk] = this.computeDamageKnightsFirst(damage);
    const [dm, km, mm] = this.computeDamageMaaFirst(damage);
    
    if (strategy === DamageStrategy.KNIGHTS_FIRST) {
      this.knights = kk;
      this.menAtArms = mk;
      return dk;
    } else {
      this.knights = km;
      this.menAtArms = mm;
      return dm;
    }
  }

  armyPoints() {
    return (this.knights * 3) + this.menAtArms;
  }

  strengthPoints() {
    let bonus = 0;
    if (this.leader === ArmyLeader.LORD_OR_TITLED_LADY || this.leader === ArmyLeader.DARC) {
      bonus = 1;
    }
    return this.armyPoints() + bonus;
  }

  dice(penalty = 0) {
    if (this.armyPoints() === 0) return 0;
    
    const s = this.strengthPoints();
    let d = 0;
    
    if (s >= 1 && s <= 6) {
      d = 1;
    } else if (s <= 12) {
      d = 2;
    } else if (s >= 13) {
      d = 3;
    }
    
    d += penalty;
    if (this.leader === ArmyLeader.DARC) {
      d += 1;
    }
    if (d < 0) d = 0;
    
    return d;
  }

  attackerPenalty() {
    if (this.structure === DefensiveStructure.FORTIFIED_CITY) return -2;
    if (this.structure === DefensiveStructure.STRONGHOLD) return -1;
    return 0;
  }
}

class BattleDiceSet {
  constructor(dice = 1) {
    this.dice = dice;
  }

  roll(diceBonus = 0) {
    let total = 0;
    for (let i = 0; i < this.dice; i++) {
      total += Math.floor(Math.random() * 3) + 1 + diceBonus;
    }
    return total;
  }
}

const DICE_SETS = {
  0: new BattleDiceSet(0),
  1: new BattleDiceSet(1),
  2: new BattleDiceSet(2),
  3: new BattleDiceSet(3),
  4: new BattleDiceSet(4)
};

function battle(armyA, armyB, iterations = 1000) {
  const penaltyA = armyB.attackerPenalty();
  const penaltyB = armyA.attackerPenalty();
  
  let winA = 0;
  let ties = 0;
  let winB = 0;
  
  for (let i = 0; i < iterations; i++) {
    const ai = armyA.copy();
    const bi = armyB.copy();
    
    while (true) {
      const dcA = ai.dice(penaltyA);
      const dcB = bi.dice(penaltyB);
      
      if (dcA === 0 || dcB === 0) {
        if (dcA === 0 && dcB === 0) {
          ties += 1;
        } else if (dcA === 0) {
          winB += 1;
        } else if (dcB === 0) {
          winA += 1;
        }
        break;
      }
      
      const dA = DICE_SETS[dcA].roll();
      const dB = DICE_SETS[dcB].roll();
      ai.applyDamage(dB, DamageStrategy.MEN_AT_ARMS_FIRST);
      bi.applyDamage(dA, DamageStrategy.MEN_AT_ARMS_FIRST);
      
      if (ai.isDefeated() || bi.isDefeated()) {
        if (ai.isDefeated() && bi.isDefeated()) {
          ties += 1;
        } else if (ai.isDefeated()) {
          winB += 1;
        } else if (bi.isDefeated()) {
          winA += 1;
        }
        break;
      }
    }
  }
  
  return {
    winA: winA / iterations,
    ties: ties / iterations,
    winB: winB / iterations
  };
}

// Lucide icons as SVG components
const Swords = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M14.5 17.5 3 6V3h3l11.5 11.5"/>
    <path d="M13 19 9 15"/>
    <path d="m16 16 5 5"/>
    <path d="m19 14-3 3"/>
    <path d="M9.5 6.5 21 18V21h-3L6.5 9.5"/>
    <path d="M5 10 9 14"/>
    <path d="m2 2 5 5"/>
    <path d="M8 8 5 11"/>
  </svg>
);

const Shield = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
  </svg>
);

const Users = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
    <circle cx="9" cy="7" r="4"/>
    <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
    <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
  </svg>
);

const Crown = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M2 18h20"/>
    <path d="M12 2v16"/>
    <path d="m2 6 10 6 10-6"/>
    <path d="M12 2 2 18h20L12 2z"/>
  </svg>
);

function BattleSimulator() {
  const [armyA, setArmyA] = useState({
    menAtArms: 5,
    knights: 3,
    structure: DefensiveStructure.NONE,
    leader: ArmyLeader.NONE_OR_LADY
  });
  
  const [armyB, setArmyB] = useState({
    menAtArms: 4,
    knights: 2,
    structure: DefensiveStructure.STRONGHOLD,
    leader: ArmyLeader.NONE_OR_LADY
  });
  
  const [results, setResults] = useState(null);
  const [simulating, setSimulating] = useState(false);

  const runSimulation = () => {
    setSimulating(true);
    setTimeout(() => {
      const a = new Army(armyA.menAtArms, armyA.knights, armyA.structure, armyA.leader);
      const b = new Army(armyB.menAtArms, armyB.knights, armyB.structure, armyB.leader);
      const result = battle(a, b, SIMULATIONS);
      setResults(result);
      setSimulating(false);
    }, 10);
  };

  const ArmyConfig = ({ army, setArmy, title, color }) => {
    const a = new Army(army.menAtArms, army.knights, army.structure, army.leader);
    
    return React.createElement('div', { className: `p-6 rounded-lg border-2 ${color}` },
      React.createElement('h3', { className: 'text-xl font-bold mb-4 flex items-center gap-2' },
        React.createElement(Swords),
        title
      ),
      React.createElement('div', { className: 'space-y-4' },
        React.createElement('div', null,
          React.createElement('label', { className: 'block text-sm font-medium mb-1' },
            React.createElement(Users),
            ' Men-at-Arms: ', army.menAtArms
          ),
          React.createElement('input', {
            type: 'range',
            min: 0,
            max: MAX_MEN_AT_ARMS,
            value: army.menAtArms,
            onChange: (e) => setArmy({...army, menAtArms: parseInt(e.target.value)}),
            className: 'w-full'
          })
        ),
        React.createElement('div', null,
          React.createElement('label', { className: 'block text-sm font-medium mb-1' },
            React.createElement(Shield),
            ' Knights: ', army.knights
          ),
          React.createElement('input', {
            type: 'range',
            min: 0,
            max: MAX_KNIGHTS,
            value: army.knights,
            onChange: (e) => setArmy({...army, knights: parseInt(e.target.value)}),
            className: 'w-full'
          })
        ),
        React.createElement('div', null,
          React.createElement('label', { className: 'block text-sm font-medium mb-1' },
            React.createElement(Crown),
            ' Leader'
          ),
          React.createElement('select', {
            value: army.leader,
            onChange: (e) => setArmy({...army, leader: parseInt(e.target.value)}),
            className: 'w-full p-2 border rounded text-black'
          },
            React.createElement('option', { value: ArmyLeader.NONE_OR_LADY }, 'None/Lady'),
            React.createElement('option', { value: ArmyLeader.LORD_OR_TITLED_LADY }, 'Lord/Titled Lady'),
            React.createElement('option', { value: ArmyLeader.DARC }, "D'Arc")
          )
        ),
        React.createElement('div', null,
          React.createElement('label', { className: 'block text-sm font-medium mb-1' }, 'Defensive Structure'),
          React.createElement('select', {
            value: army.structure,
            onChange: (e) => setArmy({...army, structure: parseInt(e.target.value)}),
            className: 'w-full p-2 border rounded text-black'
          },
            React.createElement('option', { value: DefensiveStructure.NONE }, 'None'),
            React.createElement('option', { value: DefensiveStructure.STRONGHOLD }, 'Stronghold'),
            React.createElement('option', { value: DefensiveStructure.FORTIFIED_CITY }, 'Fortified City')
          )
        ),
        React.createElement('div', { className: 'pt-3 border-t space-y-1 text-sm' },
          React.createElement('div', null, 'Army Points: ', React.createElement('span', { className: 'font-bold' }, a.armyPoints())),
          React.createElement('div', null, 'Strength: ', React.createElement('span', { className: 'font-bold' }, a.strengthPoints())),
          React.createElement('div', null, 'Base Dice: ', React.createElement('span', { className: 'font-bold' }, a.dice()))
        )
      )
    );
  };

  return React.createElement('div', { className: 'min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 text-white p-8' },
    React.createElement('div', { className: 'max-w-6xl mx-auto' },
      React.createElement('h1', { className: 'text-4xl font-bold text-center mb-8' }, 'Medieval Battle Simulator'),
      React.createElement('div', { className: 'grid md:grid-cols-2 gap-6 mb-8' },
        React.createElement(ArmyConfig, {
          army: armyA,
          setArmy: setArmyA,
          title: 'Army A (Attacker)',
          color: 'border-blue-500 bg-blue-900/20'
        }),
        React.createElement(ArmyConfig, {
          army: armyB,
          setArmy: setArmyB,
          title: 'Army B (Defender)',
          color: 'border-red-500 bg-red-900/20'
        })
      ),
      React.createElement('div', { className: 'text-center mb-8' },
        React.createElement('button', {
          onClick: runSimulation,
          disabled: simulating,
          className: 'bg-amber-600 hover:bg-amber-700 disabled:bg-gray-600 px-8 py-3 rounded-lg font-bold text-lg transition-colors'
        }, simulating ? 'Simulating...' : `Run Battle Simulation (${SIMULATIONS} iterations)`)
      ),
      results && React.createElement('div', { className: 'bg-slate-800 p-6 rounded-lg border-2 border-amber-500' },
        React.createElement('h2', { className: 'text-2xl font-bold mb-4 text-center' }, 'Battle Results'),
        React.createElement('div', { className: 'grid grid-cols-3 gap-4 text-center' },
          React.createElement('div', { className: 'bg-blue-900/30 p-4 rounded' },
            React.createElement('div', { className: 'text-3xl font-bold text-blue-400' }, (results.winA * 100).toFixed(1) + '%'),
            React.createElement('div', { className: 'text-sm mt-1' }, 'Army A Wins')
          ),
          React.createElement('div', { className: 'bg-gray-700/30 p-4 rounded' },
            React.createElement('div', { className: 'text-3xl font-bold text-gray-300' }, (results.ties * 100).toFixed(1) + '%'),
            React.createElement('div', { className: 'text-sm mt-1' }, 'Ties')
          ),
          React.createElement('div', { className: 'bg-red-900/30 p-4 rounded' },
            React.createElement('div', { className: 'text-3xl font-bold text-red-400' }, (results.winB * 100).toFixed(1) + '%'),
            React.createElement('div', { className: 'text-sm mt-1' }, 'Army B Wins')
          )
        )
      )
    )
  );
}

ReactDOM.render(React.createElement(BattleSimulator), document.getElementById('root'));
