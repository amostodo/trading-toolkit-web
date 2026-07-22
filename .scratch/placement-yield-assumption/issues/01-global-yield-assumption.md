# Global Placement Yield Assumption

Type: feature
Status: resolved
Labels: resolved

Implement the OpenSpec change `placement-yield-assumption`: add a persisted placement-only premium selector and derive expected profit, safety pad, rating, and ranking from it without changing the API.

## Acceptance

- Default is 30%; only 30% to 100% in 10% increments are valid.
- The active assumption overrides API display fields and updates list, detail, tooltip, sorting, and rating reactively.
- Other convertible strategies and LOF remain unchanged.

## Comments

- 2026-07-22: Planning complete. Implementation has not started.
- 2026-07-22: Implemented and verified. The Web-only preference defaults to 30%, accepts only approved 10% increments through 100%, updates placement-derived metrics reactively, and leaves other convertible strategies and LOF unchanged.
