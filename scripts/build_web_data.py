"""
Prépare les données pour la page web : écrit docs/data.js à partir de
data/btc_cycles.csv et data/current_position.json.

Pourquoi un fichier .js et pas directement le CSV ? Parce que les navigateurs
interdisent à une page ouverte depuis le disque (double-clic) d'aller lire un
autre fichier du disque. En écrivant les données sous forme de fichier
JavaScript, la page fonctionne aussi bien en local qu'une fois publiée en ligne,
sans rien avoir à installer.

Ne fait aucun appel réseau.
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CYCLES_FILE = ROOT / "data" / "btc_cycles.csv"
POSITION_FILE = ROOT / "data" / "current_position.json"
OUTPUT_FILE = ROOT / "docs" / "data.js"

METRICS = ["mvrv", "mayer_multiple", "drawdown_pct"]

# Lissage de la fourchette historique, en jours de part et d'autre.
# Sans lissage, la bande min-max de trois séries très volatiles est tellement
# dentelée qu'elle se lit comme du bruit. On regroupe donc les valeurs
# observées autour de la même phase de cycle, ce qui rejoint la fenêtre déjà
# utilisée par cycle_engine.py. La bande obtenue est un peu plus large que le
# min-max jour par jour : elle dit "voici ce qu'on a observé autour de ce
# moment du cycle", ce qui est plus prudent, pas moins.
ENVELOPE_WINDOW = 10

HALVING_LABELS = {
    1: "Cycle 2012",
    2: "Cycle 2016",
    3: "Cycle 2020",
    4: "Cycle 2024 (en cours)",
}


def to_float(value):
    return float(value) if value not in ("", None) else None


def load_cycles():
    with open(CYCLES_FILE, newline="") as f:
        rows = list(csv.DictReader(f))
    rows.sort(key=lambda r: r["date"])

    cycles = {}
    for row in rows:
        if row["halving_number"] == "":
            continue
        n = int(row["halving_number"])
        cycles.setdefault(n, []).append(row)
    return cycles


def build_series(cycles):
    """Pour chaque cycle : liste de points [jour, mvrv, mayer, drawdown, prix]."""
    series = {}
    for n, rows in cycles.items():
        points = []
        for row in rows:
            mvrv = to_float(row["mvrv"])
            mayer = to_float(row["mayer_multiple"])
            drawdown = to_float(row["drawdown_pct"])
            price = to_float(row["price_usd"])
            points.append([
                int(row["days_since_halving"]),
                round(mvrv, 3) if mvrv is not None else None,
                round(mayer, 3) if mayer is not None else None,
                round(drawdown, 2) if drawdown is not None else None,
                round(price) if price is not None else None,
            ])
        series[n] = {
            "label": HALVING_LABELS.get(n, f"Cycle {n}"),
            "start_date": rows[0]["date"],
            "points": points,
        }
    return series


def build_envelope(cycles, reference_numbers):
    """Fourchette (min / médiane / max) des cycles de référence autour de chaque
    jour du cycle. C'est ce qui rend la dispersion visible en permanence sur le
    graphique, plutôt qu'un seul chiffre à la date du jour.

    On ne garde que les jours où TOUS les cycles de référence ont des valeurs :
    sinon la fourchette se rétrécirait artificiellement en fin de graphique,
    simplement parce qu'il y reste moins de cycles."""
    # Pour chaque cycle et chaque métrique : jour -> valeur
    par_cycle = {n: {m: {} for m in METRICS} for n in reference_numbers}
    for n in reference_numbers:
        for row in cycles[n]:
            day = int(row["days_since_halving"])
            for metric in METRICS:
                value = to_float(row[metric])
                if value is not None:
                    par_cycle[n][metric][day] = value

    dernier_jour_commun = min(
        max(par_cycle[n][METRICS[0]]) for n in reference_numbers
    )

    envelope = {metric: [] for metric in METRICS}
    for day in range(dernier_jour_commun + 1):
        for metric in METRICS:
            values = []
            tous_presents = True
            for n in reference_numbers:
                serie = par_cycle[n][metric]
                proches = [
                    serie[d]
                    for d in range(day - ENVELOPE_WINDOW, day + ENVELOPE_WINDOW + 1)
                    if d in serie
                ]
                if not proches:
                    tous_presents = False
                    break
                values.extend(proches)

            if not tous_presents:
                continue

            values.sort()
            envelope[metric].append([
                day,
                round(values[0], 3),
                round(values[len(values) // 2], 3),
                round(values[-1], 3),
            ])
    return envelope


def main():
    print("Lecture des données...")
    cycles = load_cycles()
    current_number = max(cycles)
    reference_numbers = sorted(n for n in cycles if n != current_number)

    series = build_series(cycles)
    envelope = build_envelope(cycles, reference_numbers)

    with open(POSITION_FILE) as f:
        position = json.load(f)

    payload = {
        "cycles": series,
        "envelope": envelope,
        "current_cycle_number": current_number,
        "reference_cycle_numbers": reference_numbers,
        "position": position,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        f.write("// Fichier généré automatiquement par scripts/build_web_data.py\n")
        f.write("// Ne pas modifier à la main : il sera écrasé au prochain lancement.\n")
        f.write("const DONNEES = ")
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")

    size_ko = OUTPUT_FILE.stat().st_size / 1024
    print(f"Terminé : {OUTPUT_FILE} ({size_ko:.0f} Ko)")
    for n, data in sorted(series.items()):
        print(f"  {data['label']} : {len(data['points'])} jours")
    print(f"  Fourchette historique : {len(envelope['mvrv'])} jours couverts")


if __name__ == "__main__":
    main()
