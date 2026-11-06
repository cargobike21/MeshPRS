# 0034: The smart-beaconing move threshold default is 500 m

- **Status:** accepted
- **Date:** 2026-11-06
- **Answers:** OPEN-QUESTIONS Q43
- **Spec sections affected:** §5.5

## Context

- **§5.5's distance trigger defaulted to 100 m.**
- **GPS drift moves a parked tracker.** On 2026-11-05, with a 50 m threshold, VK4AZ-12 parked indoors at work sent about 20 positions in a day that came only from drift: the fix wandered and the altitude ran from 32 m to 193 m. Each was a flood (`../../design/field-trial-log.md` §4).
- **With 500 m and a 60 min maximum interval** (2026-11-06), the drift positions stopped.
- **Moving, 500 m costs little track detail.** At bike speed the 120 s minimum interval, not the distance, sets the beacon rate: at 20 km/h a bike covers about 670 m in 120 s. The heading trigger (15°) still marks the turns.

## Options

1. **Raise the default to 500 m.** For: measured, and stops drift floods with no new rule. Against: a walker (about 5 km/h) beacons on distance only every 6 min, though turns and the maximum interval still fire.
2. **Keep 100 m, but ignore the distance trigger while speed stays under 5 km/h.** For: keeps detail for slow movers. Against: speed from a drifting fix is itself noisy, and it hasn't been tested.
3. **Keep 100 m.** For: nothing changes. Against: the floods measured on 2026-11-05.

## Decision

Option 1. Decided by Alec, 2026-11-06.

## Consequences

- **The spec, §5.5:** the "moved more than" default becomes 500 m. It stays configurable, so a walker or a slow mobile MAY set it lower.
- **Implementations:** Mesh Buddy's default for a new install becomes 500 m (`tools/mesh-buddy/main.cpp`). A saved setting is kept, and VK4AZ-12 already uses 500 m.
- **Test vectors:** none. They don't cover beacon timing.
