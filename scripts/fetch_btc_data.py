"""
Récupère les données Bitcoin (prix, capitalisation, MVRV, offre en circulation)
depuis l'API gratuite Coin Metrics, et les enregistre dans un fichier CSV.

Aucune clé API n'est nécessaire. Cette API est limitée à 10 requêtes / 6 secondes
par adresse IP - largement suffisant pour ce script (une poignée de requêtes).
"""

import csv
import json
import urllib.request
from pathlib import Path

API_URL = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
METRICS = ["PriceUSD", "CapMrktCurUSD", "CapMVRVCur", "SplyCur"]
OUTPUT_FILE = Path(__file__).resolve().parent.parent / "data" / "btc_metrics.csv"


def fetch_all_pages():
    """Interroge l'API Coin Metrics et récupère toutes les pages de résultats."""
    rows = []
    url = (
        f"{API_URL}?assets=btc&metrics={','.join(METRICS)}"
        "&frequency=1d&page_size=1000"
    )

    while url:
        with urllib.request.urlopen(url) as response:
            payload = json.loads(response.read())

        rows.extend(payload["data"])
        print(f"{len(rows)} jours récupérés...")
        url = payload.get("next_page_url")

    return rows


def build_csv_rows(raw_rows):
    """Calcule le prix réalisé (CapRealUSD n'est plus gratuit sur Coin Metrics,
    on le retrouve par calcul : capitalisation réalisée = cap. de marché / MVRV)
    et prépare les lignes du CSV final."""
    csv_rows = []
    skipped = 0

    for row in raw_rows:
        needed = (row.get("CapMrktCurUSD"), row.get("CapMVRVCur"),
                  row.get("SplyCur"), row.get("PriceUSD"))
        if None in needed:
            skipped += 1
            continue

        market_cap = float(row["CapMrktCurUSD"])
        mvrv = float(row["CapMVRVCur"])
        supply = float(row["SplyCur"])
        realized_cap = market_cap / mvrv
        realized_price = realized_cap / supply

        csv_rows.append({
            "date": row["time"][:10],
            "price_usd": row["PriceUSD"],
            "market_cap_usd": row["CapMrktCurUSD"],
            "mvrv": row["CapMVRVCur"],
            "supply": row["SplyCur"],
            "realized_price_usd": realized_price,
        })

    if skipped:
        print(f"{skipped} jours ignorés (données manquantes)")

    return csv_rows


def main():
    print("Récupération des données Bitcoin depuis Coin Metrics...")
    raw_rows = fetch_all_pages()
    csv_rows = build_csv_rows(raw_rows)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_rows[0].keys())
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"Terminé : {len(csv_rows)} lignes enregistrées dans {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
