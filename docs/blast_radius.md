# Blast radius and risk

For each changed SDK symbol, CanaryGraph selects direct usage callers, walks graph predecessors, and
projects affected functions onto classes, modules, and detected HTTP endpoints. It records shortest
paths so every impact statement is explainable.

Risk is capped at 100:

```text
round(change severity × 0.45)
+ min(direct functions, 3) × 8
+ min(transitive functions, 8) × 2
+ min(endpoints, 2) × 12
+ 5 when mean resolution confidence < 0.75
```

Levels are LOW 0–34, MEDIUM 35–64, HIGH 65–84, and CRITICAL 85–100. The report includes each
component; no learned model or hidden weight is involved.

