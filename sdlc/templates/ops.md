# Ops report <yyyy-mm-dd hh:mm>
Window: <from> → <to> · Source: var/log/app.jsonl · Version: <latest tag>
Verdict: HEALTHY | BREACH

## Signals (≤ 8 lines)
- requests: <n> · errors: <n> (<rate>%) · p95: <ms> ms
- top paths: <path n, path n>

## Breaches (≤ 10 lines; "None." if healthy)
- <threshold broken> — <evidence: count, sample event>

## Diagnosis (≤ 8 lines; omit if healthy)
- Likely cause: <code path app/<file>.py:<line>> — <why>

## Proposed intent (≤ 5 lines; omit if healthy)
- slug: <kebab-slug>
- problem: <one line, user impact first>
