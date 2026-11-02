# World notes: overworld and race tracks (art planning)

> Notes only, from Austin (2026-11-02). Nothing here is built yet. Owner: Arthur (Art Director).

## Two separate spaces
- **Overworld:** the free-drive layer between races. Its road layouts are based on **OpenStreetMap (OSM)** data, so areas are *inspired by* real places.
- **Races:** turn-based, on **pregenerated tracks**, in the spirit of Racing Lagoon. They don't take place in the overworld.

## Overworld (OSM-based)
- Take **only the road layout** from OSM: street pattern, curves, junctions, widths, lane counts and one-way tags.
- **No real building geometry.** Each area is dressed with our own stylized PSX/PS2 pieces (see `art_direction.md` and the district asset packs).
- Remix freely: trim to a playable area, merge fussy side streets, and change the layout where it plays better.
- **Canon fit** (`story/canon.md` decision 6): the city is a fictional mix, neither Japan nor the US, with no real places. So stitch and rename layouts from several sources so that no area reads as a copy of a real one.
- Optional elevation from a height map (hills, Touge).
- **Licence:** OSM data is ODbL, so the game credits "© OpenStreetMap contributors".
- **Camera (reference: Racing Lagoon free roam, [YouTube](https://youtu.be/AH90Y9Z1Tcs?t=990) around 16:30):** a high overhead *perspective* camera, roughly 50–65° down. It isn't a chase cam and isn't true isometric, because buildings lean away from the frame centre. The car is small on screen. Austin notes the camera has rotation, so treat it as rotatable. (`godot-build-guide.md` says "isometric"; this reference supersedes that for art purposes, and the exact angle and rotation rules are still for design to set.)
- **Art implications of that camera:**
  - Rooftops, road surfaces, markings and water carry the look. Building fronts matter less but still need to read from any direction, since the camera rotates, so there are no one-sided cut-outs.
  - The overworld car can be a lighter LOD than the 2,000-triangle race car, because it's small on screen.
  - Readable from above: lane markings, intersections, a minimap-style road hierarchy, and lit rooftops and signs for the night mood.

## Race tracks (pregenerated, turn-based)
- Per `godot-build-guide.md` §13–14, there's no continuous track. Each turn loads one **straight + corner segment** (`TrackData.gd`, 10 turns per circuit), plays it as a cinematic, then unloads it.
- Art implication: build a **reusable corner-segment kit per district** (Touge, Wangan, Street), not whole circuits.

## Inputs we can work from
- **Hand-drawn map:** it can be traced the same way as car blueprints. We need one known distance for scale, plus lane and one-way info.
- **OSM extract:** preferred for the overworld. It comes already scaled and tagged.
