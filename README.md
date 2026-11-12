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
| v12 | small-ball: bet whenever checked to (bluff_scale 30), bluffs 1/3 pot (bluff_size 0.33), value 0.45 pot + flat slope (bet_slope 0.5): one small size, so v11-style folders over-fold | vs v11: +511, +608 / +544 (value 0.30 / 0.45), +585 (48 seeds each, all fresh); stage 2 +1118 (15/1); vs a nasty v11 copy (small-ball + wide 3bets + bluff-raises) -16 vs -313 for v11; tag +1629 vs +1897; gauntlet 36/36 |
| v13 | always trap (trap_p 0.4 -> 1.0): vs frequent bettors, check every E > 0.8 on flop/turn and raise their bet. now that we range-bet, our checks were all weak; this protects them | vs v12: +170 / +130 (0.6), +253, +190 (1.0); stage 2 +337 (12/4); pool vs barrel / bigbet / v6 / v11 / tag +448 / +529 / +391 / +253 / +135 over v12 on the same seeds, nasty -122 (noise); gauntlet 36/36 |
| v14 | river betting from a solved toy game (CFR+, 20 buckets, 1/3 and 3/4 pot): OOP first action and IP checked-to only; facing bets stays exploitative | vs v13: +116 / +142 / +81 (48 seeds each, fresh), N: +218 / +78; stage 2 (1000 hands) +191 ± 170; pool vs v13 on the same seeds: barrel -37, nasty +161, bigbet -256, tag +281, v6 +174; using the table for facing bets too was worse (barrel -326); gauntlet 36/36 |
| v15 | shrink the flop/turn call margin vs tiny bets: margin x min(1, bet/pot / 0.3), so 1/3 pot and up is unchanged | vs tiny13 (v13 with ~1/8 pot sizes), paired with v14: -28 -> +144 (7401-7436), +141 -> +376 (7501-7548); vs v14 +46 / -20 (flat, as expected since only tiny bets change); 0.2 did nothing (-24); gauntlet 36/36, fuzz ok |
| v16 | tiny-bet margin shrink squared: margin x min(1, r/0.3)^2 (a 1/8 pot bet now gets ~0.19 of the margin instead of ~0.42) | vs tiny13 paired with v15: +241 -> +561 (8101-8136), +131 -> +330 (8201-8248); vs v15 +100 / +55; pool 8301-8328 bigbet +141, minbettor +121, smallball 0, nasty -78, barrel -150 (barrel never bets < 0.3 pot, so noise); pow 3: tiny13 +673 but v15 -68 |

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
OOP value-bet threshold +0.06 (-98) / -0.06 (-146). BB preflop call margin 0.10 (-16, +7) / 0.0 (+16, -115). On top of v8: opening 100% (-53 +-121), open size 0.5
(-96 +-134) or 1.0 (+135 +-110, maybe worth more seeds), lower BB 3-bet threshold vs wide openers
(pf_reraise_t 0.56 / 0.50: -67 / +157 vs a +187 mirror on the same seeds, noise).
On top of v13: call_margin 0.28 (+129 fresh, nasty -865), multiplicative realization
(call when R*E >= odds; R .55/.42: +138 vs v13 but nasty -684, bigbet -398) and a hybrid
min(flat, R) margin (-56 / -102 vs v13); river bluff/value thresholds and sizes; tiny-bet probes
(v13 beats minbettor +3202, ties tiny13).
Also on v13: off-grid bet sizes 0.6x/1.4x on 30% of bets (+14 vs v13, pool unchanged: a free
hedge vs table-based bots but nothing measurable vs ours, so left out); mixing close discards
(-64 / -178 vs v13); switching whole styles mid-match by which is winning (v13 vs a "call more"
style in 20-hand blocks): maniac +2.3k, tag +0.2k but nasty -0.5k and v13 -363 (7/21), since
exploring costs too much against strong bots in a 200-hand leg.
On top of v14-v16 (all noise or worse, so not adopted): river table with a 1.5 pot overbet
(+106 / +27 vs v14, pool ~+60), the same one-street table on the turn (-283, the turn wants the
range bet), 40 buckets instead of 20 (+58), call margin scaled by SPR after calling (-151 to
-294: their big bets are just strong), opponent-model decay vs a style switcher (v15 already
+2722 vs it; decay +18 / -4 vs v15), tiny-bet cutoff 0.4 / 0.5 (+19 / +110 then +25; the 1/3 pot
lead stays above it), bigger value bets bet_base 0.55 / 0.62 (-165 / -128), wider BB 3-bets
pf_reraise_t 0.50 / 0.45 (+103 then +21 / +2). Two random-copy hunts (28 v16 copies with 4-6
random knobs) found nothing that beats v16: the closest, s15, was +3 as hero on 48 seeds.
v16 vs every bot in opponents/ at real stage 2 (1000 hands): all 12/0 except our own copies
(tiny13 9/3 before v16, v13 7/5). River calls after we check / vs a check-raise win only 8-19% at showdown vs our
copies, but a river margin there (0.2 / 0.3) is +155 / +115 / +67 and +126 vs v16 while costing
~-100 / -65 on average vs nasty/barrel/bigbet/xr16/tag/maniac (tag -270, maniac -222): copies
rarely bluff there, real bluffers do. Not adopted. Scaling it by the learned bluff_rate (full below 10%, zero above 20%): +35 vs v16, maniac -413, tag -163; the signal is too slow within a leg. Flop/turn margin when facing a raise after our own bet: x0.5 / x0 lose -1000 / -1900 vs v16 and the raisers (their raises are strong); x1.3 / x1.6 win vs v16 (+193 / +304) but lose vs raiser16 (-181 / -605) and xr16: self-play trap both ways, so x1 stays.

