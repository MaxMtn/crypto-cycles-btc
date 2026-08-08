"""
Récupère les données de chaque actif suivi (prix, capitalisation, MVRV, offre
en circulation) depuis l'API gratuite Coin Metrics, et les enregistre dans un
fichier CSV par actif.

Aucune clé API n'est nécessaire. Cette API est limitée à 10 requêtes / 6 secondes
par adresse IP - largement suffisant pour ce script.

Les actifs suivis sont listés dans scripts/actifs.py.
"""

import csv
import json
import urllib.request

from actifs import METRIQUES_API, actifs_reels, fichier_metriques

API_URL = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"


def fetch_all_pages(actif):
    """Interroge l'API Coin Metrics et récupère toutes les pages de résultats."""
    rows = []
    url = (
        f"{API_URL}?assets={actif}&metrics={','.join(METRIQUES_API)}"
        "&frequency=1d&page_size=10000"
    )

    while url:
        with urllib.request.urlopen(url) as response:
            payload = json.loads(response.read())

        rows.extend(payload["data"])
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

    # Tri chronologique : l'API renvoie ses pages dans un ordre qui dépend de
    # leur taille. Sans ce tri, chaque actualisation quotidienne réécrirait le
    # fichier dans un ordre différent et produirait un diff illisible dans git,
    # au lieu des seules lignes réellement ajoutées.
    csv_rows.sort(key=lambda r: r["date"])
    return csv_rows, skipped


def traiter_actif(actif, config):
    print(f"Récupération des données {config['nom']} ({actif.upper()})...")
    raw_rows = fetch_all_pages(actif)
    csv_rows, skipped = build_csv_rows(raw_rows)

    if skipped:
        print(f"  {skipped} jours ignorés (données manquantes)")

    destination = fichier_metriques(actif)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with open(destination, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_rows[0].keys())
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"  Terminé : {len(csv_rows)} lignes enregistrées dans {destination}")


def main():
    # Les actifs synthétiques (indicateurs de marché) sont produits par
    # fetch_marche.py, pas téléchargés tels quels.
    for actif, config in actifs_reels().items():
        traiter_actif(actif, config)


if __name__ == "__main__":
    main()
