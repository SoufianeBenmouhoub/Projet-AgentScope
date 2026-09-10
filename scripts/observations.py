"""Calcule les trois observations chiffrées de `docs/observations.md`.

    python scripts/observations.py chemin/vers/tracelab-extrait.jsonl

**Les chiffres sont calculés par le programme, jamais estimés.** Ce script lit l'extrait
brut plutôt que la base : à ce jour, la normalisation ne produit que des sessions, donc les
appels d'outils sur lesquels portent deux des trois observations ne sont pas encore
importés. Le jour où ils le seront, les mêmes chiffres seront lisibles directement dans le
tableau de bord — `docs/observations.md` indique pour chacun l'écran et le filtre.
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def load(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def tool_error_rate(records: list[dict[str, Any]]) -> None:
    tools = [tool for record in records for tool in (record.get("tools") or [])]
    observed = [tool for tool in tools if tool.get("is_error") is not None]
    failed = [tool for tool in observed if tool["is_error"]]

    print("1. Taux d'erreur des appels d'outils")
    print(f"   appels d'outils           : {len(tools)}")
    print(f"   dont l'issue est connue   : {len(observed)}")
    print(f"   en erreur                 : {len(failed)}")
    print(f"   taux                      : {100 * len(failed) / len(observed):.2f} %")
    unknown = len(tools) - len(observed)
    naive = 100 * len(failed) / len(tools)
    print(f"   issue inconnue            : {unknown} — exclus du dénominateur")
    print(f"   (les compter comme réussis donnerait {naive:.2f} %, soit une sous-estimation)")


def latency_spread(records: list[dict[str, Any]]) -> None:
    latencies = sorted(
        tool["tool_wall_latency_ms"]
        for record in records
        for tool in (record.get("tools") or [])
        if tool.get("tool_wall_latency_ms") is not None
    )

    median = statistics.median(latencies)
    mean = statistics.mean(latencies)
    p90 = latencies[int(len(latencies) * 0.90)]
    p99 = latencies[int(len(latencies) * 0.99)]

    print("\n2. Latence des appels d'outils")
    print(f"   mesures                   : {len(latencies)}")
    print(f"   médiane                   : {median:.0f} ms")
    print(f"   p90                       : {p90} ms")
    print(f"   p99                       : {p99} ms")
    print(f"   moyenne                   : {mean:.0f} ms")
    print(
        f"   (la moyenne vaut {mean / median:.1f}× la médiane : la distribution a une queue longue)"
    )


def cache_by_provider(records: list[dict[str, Any]]) -> None:
    total: Counter[str] = Counter()
    published: Counter[str] = Counter()
    tokens: defaultdict[str, int] = defaultdict(int)

    for record in records:
        provider = record["provider"]
        total[provider] += 1
        value = record.get("claude_cache_creation_input_tokens")
        if value is not None:
            published[provider] += 1
            tokens[provider] += value

    print("\n3. Tokens de création de cache, par agent")
    for provider in sorted(total):
        share = 100 * published[provider] / total[provider]
        print(
            f"   {provider:<8} {published[provider]:>6} / {total[provider]:<6} invocations "
            f"renseignent la mesure ({share:.0f} %) — {tokens[provider]} tokens"
        )
    print("   (une part à 0 % signifie « non publié », jamais « zéro token »)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(1)

    data = load(Path(sys.argv[1]))
    print(f"Extrait : {len(data)} invocations, {len({r['session_id'] for r in data})} sessions\n")
    tool_error_rate(data)
    latency_spread(data)
    cache_by_provider(data)
