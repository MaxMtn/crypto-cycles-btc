"""
Liste des actifs suivis par la plateforme, partagée par tous les scripts.

Pour ajouter un actif : vérifier d'abord que Coin Metrics fournit gratuitement
les quatre métriques nécessaires (PriceUSD, CapMrktCurUSD, CapMVRVCur, SplyCur),
puis ajouter une ligne ici. Rien d'autre à modifier.

Vérification faite le 2026-08-08 : sur les 138 actifs du tier community, 125
disposent du MVRV. SOL, AVAX, MATIC et XMR en sont dépourvus et ne peuvent donc
pas recevoir le même traitement.
"""

from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_DONNEES = RACINE / "data"

ACTIFS = {
    "btc": {
        "nom": "Bitcoin",
        "symbole": "BTC",
        "debut_donnees": "2010-07-18",
    },
    "eth": {
        "nom": "Ethereum",
        "symbole": "ETH",
        # ETH démarre en août 2015. Le cycle 1 (nov. 2012 - juil. 2016) n'est
        # donc couvert qu'à 25 % : il sera automatiquement écarté des cycles
        # de référence, car incomplet.
        "debut_donnees": "2015-08-08",
    },
    # Altcoins (LTC, XRP, DOGE, XLM) retirés le 2026-08-11 : le calque du
    # moteur de cycles BTC (halving, MVRV, comparaison à 2 cycles) ne leur
    # apportait pas grand-chose — ils n'ont pas de halving propre, et les
    # comparer à seulement 2 cycles passés était la fourchette la plus fragile
    # de tout le site. Voir CLAUDE.md pour la discussion complète.
    #
    # Le panier fixe utilisé par fetch_marche.py pour calculer la dominance du
    # BTC (scripts/fetch_marche.py, PANIER) continue d'inclure ltc/xrp/doge/xlm
    # comme composantes de calcul : retirer leur onglet d'analyse individuel
    # ne change rien à ce panier, qui doit rester figé pour que l'indexation
    # base 100 reste comparable d'un cycle à l'autre.
    #
    # Indicateurs de marché : pas un actif mais deux séries construites, d'où
    # "synthetique" (fetch_data.py les ignore, fetch_marche.py les produit).
    "marche": {
        "nom": "BTC Dominance",
        "symbole": "vs marché",
        "debut_donnees": "2016-07-09",
        "synthetique": True,
        "metriques": ["dominance_base100", "dominance_btc",
                      "ratio_base100", "ratio_eth_btc"],
    },
}

# Métriques par défaut, pour les actifs qui n'en déclarent pas. Le drawdown
# est en tête : c'est la métrique active au premier chargement de la page
# (voir metriqueChoisie dans docs/index.html), sa carte doit donc apparaître
# en premier plutôt qu'en bas de la colonne.
METRIQUES_STANDARD = ["drawdown_pct", "mvrv", "mayer_multiple"]


# Nombre de décimales conservées dans le fichier envoyé à la page. Inutile
# d'embarquer plus de précision que ce qui sera affiché : le fichier est
# téléchargé à chaque visite.
PRECISION = {
    "mvrv": 3,
    "mayer_multiple": 3,
    "drawdown_pct": 2,
    "dominance_btc": 3,
    "dominance_base100": 2,
    "ratio_eth_btc": 6,
    "ratio_base100": 2,
}


def metriques_de(actif):
    return ACTIFS[actif].get("metriques", METRIQUES_STANDARD)


def est_synthetique(actif):
    return ACTIFS[actif].get("synthetique", False)


def actifs_reels():
    return {c: v for c, v in ACTIFS.items() if not est_synthetique(c)}

# Les quatre métriques récupérées pour chaque actif. La capitalisation réalisée
# (CapRealUSD) n'est plus gratuite depuis fin 2025 : on la reconstitue à partir
# de la capitalisation de marché et du MVRV.
METRIQUES_API = ["PriceUSD", "CapMrktCurUSD", "CapMVRVCur", "SplyCur"]



def fichier_metriques(actif):
    return DOSSIER_DONNEES / f"{actif}_metrics.csv"


def fichier_cycles(actif):
    return DOSSIER_DONNEES / f"{actif}_cycles.csv"


def fichier_position(actif):
    return DOSSIER_DONNEES / f"{actif}_position.json"
