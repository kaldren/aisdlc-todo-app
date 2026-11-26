# Release NNN → v0.N.0
Commit: <sha on main> · Result: READY | NOT READY (<why>)

## Checks (≤ 10 lines)
- `make test` → <result>
- `make smoke` → <result>
- AC<n> end-to-end: `<curl ...>` → <result>

## Changes for users (≤ 5 lines)
- <change>

## Rollback (≤ 3 lines)
`git checkout <previous tag> && make prod`

## Watch after release (≤ 4 lines; for the ops agent)
- <log event / path / signal> — <what "wrong" looks like>
