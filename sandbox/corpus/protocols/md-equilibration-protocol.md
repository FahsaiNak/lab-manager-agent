---
type: protocol
status: SYNTHETIC DEMO DATA — fictional, not derived from any real lab protocol
---

# Standard MD Equilibration Protocol (demo fixture)

## Purpose
Reference protocol for equilibrating a solvated protein system prior to production MD,
used here only as fixture content for the Knowledge Curator Q&A demo.

## Steps
1. Energy minimization: steepest descent, 5000 steps, until max force < 1000 kJ/mol/nm.
2. NVT equilibration: 100 ps at 310 K, position restraints on heavy atoms (force constant 1000 kJ/mol/nm^2).
3. NPT equilibration: 1 ns at 310 K / 1 bar, restraints released gradually over 4 stages.
4. Production run starts only after RMSD of backbone atoms plateaus (<0.2 nm drift over last 200 ps).

## Common Pitfalls
- Releasing restraints too quickly causes solvent box instability.
- Skipping the NVT stage before NPT often produces pressure-coupling artifacts.
