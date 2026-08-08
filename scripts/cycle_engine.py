"""
Moteur de cycles : situe la position actuelle de chaque actif par rapport aux
cycles historiques complets, à la même phase (même nombre de jours depuis le
halving Bitcoin).

Ne fait aucun appel réseau : tout est calculé localement à partir des fichiers
produits par compute_metrics.py. Écrit un fichier de position par actif.

Règles épistémiques (voir CLAUDE.md) : on ne dispose que de très peu de cycles
complets — 3 pour Bitcoin, 2 pour Ethereum dont l'historique commence en 2015.
Toute statistique dérivée est donc fragile. On affiche systématiquement la
fourchette (min/médiane/max) et jamais un chiffre unique présenté comme
certain. Aucune prédiction de date ou de prix.
"""

import csv
import json
import statistics

from actifs import ACTIFS, fichier_cycles, fichier_position, metriques_de

# Fenêtre de tolérance (en jours) pour élargir l'échantillon autour de la même
# phase de cycle : comparer uniquement le jour exact ne donnerait que 2 ou 3
# valeurs possibles (une par cycle), on assouplit donc un peu pour avoir une
# lecture moins grossière, sans s'éloigner de "la même phase".
WINDOW_DAYS = 14


def load_rows(actif):
    with open(fichier_cycles(actif), newline="") as f:
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


def cycle_est_complet(cycle_rows):
    """Un cycle n'est utilisable comme référence que s'il commence bien au jour
    du halving. Sinon l'actif n'existait pas encore, ou ses données commencent
    en cours de route : sa courbe serait tronquée et comparée à tort à des
    cycles entiers. C'est le cas d'Ethereum sur le cycle 2012, couvert à 25 %
    seulement."""
    return int(cycle_rows[0]["days_since_halving"]) == 0


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


def construire_avertissement(actif, config, reference_cycles, cycles_ecartes):
    nombre = len(reference_cycles)
    texte = (
        f"Comparaison basée sur seulement {nombre} "
        f"cycle{'s' if nombre > 1 else ''} historique{'s' if nombre > 1 else ''} "
        f"complet{'s' if nombre > 1 else ''} : chaque écart peut refléter le "
        "hasard autant qu'un signal réel. Le cycle actuel diffère "
        "structurellement des précédents (ETF spot, flux institutionnels, "
        "contexte de taux) : ne pas traiter l'historique comme un gabarit "
        "fiable. Ceci n'est pas une prédiction."
    )

    if cycles_ecartes:
        liste = ", ".join(str(n) for n in sorted(cycles_ecartes))
        texte += (
            f" Le{'s' if len(cycles_ecartes) > 1 else ''} cycle{'s' if len(cycles_ecartes) > 1 else ''} "
            f"{liste} {'sont écartés' if len(cycles_ecartes) > 1 else 'est écarté'} "
            f"de la comparaison : l'historique de {config['nom']} commence le "
            f"{config['debut_donnees']} et ne les couvre pas entièrement."
        )

    if config.get("synthetique"):
        texte += (
            " Ces indicateurs reposent sur un panier figé de 11 actifs suivis "
            "sans interruption depuis 2016, hors stablecoins et jetons "
            "enveloppés. Ce panier ne représente pas tout le marché : il est "
            "composé des survivants de 2016, et les alts qui ont dominé "
            "ensuite (BNB, SOL, ADA...) n'y figurent pas. La part du Bitcoin "
            "y dérive donc à la hausse pour une raison de composition, pas de "
            "marché. Comparer la FORME à l'intérieur d'un cycle a du sens ; "
            "comparer les NIVEAUX d'un cycle à l'autre n'en a pas, d'où "
            "l'affichage en base 100 au halving."
        )
    elif actif != "btc":
        texte += (
            f" {config['nom']} n'a pas de halving : son cycle est ici aligné "
            "sur les halvings du Bitcoin, en supposant que celui-ci pilote le "
            "reste du marché. C'est une hypothèse de lecture, pas un fait."
        )

    return texte


def traiter_actif(actif, config):
    print(f"{config['nom']} ({actif.upper()}) :")
    rows = load_rows(actif)
    cycles = group_by_cycle(rows)

    current_cycle_number = max(cycles.keys())
    current_cycle_rows = cycles[current_cycle_number]

    reference_cycles, cycles_ecartes = {}, []
    for n, cycle_rows in cycles.items():
        if n == current_cycle_number:
            continue
        if cycle_est_complet(cycle_rows):
            reference_cycles[n] = cycle_rows
        else:
            cycles_ecartes.append(n)

    latest_row = current_cycle_rows[-1]
    day_offset = int(latest_row["days_since_halving"])

    print(f"  Position : cycle {current_cycle_number}, jour {day_offset} après le halving.")
    print(f"  Cycles de référence complets : {sorted(reference_cycles.keys())}")
    if cycles_ecartes:
        print(f"  Cycles écartés (incomplets) : {sorted(cycles_ecartes)}")

    metrics_report = {}
    for metric in metriques_de(actif):
        current_value = to_float(latest_row[metric])
        metrics_report[metric] = build_metric_report(
            current_value, reference_cycles, day_offset, metric
        )

    result = {
        "asset": actif,
        "asset_name": config["nom"],
        "generated_date": latest_row["date"],
        "current_cycle": {
            "halving_number": current_cycle_number,
            "days_since_halving": day_offset,
        },
        "reference_cycles_used": sorted(reference_cycles.keys()),
        "reference_cycles_excluded": sorted(cycles_ecartes),
        "caveat": construire_avertissement(actif, config, reference_cycles, cycles_ecartes),
        "metrics": metrics_report,
    }

    destination = fichier_position(actif)
    with open(destination, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"  Terminé : {destination}")
    for metric, report in metrics_report.items():
        print(f"    {metric} : actuel = {report['current_value']}, "
              f"cycles précédents (min/médiane/max) = "
              f"{report['historical_min']} / {report['historical_median']} / "
              f"{report['historical_max']}")


def main():
    for actif, config in ACTIFS.items():
        traiter_actif(actif, config)


if __name__ == "__main__":
    main()
