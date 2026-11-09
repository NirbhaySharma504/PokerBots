# Pokerbots — Discard Hold'em

Submission: `bot/bot.py` (single file, stdlib + numpy only). Deadline 15 Nov 2026, 23:59 IST.

## Layout

| Path | What |
|---|---|
| `bot/bot.py` | the bot we upload |
| `bot/tools/` | evaluator tests, preflop table generator, gauntlet runner |
| `bot/opponents/` | archetype sparring bots (station, maniac, nit, tag, random, check/call) |
| `Starter_Kit/` | organisers' kit: engine, rules PDFs |

## Quick commands

    cd bot
    python3.11 tools/test_eval.py                      # evaluator vs official engine
    python3.11 tools/gauntlet.py --seeds 1 2 -j 3      # full timed matches vs all archetypes
    python3.11 tools/precompute.py 10000               # rebuild preflop table inside bot.py

## Plan

### What decides the tournament
- Match = win/loss on total chips over 400 (Stage 1) or 1000 (Stage 2) hands, duplicate deals.
  Luck mostly cancels, so a consistent edge wins. Margin only matters for tie-breaks (capped at C).
- Most of the field will be simple heuristic bots. The biggest edge comes from **exploiting**
  them (value-bet stations, call down maniacs, steal from nits), not from being unexploitable.
- A forfeit is -C and a guaranteed loss → crash safety and time safety come before everything.

### Architecture (v1, done)
1. **Vectorised numpy evaluator** for 5–7 cards (verified 0 mismatches vs `engine.py`).
2. **Preflop table**: equity of all 1,755 three-card classes vs a random hand, with both players
   discarding by a flop heuristic. Used as hand percentile for range modelling.
3. **Range-weighted Monte Carlo equity**: sample opponent hands, weight each by consistency with
   their actions (preflop percentile, postflop strength percentile, exposed discard), using
   thresholds taken from that opponent's own observed frequencies.
4. **Discard**: pick the keep with the highest equity vs the weighted range.
5. **Policy**: equity vs pot odds; value-bet sizing grows with equity; bluff frequency driven by
   the opponent's measured fold rate; thinner/bigger value vs stations.
6. **Time control**: measures its own cost per sample and sizes the sample count to a fraction of
   `time_left_ms / hands_left`. Everything wrapped so an exception falls back to check/fold.

### Next
- [ ] Stronger sparring partners: a copy of ourselves, plus an equity-based bot that isn't ours
- [ ] Parameter tuning (thresholds, sizing, bluff rates) via self-play / gauntlet sweeps
- [ ] Opponent model from showdowns (do they bluff? how strong are their big bets?)
- [ ] Better preflop strategy (position-aware, 3-bet/4-bet ranges, jam thresholds)
- [ ] Discard as signal: what the opponent's discard says about the rest of their hand
- [ ] Timing check under `taskset`/CPU throttling to simulate a slow 1 vCPU box
- [ ] Final checklist from the README before uploading
