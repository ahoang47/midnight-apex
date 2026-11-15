# skill-points-v1: decision (Austin 2026-11-14)

Austin "sounds good." on whole skill points at 10× with a hard retune limit, then "Great. Commit and push." on the package below.

- **Whole points at 10× resolution (scheme S3):** skill_points(L) = round(10 × SP(L)), 2,400 at L0, 19 to 48 per level.
- **Band:** each of POW, HAN and EN stays within 25–50% of the points spent. This is enforced.
- **Locking:** points lock once spent. Newly earned points are free to place within the band.
- **Retune budget:** B = **20%** of spent points may move at each district change (R1→R2, R2→R3, and before P1, M11, M21, M31). There is no other retuning and no paid respec for skill points.

Why 20%: it is the smallest budget tested that keeps every target. 15% passes the campaign, but the 60/60 win rate in the F3 billed finale drops to 28–29%, below the 30% floor. 10% or less breaks R2. See RETUNE.md.

The live implementation is sim/velocity_shift/equations.py (constants and checks) plus progression.py (build walk and off-tune delta), with off-tune data in sim/config/winrate_offtune_v1.json (= retune_sweep_rt1.json). verify_live.txt shows that the live code reproduces the draft B = 20% numbers.
