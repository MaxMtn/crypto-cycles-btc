"""
Moteur de cycles : situe la position actuelle du Bitcoin par rapport aux cycles
historiques complets, à la même phase (même nombre de jours depuis le halving).

Ne fait aucun appel réseau : tout est calculé localement à partir de
data/btc_cycles.csv. Écrit data/current_position.json, utilisé plus tard par
la page web.

Règles épistémiques (voir CLAUDE.md) : on ne dispose que de 3 cycles complets.
Toute statistique dérivée est donc fragile. On affiche systématiquement la
fourchette (min/médiane/max) et jamais un chiffre unique présenté comme
certain. Aucune prédiction de date ou de prix.
"""

import csv
import json
import statistics
from pathlib import Path

INPUT_FILE = Path(__file__).resolve().parent.parent / "data" / "btc_cycles.csv"
OUTPUT_FILE = Path(__file__).resolve().parent.parent / "data" / "current_position.json"

# Fenêtre de tolérance (en jours) pour élargir l'échantillon autour de la même
# phase de cycle : comparer uniquement le jour exact ne donnerait que 3 valeurs
# possibles (une par cycle), on assouplit donc un peu pour avoir une lecture
# moins grossière, sans s'éloigner de "la même phase".
WINDOW_DAYS = 14

METRICS = ["mvrv", "mayer_multiple", "drawdown_pct"]


def load_rows():
    with open(INPUT_FILE, newline="") as f:
        rows = list(csv.DictReader(f))
    rows.sort(key=lambda r: r["date"])
    return rows


def to_float(value):
    return float(value) if value not in ("", None) else None


def group_by_cycle(rows):
    """Répartit les lignes par numéro de halving. Ignore les lignes d'avant
    le premier halving (pas de cycle défini)."""
    cycles = {}
    for row in rows:
        if row["halving_number"] == "":
            continue
        n = int(row["halving_number"])
        cycles.setdefault(n, []).append(row)
    return cycles


def value_at_day_offset(cycle_rows, day_offset, metric):
    for row in cycle_rows:
        if int(row["days_since_halving"]) == day_offset:
            return to_float(row[metric])
    return None


def values_in_window(cycle_rows, day_offset, metric, window):
    values = []
    for row in cycle_rows:
        d = int(row["days_since_halving"])
        if abs(d - day_offset) <= window:
            v = to_float(row[metric])
            if v is not None:
                values.append(v)
    return values


def percentile_rank(value, sample):
    """Pourcentage de l'échantillon historique inférieur ou égal à `value`."""
    if not sample:
        return None
    at_or_below = sum(1 for v in sample if v <= value)
    return round(at_or_below / len(sample) * 100, 1)


def build_metric_report(current_value, reference_cycles, day_offset, metric):
    exact_day_values = {}
    for cycle_number, cycle_rows in reference_cycles.items():
        v = value_at_day_offset(cycle_rows, day_offset, metric)
        if v is not None:
            exact_day_values[f"cycle_{cycle_number}"] = round(v, 4)

    exact_sample = list(exact_day_values.values())

    windowed_sample = []
    for cycle_rows in reference_cycles.values():
        windowed_sample.extend(values_in_window(cycle_rows, day_offset, metric, WINDOW_DAYS))

    return {
        "current_value": round(current_value, 4) if current_value is not None else None,
        "historical_values_same_day": exact_day_values,
        "historical_min": round(min(exact_sample), 4) if exact_sample else None,
        "historical_median": round(statistics.median(exact_sample), 4) if exact_sample else None,
        "historical_max": round(max(exact_sample), 4) if exact_sample else None,
        "rank_percentile_exact_day": percentile_rank(current_value, exact_sample),
        "rank_percentile_windowed": percentile_rank(current_value, windowed_sample),
        "windowed_sample_size": len(windowed_sample),
        "window_days": WINDOW_DAYS,
    }


def main():
    print("Lecture de data/btc_cycles.csv...")
    rows = load_rows()
    cycles = group_by_cycle(rows)

    current_cycle_number = max(cycles.keys())
    current_cycle_rows = cycles[current_cycle_number]
    reference_cycles = {n: r for n, r in cycles.items() if n != current_cycle_number}

    latest_row = current_cycle_rows[-1]
    day_offset = int(latest_row["days_since_halving"])

    print(f"Position actuelle : cycle {current_cycle_number}, "
          f"jour {day_offset} après le halving.")
    print(f"Cycles de référence (complets) : {sorted(reference_cycles.keys())}")

    metrics_report = {}
    for metric in METRICS:
        current_value = to_float(latest_row[metric])
        metrics_report[metric] = build_metric_report(
            current_value, reference_cycles, day_offset, metric
        )

    result = {
        "generated_date": latest_row["date"],
        "current_cycle": {
            "halving_number": current_cycle_number,
            "days_since_halving": day_offset,
        },
        "reference_cycles_used": sorted(reference_cycles.keys()),
        "caveat": (
            "Comparaison basée sur seulement "
            f"{len(reference_cycles)} cycles historiques complets : chaque écart "
            "peut refléter le hasard autant qu'un signal réel. Le cycle actuel "
            "diffère structurellement des précédents (ETF spot, flux "
            "institutionnels, contexte de taux) : ne pas traiter l'historique "
            "comme un gabarit fiable. Ceci n'est pas une prédiction."
        ),
        "metrics": metrics_report,
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Terminé : résultat enregistré dans {OUTPUT_FILE}")
    print()
    print("--- Résumé lisible ---")
    for metric, report in metrics_report.items():
        print(f"{metric} : valeur actuelle = {report['current_value']}, "
              f"cycles précédents à ce stade (min/médiane/max) = "
              f"{report['historical_min']} / {report['historical_median']} / "
              f"{report['historical_max']}")


if __name__ == "__main__":
    main()
