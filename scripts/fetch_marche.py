"""
Construit les deux indicateurs de marché : la part du Bitcoin dans un panier
constant d'actifs, et le ratio ETH/BTC.

Pourquoi un panier constant et non « tout le marché » ?
-------------------------------------------------------
Une dominance calculée sur tous les actifs disponibles serait faussée par la
couverture de Coin Metrics, qui commence et s'arrête à des dates arbitraires.
BNB s'arrête en 2019, DOT en 2022, XTZ en 2022 — alors que ces projets sont
bien vivants. Chaque sortie du panier ferait bondir mécaniquement la part du
Bitcoin, sans aucun rapport avec le marché.

On fige donc un panier d'actifs présents en continu depuis le halving de 2016,
ce qui garantit qu'une variation de la part traduit un mouvement de prix, et
non un changement de composition.

Limite à assumer, affichée dans l'interface : ce panier est composé des
survivants de 2016. Les alts qui ont dominé ensuite (BNB, SOL, ADA...) n'y
figurent pas, et les vétérans qu'il contient ont décliné. La part du BTC y
dérive donc à la hausse sur le long terme pour une raison de composition. Seule
la FORME à l'intérieur d'un cycle est comparable, pas le NIVEAU d'un cycle à
l'autre.

Stablecoins et jetons enveloppés sont exclus : les premiers ne suivent pas le
cycle, les seconds compteraient deux fois le même actif (weth, wbtc, usdt_omni).
"""

import csv
import json
import urllib.request

from actifs import DOSSIER_DONNEES, fichier_cycles
from compute_metrics import add_halving_info

API_URL = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"

# Panier figé : actifs dont Coin Metrics couvre la capitalisation en continu
# depuis le halving de juillet 2016 jusqu'à aujourd'hui, hors stablecoins et
# hors jetons enveloppés. Vérifié le 2026-08-08.
PANIER = ["btc", "eth", "ltc", "xrp", "xlm", "xmr",
          "doge", "dash", "dcr", "dgb", "xem"]

DEBUT = "2016-07-09"
SORTIE = DOSSIER_DONNEES / "marche_metrics.csv"


def recuperer(metrique, actifs, debut):
    url = (f"{API_URL}?assets={','.join(actifs)}&metrics={metrique}"
           f"&frequency=1d&page_size=10000&start_time={debut}")
    par_jour = {}
    while url:
        with urllib.request.urlopen(url) as reponse:
            page = json.loads(reponse.read())
        for ligne in page["data"]:
            valeur = ligne.get(metrique)
            if valeur is not None:
                par_jour.setdefault(ligne["time"][:10], {})[ligne["asset"]] = float(valeur)
        url = page.get("next_page_url")
    return par_jour


def indexer_base_100(lignes):
    """Ramène chaque cycle à 100 le jour de son halving.

    Sans cela, les cycles ne seraient pas comparables : la part du BTC dans ce
    panier dérive à la hausse sur dix ans parce que les alts qui le composent
    ont vieilli, pas parce que le marché se comporte différemment. En base 100,
    on compare des mouvements relatifs à l'intérieur de chaque cycle, ce qui
    est la question posée — pas des niveaux absolus, qui ne veulent rien dire
    d'un cycle à l'autre."""
    references = {}
    for ligne in lignes:
        cycle = ligne["halving_number"]
        if cycle == "" or cycle in references:
            continue
        references[cycle] = (ligne["dominance_btc"], ligne["ratio_eth_btc"])

    for ligne in lignes:
        cycle = ligne["halving_number"]
        if cycle == "":
            ligne["dominance_base100"] = ""
            ligne["ratio_base100"] = ""
            continue
        base_dominance, base_ratio = references[cycle]
        ligne["dominance_base100"] = round(100 * ligne["dominance_btc"] / base_dominance, 3)
        ligne["ratio_base100"] = round(100 * ligne["ratio_eth_btc"] / base_ratio, 3)


def main():
    print(f"Récupération des capitalisations du panier ({len(PANIER)} actifs)...")
    caps = recuperer("CapMrktCurUSD", PANIER, DEBUT)

    print("Récupération des prix BTC et ETH...")
    prix = recuperer("PriceUSD", ["btc", "eth"], DEBUT)

    lignes = []
    jours_incomplets = 0

    for jour in sorted(caps):
        valeurs = caps[jour]
        # On n'écrit que les jours où TOUS les actifs du panier sont présents :
        # un panier à composition variable ne se compare pas à lui-même.
        if len(valeurs) != len(PANIER):
            jours_incomplets += 1
            continue

        prix_jour = prix.get(jour, {})
        if "btc" not in prix_jour or "eth" not in prix_jour:
            jours_incomplets += 1
            continue

        total = sum(valeurs.values())
        lignes.append({
            "date": jour,
            "dominance_btc": round(100 * valeurs["btc"] / total, 4),
            "ratio_eth_btc": round(prix_jour["eth"] / prix_jour["btc"], 8),
        })

    if jours_incomplets:
        print(f"  {jours_incomplets} jours ignorés (panier incomplet)")

    add_halving_info(lignes)
    indexer_base_100(lignes)

    colonnes = ["date", "dominance_btc", "ratio_eth_btc",
                "dominance_base100", "ratio_base100",
                "halving_number", "days_since_halving"]

    destination = fichier_cycles("marche")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with open(destination, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=colonnes)
        writer.writeheader()
        writer.writerows(lignes)

    print(f"  Terminé : {len(lignes)} lignes enregistrées dans {destination}")
    print(f"  du {lignes[0]['date']} au {lignes[-1]['date']}")
    print(f"  part du BTC aujourd'hui : {lignes[-1]['dominance_btc']:.1f} %")
    print(f"  ratio ETH/BTC aujourd'hui : {lignes[-1]['ratio_eth_btc']:.5f}")


if __name__ == "__main__":
    main()
