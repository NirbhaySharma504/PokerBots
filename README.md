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

### Version history (each step A/B tested through the timed engine)
| Version | Change | Result vs previous |
|---|---|---|
| v1 | baseline: evaluator, range-weighted MC, opponent stats | beats all archetypes |
| v2 | bluff 2.5x more, learn bluff rate from showdowns | +540 +-101 (20/4) |
| v3 | bigger value bets, more semi-bluff raises | +203 +-64 (32/16) |
| v4 | read opponent bet sizes when narrowing their range | +900 +-73 (47/1) |
| v5 | bluff with value-sized bets (hide our own sizing) | +334 +-81 (37/11) |
| v6 | overbet calling stations with near-nuts, trap frequent bettors | station +1532, v5 +107 +-53 |
| v7 | Monte Carlo budget 0.15 -> 0.06 of the per-hand share (same strategy, less time) | v6 +87 +-77 |
| v8 | open ~98% of buttons (open_t 0.35, limp_t 0.30): 3-card equities are compressed, initiative > hand selection | +398 +-103 (36/12) and +303 +-103 (30/18), two machines |
| v9 | call less on flop/turn (call_margin 0.03 -> 0.10) + bluff more (bluff_scale 2.5 -> 4): fold marginal hands that realise badly, take those pots by betting instead | +386 +-100, +430 +-114, +457 +-115 vs v8; stage 2 +642 +-210 |
| v10 | call_margin 0.10 -> 0.22: flop/turn E vs a betting range runs high, so fold more | +772 +-96 vs v9; vs v9 copies bluffing 1.5x / 2.25x: +1135 / +1271 (0.10: -42 / +18); stage 2 +775 +-190; frozen v6 +1179 (47/1) vs +672 |
| v11 | extra flop/turn call margin out of position (cm_oop 0.12, so 0.34 OOP / 0.22 IP): OOP calls realise even less | vs v10: +373 / +483 (0.08), +448 (0.12), +553 (0.16) on A; +472 / +193 (0.10), +361 / +500 (0.16) on N; control cm_oop -0.10: -441; vs vbluff6 +1397 vs +1230, v6 +1387 vs +1185; gauntlet 72/72 |

v6 also beats v1 / v2 / v3 / v1_aggro by +700 to +800 each (no rock-paper-scissors).

Tried and rejected (no gain or worse): minimum-defense-frequency calling, fully fixed bet sizing,
looser calling margins, small preflop threshold moves (open_t 0.46/0.54 vs v3; the real effect
only showed up at 0.35, see v8), wider steals vs folders, learned
discard-style model, river-call self-calibration (shift river bluff-catch equity by how past
river calls did: tag +31, v7 -69, noise), overbetting the river with near-nuts vs non-stations
(v7 -243 +-89: size readers just fold). On top of v10 (all within the null-test noise): per-street
call margins, bluff_scale 3/5, river value threshold +-0.08, river bluff frequency / hand
strength. (Extra margin out of position looked like noise in one run, +112 +-79, but replicated
on 8 more runs and became v11.) On top of v11: OOP bluff frequency x0.5 (-151) / x1.6 (+38),
OOP value-bet threshold +0.06 (-98) / -0.06 (-146). On top of v8: opening 100% (-53 +-121), open size 0.5
(-96 +-134) or 1.0 (+135 +-110, maybe worth more seeds), lower BB 3-bet threshold vs wide openers
(pf_reraise_t 0.56 / 0.50: -67 / +157 vs a +187 mirror on the same seeds, noise).

### How much to trust an A/B number
Null tests (identical bots through `tools/ab.py`): +202 +-83, -171 +-64, -49 +-96 (same seeds as
the first), +8 +-55. The spread of those means is about 2x the reported SE, so a single run under
~3 SE is noise. Promote only what replicates on independent seed sets and on both machines (v8,
v9, v10 each did, at +300 to +900 per run).

### Pre-submission check (v10, current main)
- all wins vs random, check/call, station, maniac, nit, tag, eqbot, polar, lag_eq, sizer, jammer,
  minraiser (both machines, 0 notices); smallest margin nit ~+900
- 4 parallel matches pinned to efficiency cores: all finish, ~12s of the 30s bank per leg
  (engine "time used" is summed over both legs); stage 2 ~16s of 75s per leg
- lean / panic modes driven by engine-reported `time_left_ms`; start-up 0.19s, ~40MB
- protocol fuzz: unknown types/fields, malformed lines, notices -> ignored; exits on match_end
- evaluator: 0 mismatches vs engine; numpy 1.24 / 1.26 / 2.x give identical tables

### Open ideas
- [ ] a stronger, independent size-reading opponent to test v5/v6 sizing against
- [ ] more careful river play (thin value, bluff-catching vs polarized bettors)
- [ ] stage 2 (1000 hands): trust the opponent model sooner / weaker priors?
