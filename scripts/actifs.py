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
    # Altcoins retenus le 2026-08-08. Critère : disposer des quatre métriques
    # ET couvrir entièrement au moins deux cycles BTC (2016 et 2020). Un seul
    # cycle de référence ne permet aucune fourchette.
    # Écartés pour un seul cycle complet : ADA, BCH, LINK, ETC.
    # Écarté faute de MVRV : XMR.
    # Disponibles mais non retenus car marginaux aujourd'hui : DASH, DCR, DGB, XEM.
    "ltc": {
        "nom": "Litecoin",
        "symbole": "LTC",
        "debut_donnees": "2013-04-01",
    },
    "xrp": {
        "nom": "XRP",
        "symbole": "XRP",
        "debut_donnees": "2014-08-15",
    },
    "doge": {
        "nom": "Dogecoin",
        "symbole": "DOGE",
        "debut_donnees": "2014-01-23",
    },
    "xlm": {
        "nom": "Stellar",
        "symbole": "XLM",
        "debut_donnees": "2015-09-30",
    },
}

# Les quatre métriques récupérées pour chaque actif. La capitalisation réalisée
# (CapRealUSD) n'est plus gratuite depuis fin 2025 : on la reconstitue à partir
# de la capitalisation de marché et du MVRV.
METRIQUES_API = ["PriceUSD", "CapMrktCurUSD", "CapMVRVCur", "SplyCur"]

# Métriques calculées ensuite, communes à tous les actifs.
METRIQUES_CALCULEES = ["mvrv", "mayer_multiple", "drawdown_pct"]


def fichier_metriques(actif):
    return DOSSIER_DONNEES / f"{actif}_metrics.csv"


def fichier_cycles(actif):
    return DOSSIER_DONNEES / f"{actif}_cycles.csv"


def fichier_position(actif):
    return DOSSIER_DONNEES / f"{actif}_position.json"
