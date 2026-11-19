> **v3 (Austin 2026-11-19):** the BRZ, MX-5 and S2000 use the live Touge tune: POW/HAN/EN = 1350/750/900 points (45/25/30%).
> The GR Corolla and WRX STI use the live Wangan tune: 750/750/1500 (25/25/50%). Both are DISTRICT_TUNE x 3,000.
> Totals are equal, but whether every matchup stays within 1.07 is unverified until Austin gives a go to sim. v2 below is superseded.

> **v2 (2026-11-19, after Austin's correction via Gordon):** each car has 3,000 points, with each stat at 25-50% (750-1,500).
> Placeholder shapes (POW/HAN/EN points): BRZ 900/1250/850, GR Corolla 1000/950/1050, MX-5 800/1350/850,
> S2000 1200/1000/800, WRX STI 1150/850/1000. Totals are equal, but whether every matchup stays within 1.07 is
> UNVERIFIED until Austin gives a go to sim. The car identities (which car leans which way) are a placeholder and need
> Desmond and Arthur's input. v1 below is superseded.

# touge-race-parity (Barry DRAFT, 2026-11-19, unapproved)

Car stat blocks for the 10-turn Touge test race on touge-race (no mods, no retune). Austin's answers came through Gordon:
the car-select screen lists all the cars in the repo, and parity means any pair of cars within the 1.07 cap.

## Draft
- Every car gets the live stock car evenly split: POW / HAN / EN = 100 / 100 / 100 (total 300 power units = the 3,000-point
  stock car at L0). Every pairing is r = 1.00, inside the 1.07 cap.
- The AI QTE ratio is 1.0 (the sim's pure stat-parity setting in models.py).
- Values are in `blocks.json`. No sim has been run; these come straight from the live stock car constants in equations.py.

## Open for Austin
1. The repo has 5 car folders in assets/cars/ (brz, gr_corolla, mx5, s2000, wrx_sti); the request said 4. Which one drops?
2. Should cars have different stat shapes (still within 1.07)? Doing that means choosing a shape for each car, which is a
   story and art call, and checking the matchups would need a sim run.
