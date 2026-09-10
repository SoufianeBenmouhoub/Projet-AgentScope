"""Construit un extrait TraceLab de taille raisonnable, et le décrit.

    python scripts/build_tracelab_extract.py chemin/vers/syfi_coding_trace.jsonl.gz

Méthode de sélection — les deux choix sont justifiés dans `docs/data-sources.md` :

- on sélectionne **par session**, pas par ligne : une ligne est une invocation du modèle,
  et couper une session en deux fausserait toute mesure par session ;
- on impose un **quota par agent** : le fichier est ordonné et ses premières sessions sont
  toutes produites par Claude ; sans quota, l'extrait serait mono-agent.

Le script ne modifie rien et n'écrit que le fichier d'extrait, à côté de la source.
"""

from __future__ import annotations

import gzip
import json
import sys
from collections import Counter
from pathlib import Path

SESSIONS_PER_PROVIDER = 120


def build(source: Path, sessions_per_provider: int = SESSIONS_PER_PROVIDER) -> Path:
    target = source.parent / "tracelab-extrait.jsonl"

    kept: list[dict] = []
    sessions: set[str] = set()
    per_provider: Counter[str] = Counter()

    with gzip.open(source, "rt", encoding="utf-8") as stream:
        for line in stream:
            record = json.loads(line)
            session = record.get("session_id")
            provider = record.get("provider")

            if session not in sessions:
                if per_provider[provider] >= sessions_per_provider:
                    continue
                per_provider[provider] += 1

            sessions.add(session)
            kept.append(record)

    target.write_text("\n".join(json.dumps(record) for record in kept), encoding="utf-8")
    _describe(target, kept, sessions)
    return target


def _describe(target: Path, kept: list[dict], sessions: set[str]) -> None:
    providers = Counter(record["provider"] for record in kept)
    tools = [tool for record in kept for tool in (record.get("tools") or [])]
    moments = [
        event["timestamp"]
        for record in kept
        for event in (record.get("timing_events") or [])
        if event.get("timestamp")
    ]

    print(f"Extrait écrit : {target}  ({target.stat().st_size / 1024 / 1024:.1f} Mo)")
    print(f"  sessions            : {len(sessions)}")
    print(f"  invocations         : {len(kept)}")
    print(f"  agents              : {dict(providers)}")
    print(f"  appels d'outils     : {len(tools)}")
    if moments:
        print(f"  période             : {min(moments)[:10]} → {max(moments)[:10]}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(1)

    build(Path(sys.argv[1]))
