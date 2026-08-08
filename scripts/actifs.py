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
