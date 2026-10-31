# Ladder testing capacity and the screen band (2026-10-30, after b18)

## Quota

- 50 groups (250 games) per rolling hour. `resetsAt` is one hour after the first group of a window (04:13:44 → 05:13:44, 06:12:31 → 07:12:31).
- The intel rule (use at most half of what's left) allows 25 groups from a fresh window: 2 full bands (24 groups), or 4 screen bands (6 groups each) per hour.
- Quota is not the bottleneck. The real costs per candidate are:
  1. **It must be live:** unranked groups play whatever version is live, so every candidate plays ranked games on the ladder for its whole live time.
  2. **Platform build:** 4-9 minutes from submit to live.
  3. **Bands run in about 5 minutes now:** b18base's 60 games took 4 s each, all in parallel.
  - So a candidate needs about 15-20 minutes live for a screen or full band, plus a revert if it fails (another 4-9 minutes).
- **Baseline drift is small.** v40 at 06:13Z vs 09:57Z: 55 of 60 games identical. One v40 baseline per ~4 hours is enough.

## Why a smaller band works

Over 6 runs of band_v2 (b14+b15base, b15, b16, b17, b18base, b18; v38, v39, v40, v41, v43), **38 of 60 games never changed result**: 19 always won and 19 always lost. They carry no signal for a candidate that makes a small change. 22 games swung at least once; 13 more kept their result but came within 250 gems at some point.

## screen_v1_plan.json: 6 groups, 30 games

- Opponents: lETHal, JOHN_BANEGA_DON, noobers, CompetitiveBasmaga, Anime girls, Tozo's Disciples. These are where the swing games concentrate.
- Each group holds its opponent's swing games first, then close ones: 17 of the 22 swing games and 8 close games. Each game keeps its band_v2 side.
- A group must be exactly 5 matches, so 5 filler games are included.

Signal it would have caught, in-sample (the screen was chosen from these same runs, so this flatters it):

| change | flips, full band (to a win / to a loss) | flips, screen | gems per game, full band | gems per game, screen |
|---|---|---|---|---|
| v38 → v39 | 3 (2/1) | 2 (1/1) | +9.2 | +8.9 |
| v39 → v40 | 12 (6/6) | 10 (4/6) | +30.4 | +3.8 |
| v40 → v41 | 7 (2/5) | 6 (2/4) | -37.7 | -58.7 |
| v40 → v43 | 11 (4/7) | 10 (3/7) | -17.9 | -54.5 |

- 28 of 33 flips are inside the screen, and the verdict would have been the same in all four cases.
- **Blind spot:** a candidate can open a new swing in a "dead" game. The v39 freeze fix flipped 02harvest vs Sloppy Joe, which is outside the screen.
- **Proposal:** screen first (6 groups). Promote a candidate that is up on flips and gems to the full band (12 groups) before deciding to keep it. Revert at once if the screen is clearly down. Re-baseline the screen on the live version every ~4 hours, or after any opponent shows a changed game.

## Where the pipeline runs (from 2026-10-31 01:28Z)

The session scratch directory was retired, so the working copies moved to ~/ws/intel (outside the repo):
- bin/cambc4: the cambc 4.0.0 binary.
- ws4: the cambc 4.0.0 workspace. bots/ holds every candidate build; the .cambc build caches were removed, so the next run rebuilds.
- an/analysis: analysis/sprint1 plus tools/extract_v2 and the v2_0_0 wasm.
- runs/: fetched and extracted screens.

Usage: `RESUME_V=<live> SCR=~/ws/intel/runs WS4=~/ws/intel/ws4 CAMBC4=~/ws/intel/bin/cambc4 AN=~/ws/intel/an/analysis genome/intel/tools/screen_cycle.sh ...`
