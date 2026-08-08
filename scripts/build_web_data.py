"""
Prépare les données pour la page web : écrit docs/data.js à partir des fichiers
de cycles et de position de chaque actif suivi.

Pourquoi un fichier .js et pas directement les CSV ? Parce que les navigateurs
interdisent à une page ouverte depuis le disque (double-clic) d'aller lire un
autre fichier du disque. En écrivant les données sous forme de fichier
JavaScript, la page fonctionne aussi bien en local qu'une fois publiée en ligne,
sans rien avoir à installer.

Note : la fourchette min / médiane / max entre cycles n'est PAS calculée ici.
Elle est recalculée par la page web, parce que l'utilisateur peut y choisir
quels cycles afficher : une fourchette figée serait fausse dès qu'il en
désélectionne un. Voir la fonction calculerFourchette() dans docs/index.html.
"""

import csv
import json
from datetime import datetime, timezone

from actifs import (ACTIFS, METRIQUES_CALCULEES, RACINE, fichier_cycles,
                    fichier_position)

OUTPUT_FILE = RACINE / "docs" / "data.js"

HALVING_LABELS = {
    1: "Cycle 2012",
    2: "Cycle 2016",
    3: "Cycle 2020",
    4: "Cycle 2024 (en cours)",
}


def to_float(value):
    return float(value) if value not in ("", None) else None


def load_cycles(actif):
    with open(fichier_cycles(actif), newline="") as f:
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
    """Pour chaque cycle : liste de points [jour, mvrv, mayer, drawdown].

    Le prix n'est pas embarqué : la page ne l'affiche nulle part et il pesait
    près d'un cinquième du fichier."""
    series = {}
    for n, rows in cycles.items():
        points = []
        for row in rows:
            mvrv = to_float(row["mvrv"])
            mayer = to_float(row["mayer_multiple"])
            drawdown = to_float(row["drawdown_pct"])
            points.append([
                int(row["days_since_halving"]),
                round(mvrv, 3) if mvrv is not None else None,
                round(mayer, 3) if mayer is not None else None,
                round(drawdown, 2) if drawdown is not None else None,
            ])
        series[n] = {
            "label": HALVING_LABELS.get(n, f"Cycle {n}"),
            "start_date": rows[0]["date"],
            "points": points,
        }
    return series


def construire_actif(actif, config):
    cycles = load_cycles(actif)
    with open(fichier_position(actif)) as f:
        position = json.load(f)

    numero_actuel = max(cycles)
    # Seuls les cycles complets servent de référence. Le moteur de cycles a
    # déjà fait ce tri ; on reprend sa décision pour que la page et les
    # chiffres calculés côté Python parlent des mêmes cycles.
    references = position["reference_cycles_used"]

    series = build_series(cycles)
    # Les cycles écartés sont retirés des séries : les afficher laisserait
    # croire qu'ils sont comparables alors qu'ils sont tronqués.
    for n in position.get("reference_cycles_excluded", []):
        series.pop(n, None)

    return {
        "nom": config["nom"],
        "symbole": config["symbole"],
        "cycles": series,
        "current_cycle_number": numero_actuel,
        "reference_cycle_numbers": references,
        "position": position,
    }


def main():
    print("Lecture des données...")
    actifs = {}
    dernier_jour = ""

    for actif, config in ACTIFS.items():
        actifs[actif] = construire_actif(actif, config)
        dernier_jour = max(dernier_jour, actifs[actif]["position"]["generated_date"])

    # Deux dates différentes, et la distinction compte : la première dit
    # jusqu'où vont les données, la seconde quand on est allé les chercher.
    # Si l'actualisation automatique tombe en panne, la seconde cesse
    # d'avancer — c'est ce qui permet à la page de s'en apercevoir.
    actualise_le = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    payload = {
        "actifs": actifs,
        "actif_par_defaut": "btc",
        "dernier_jour_donnees": dernier_jour,
        "actualise_le": actualise_le,
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
    print(f"  Données jusqu'au {dernier_jour}, actualisées le {actualise_le}")
    for actif, data in actifs.items():
        cycles_txt = ", ".join(
            f"{data['cycles'][n]['label']} ({len(data['cycles'][n]['points'])} j)"
            for n in sorted(data["cycles"])
        )
        print(f"  {data['nom']} : {cycles_txt}")


if __name__ == "__main__":
    main()
