# Toot and Tumble

MVP Construct 3 project for a one-level 2D city platformer where a rotating trombone is the only traversal mechanic.

## Open in Construct 3

- Folder project: open `Toot-and-Tumble game/` as a Construct 3 project folder.
- Single-file project: open `Toot-and-Tumble.c3p`.

## Run in a Browser

- Open `index.html` for a standalone browser playtest build.
- On GitHub Pages, serve the repository root and the game will load from `index.html`.

## Controls

- Space / mouse / touch press: freeze the trombone angle.
- Release: launch opposite the horn direction.
- R / tap the fail or win screen: restart.

There is no normal jump button. The trombone is the jump.

## MVP Contents

- One scrolling city level around 60 seconds at the tuned camera speed.
- Player body uses Construct 3 Platform behavior with default controls disabled and jump strength set to 0.
- Cars, bus, scaffolds, building ledges, pits, construction hazard, dog, pedestrian, finish flag, HUD breath bar, and slide power meter.
- `ES_Game` contains the global variables and event groups requested for the MVP; the main implementation is installed from a C3 script action on layout start to avoid fragile hand-authored event-block IDs.
- `index.html` mirrors the MVP as a browser playtest page so the repo can run without opening Construct 3 first.
- The current tuning uses a slow stage scroll, a partial trombone sweep through useful launch angles, stronger brass-powered launches, generated brass sounds, and tap restart for phones.
