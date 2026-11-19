# shots14 — B.5d line preview (Arthur pass 4 mockup, commit 9a83828)

Entry / Apex / Exit selection with the hover on each stance. Seed **20261114** (opening hand P/H/E ×2; 20261113 has only one EN, so Exit EN hover would be skipped). First corner is still Touge HP L. Entry camera, Entry select framing, and Exit camera are unchanged.

- `*_640.png` — native 640×480 3D + post (RGB555 dither, no HUD). The rear-view is in the post composite during Entry.
- `*_1280.png` — final 1280×960 composite (2× nearest + pixel-hard HUD).
- `compare_arthur_vs_gordon.png` — Arthur's `a_entry_*` / `b_apex_*` / `c_exit_*` frames (left) next to this build's 1280 composites (right), each pane 640×480 nearest.

Known leftover: from the Entry chase cam the follow-on Apex/Exit chevrons vanish over the crest (`_in_straight()` hides the hook mesh). Left as-is; same gap is in the mockup.
