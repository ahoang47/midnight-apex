# planner-v1: campaign planner Page (draft, Barry 2026-11-14)

Interactive Page: https://cursor.com/canvas/store-4599c40d-e855-4fb8-bc90-b1743052ccec/786f1da3-54a2-42a2-b4c6-331eb5da9579
Rules: live sim only (sim/velocity_shift on proto-build: mods-v1, skill-points-v1, story-xp-v1, hardest-track boss tuning, and the
leftover-XP carry-over with catch-up XP, live since 2026-11-14 as xp-carry-v1 fix C). Betting is not included. The page itself is a draft tool.

Regenerate and re-verify (run from sim/):
    python3 ../unapproved/barry/planner-v1/gen_constants.py            # -> constants.ts / constants.json
    PYTHONPATH=.:../unapproved/barry/mods-v1:../unapproved/barry/skill-points-v1 \
      python3 ../unapproved/barry/planner-v1/py_reference.py            # -> py_reference.json (Python walks)
    node ../unapproved/barry/planner-v1/verify.mjs [page_source.tsx]    # JS port vs Python; optional arg checks a saved Page source
Then paste constants.ts (without `export`) and engine.ts (between ENGINE-START / ENGINE-END) into the Page. page_source.tsx is the
published Page source (its data and engine blocks are byte-identical to constants.ts / engine.ts).

Files: gen_constants.py, constants.ts/.json, engine.ts (JS port), py_reference.py/.json, verify.mjs, verify_log.txt, js_walks.json, page_source.tsx.

Target helper (2026-11-14 follow-up): Plan.target sets the "grind to my target" policy (50-95 %); it now gates every race, bosses and
finale included, with the fewest grinds (the sim's mixed / hard walks are unchanged and still match Python). Row.natural = the win
chance on arrival without that race's grinds. `node swings.mjs [target]` lists the largest race-to-race swings per profile under that
policy with auto mods (swings_<target>.json / swings_50.txt).