### Final check (v16, real stage 2: 1000 hands, 2 x 500, seeds 11701-11712)
v16 vs all 26 bots in opponents/ (+ v13, v6): 300 of 312 matches won. 21 opponents 12/0
(+1990 bigbet to +15926 maniac); threebet 11/1, raiser16 11/1, tiny13 10/2; the only close ones
are near-copies of v16 itself: xr16 +330 (6/6), v13 +196 (7/5). Max 33s of the 75s bank per leg.
Squeeze (taskpolicy -b, vs station): stage 1 8 at once ~16.7s/leg of 30, stage 2 4 at once ~29s/leg
of 75, 0 notices. A random hero search (16 v16 variants, 3 knob moves each) found nothing above noise.

### How much to trust an A/B number
Null tests (identical bots through `tools/ab.py`): +202 +-83, -171 +-64, -49 +-96 (same seeds as
the first), +8 +-55. The spread of those means is about 2x the reported SE, so a single run under
~3 SE is noise. Promote only what replicates on independent seed sets and on both machines (v8,
v9, v10 each did, at +300 to +900 per run).

### Pre-submission check (v14, current main)
- all wins vs every bot in `opponents/` (both machines, 0 notices)
- 8 parallel matches pinned to efficiency cores vs station: max ~17.6s of the 30s bank per leg;
  real stage 2 (1000 hands), 4 parallel: ~31s of 75s per leg (engine "time used" sums both legs)
- `tools/fuzz.py`: garbage / non-object JSON, unknown types, extra or missing fields, notices,
  no init, tiny time bank, all-in-only and check-only spots -> one legal reply each, clean exit
- start-up + first reply 0.18s, peak memory ~39MB; evaluator 0 mismatches vs engine
- lean / panic modes driven by engine-reported `time_left_ms`

### Open ideas
- [ ] a stronger, independent size-reading opponent to test v5/v6 sizing against
- [ ] more careful river play (thin value, bluff-catching vs polarized bettors)
- [ ] stage 2 (1000 hands): trust the opponent model sooner / weaker priors?
