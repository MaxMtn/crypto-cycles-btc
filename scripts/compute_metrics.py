"""
Calcule les métriques dérivées du cycle Bitcoin à partir de data/btc_metrics.csv :
Mayer Multiple, plus haut historique (ATH) et drawdown, jours depuis le halving.

Ne fait aucun appel réseau : tout est calculé localement à partir des données
déjà téléchargées par fetch_btc_data.py.
"""

import csv
from datetime import date
from pathlib import Path

INPUT_FILE = Path(__file__).resolve().parent.parent / "data" / "btc_metrics.csv"
OUTPUT_FILE = Path(__file__).resolve().parent.parent / "data" / "btc_cycles.csv"

SMA_WINDOW = 200

# Dates de halving Bitcoin, fixes et connues à l'avance (pas besoin d'API)
HALVING_DATES = [
    date(2012, 11, 28),
    date(2016, 7, 9),
    date(2020, 5, 11),
    date(2024, 4, 20),
]


def load_rows():
    with open(INPUT_FILE, newline="") as f:
        rows = list(csv.DictReader(f))
    rows.sort(key=lambda r: r["date"])
    return rows


def add_mayer_multiple(rows):
    """Ajoute la moyenne mobile 200 jours et le Mayer Multiple (prix / SMA200)."""
    prices = [float(r["price_usd"]) for r in rows]
    running_sum = 0.0

    for i, row in enumerate(rows):
        running_sum += prices[i]
        if i >= SMA_WINDOW:
            running_sum -= prices[i - SMA_WINDOW]

        if i >= SMA_WINDOW - 1:
            sma = running_sum / SMA_WINDOW
            row["sma_200d"] = sma
            row["mayer_multiple"] = prices[i] / sma
        else:
            # Pas assez de jours précédents pour calculer une moyenne sur 200 jours
            row["sma_200d"] = ""
            row["mayer_multiple"] = ""


def add_drawdown(rows):
    """Ajoute le plus haut historique atteint jusqu'à ce jour (ATH) et le drawdown."""
    ath = 0.0
    for row in rows:
        price = float(row["price_usd"])
        ath = max(ath, price)
        row["ath_usd"] = ath
        row["drawdown_pct"] = (price - ath) / ath * 100


def add_halving_info(rows):
    """Ajoute le numéro du halving en cours et le nombre de jours écoulés depuis."""
    for row in rows:
        row_date = date.fromisoformat(row["date"])

        current_halving = None
        halving_number = 0
        for i, halving_date in enumerate(HALVING_DATES, start=1):
            if halving_date <= row_date:
                current_halving = halving_date
                halving_number = i

        if current_halving is None:
            # Avant le tout premier halving : pas encore de cycle au sens classique
            row["halving_number"] = ""
            row["days_since_halving"] = ""
        else:
            row["halving_number"] = halving_number
            row["days_since_halving"] = (row_date - current_halving).days


def main():
    print("Lecture de data/btc_metrics.csv...")
    rows = load_rows()

    print("Calcul du Mayer Multiple...")
    add_mayer_multiple(rows)

    print("Calcul du drawdown depuis l'ATH...")
    add_drawdown(rows)

    print("Calcul des jours depuis le halving...")
    add_halving_info(rows)

    fieldnames = list(rows[0].keys())
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Terminé : {len(rows)} lignes enregistrées dans {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
