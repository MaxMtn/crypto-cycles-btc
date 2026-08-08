# Plateforme d'analyse des cycles crypto

## Contexte

Projet personnel d'analyse dynamique des cycles de marché des cryptomonnaies
(bullrun / bearmarket). L'objectif est de situer un actif dans son cycle actuel
en le comparant aux cycles historiques.

Usage strictement personnel dans un premier temps. Pas de diffusion à des tiers.

## Profil de l'utilisateur — À LIRE EN PREMIER

**L'utilisateur est débutant en développement.** Il ne code pas et ne souhaite
pas apprendre à coder pour ce projet. Cela conditionne toute l'interaction :

- Écrire l'intégralité du code, ne jamais demander à l'utilisateur d'écrire du code
- Expliquer chaque commande avant de la lancer, en français, sans jargon
- Une seule étape à la fois, vérifier que ça fonctionne avant de continuer
- Ne jamais supposer qu'un outil est installé — vérifier
- Quand quelque chose casse, demander le message d'erreur exact plutôt que de
  supposer
- Préférer systématiquement la solution la plus simple qui fonctionne, même si
  elle est moins élégante

## Contraintes dures

| Contrainte | Détail |
|---|---|
| Budget | 0 € / mois. Aucun service payant, aucune carte bancaire. |
| Licence données | Coin Metrics Community = Creative Commons **non commercial**. Compatible usage perso uniquement. |
| Infrastructure | Aucun serveur, aucune base de données à administrer. |

## Stack retenue

- **Données on-chain et prix** : Coin Metrics Community API
  (`community-api.coinmetrics.io`, aucune clé requise, ~10 requêtes / 6 s par
  IP), **source unique pour la Phase 1** — `PriceUSD` couvre déjà tout
  l'historique nécessaire, inutile de multiplier les sources pour commencer.
  Binance/CoinGecko restent une option de secours pour plus tard si Coin
  Metrics restreint encore son tier gratuit, mais ne pas les coder avant d'en
  avoir besoin. Alternative sans API : les archives CSV quotidiennes du dépôt
  GitHub `coinmetrics/data`.
- **Automatisation** : GitHub Actions (cron gratuit sur dépôt public).
- **Stockage** : le dépôt GitHub lui-même (fichiers CSV versionnés).
- **Interface** : page HTML statique hébergée sur GitHub Pages.
- **Langage** : Python pour les traitements, HTML/JS vanilla pour l'affichage.
  Éviter les frameworks lourds (pas de React, pas de build step) — l'utilisateur
  doit pouvoir ouvrir le fichier et comprendre grossièrement ce qu'il fait.

Vérifier au démarrage que les métriques nécessaires sont toujours dans le tier
community de Coin Metrics : leur offre gratuite a été réduite fin 2025.

**Point vérifié le 2026-08-06** : `CapRealUSD` (capitalisation réalisée brute)
n'est plus dans le tier gratuit (erreur 403). Elle reste calculable gratuitement
par combinaison d'autres métriques toujours libres :
`CapMrktCurUSD / CapMVRVCur = capitalisation réalisée`, puis
`capitalisation réalisée / SplyCur = prix réalisé`. `CapMVRVCur`,
`CapMrktCurUSD`, `PriceUSD` et `SplyCur` sont confirmés libres à cette date.

## Périmètre du MVP

**Bitcoin uniquement.** C'est le seul actif avec de la donnée on-chain gratuite
exploitable, et il pilote le cycle du reste du marché.

Un seul écran : les cycles historiques superposés et alignés, avec la position
actuelle marquée et exprimée en percentile.

Métriques du MVP :

1. **MVRV** — capitalisation de marché / capitalisation réalisée (`CapMrktCurUSD`
   / `CapRealUSD`, ou `CapMVRVCur` directement)
2. **Mayer Multiple** — prix / moyenne mobile 200 jours
3. **Drawdown depuis l'ATH**
4. **Jours écoulés depuis le halving**
5. **Prix réalisé** comme plancher de référence

## Le moteur de cycles — cœur du projet

C'est la partie qui a de la valeur, pas la collecte de données.

**Ancrage** : commencer par un alignement sur les halvings (simple, reproductible).
Prévoir de pouvoir basculer plus tard sur un ancrage « plus bas de cycle »
(creux de drawdown maximal) pour comparer les deux lectures.

**Normalisation** : axe temporel en jours depuis l'ancrage, avec option
« pourcentage de cycle écoulé » pour gérer les durées inégales.

**Scoring** : pour chaque métrique, calculer le percentile de la valeur actuelle
par rapport à sa distribution historique **à la même phase de cycle**. Pas de
prédiction de date, pas de prix cible.

## Règles épistémiques — non négociables

L'interface doit rendre l'incertitude visible en permanence :

- **n = 3 à 4 cycles complets seulement.** Toute statistique dérivée est fragile.
  Afficher les fourchettes et la dispersion, jamais un point unique.
- Le cycle actuel est structurellement différent des précédents (ETF spot, flux
  institutionnels, contexte de taux). Ne pas traiter l'historique comme un
  gabarit fiable.
- **Interdits** : prédiction de date de sommet, prix cible, formulation
  déterministe (« le sommet sera en… »).
- **Exception décidée le 2026-08-08** : la page affiche un « repère théorique »
  de date de creux. L'utilisateur l'a demandé après avoir pris connaissance de
  l'objection (avec n = 3, aucune méthode n'estime quoi que ce soit de solide,
  et la largeur de l'intervalle mesure surtout le manque de cycles).
  Conditions à préserver : titre annonçant explicitement le caractère
  théorique, méthode de calcul affichée à côté du chiffre, encadré visuellement
  distinct du reste (pointillés), tableau comparant en permanence les cinq
  méthodes — leurs résultats s'étalent sur 135 jours à données identiques, ce
  qui est le vrai enseignement — et mention que le creux du cycle en cours est
  peut-être déjà passé. Ne pas étendre ce procédé à une date de sommet ni à un
  prix cible, qui restent interdits.
- **Méthode retenue par défaut : « intervalle entre creux »**, choisie par
  l'utilisateur le 2026-08-08. Motif : l'intervalle calendaire entre creux
  successifs est la seule grandeur stable du jeu de données (1431 puis 1425
  jours), alors que le jour de creux compté depuis le halving se décale
  surtout parce que les halvings s'espacent (1319, 1402, 1440 jours) — le
  décalage apparent tient donc au point de référence plus qu'au marché. Ne pas
  revenir à la médiane sans raison explicite.
- Backtests : attention au biais de look-ahead (certaines métriques sont révisées
  a posteriori) et, dès qu'on sortira de BTC, au biais de survivance sur les
  altcoins.
- Aucun signal ne doit être opaque. Toute règle « acheter / conserver / vendre »
  doit rester explicite, lisible et éditable par l'utilisateur, qui doit pouvoir
  répondre à « pourquoi ce signal » six mois plus tard.

## Roadmap

**Phase 1 — MVP analyste (en cours)**
Bitcoin, 5 métriques, graphique d'alignement des cycles, mise à jour quotidienne
automatique.

**Phase 2 — Extension multi-actifs**
ETH (données on-chain partielles), puis altcoins via des proxys de cycle :
dominance BTC, ratio ETH/BTC, drawdown depuis l'ATH, force relative vs BTC.
Pas de coût de base on-chain disponible pour ces actifs — l'assumer explicitement
dans l'interface.

**Phase 3 — Portefeuille**
Saisie manuelle des positions dans un CSV du dépôt (gratuit, cinq minutes par
mois, aucun risque de sécurité). Croisement des positions avec les scores de
cycle. Les APIs de portefeuille (Zerion, Zapper, Covalent) sont écartées : tiers
gratuits trop limités.

## Sécurité — règles absolues

- **Jamais** de clé privée, de seed phrase ou de mot de passe dans le projet,
  quelle que soit la justification.
- Connexion de wallet en **lecture seule** uniquement, par adresse publique.
- Ne jamais commiter de clé API dans le dépôt.
- Le dépôt étant public (nécessaire pour GitHub Actions et Pages gratuits),
  considérer que tout son contenu est visible de tous.

## Hors périmètre

- Flux d'exchanges (entrées/sorties) : produit payant chez tous les fournisseurs,
  aucune alternative gratuite crédible. Ne pas chercher à contourner.
- Exécution d'ordres, connexion à un exchange, trading automatisé.
- Toute diffusion à des tiers : en France, fournir des recommandations
  d'investissement à autrui relève de l'AMF (statut PSAN, conseil en
  investissement). À traiter avant d'y penser.

## Note

Ce projet produit un outil d'aide à la réflexion, pas un conseil en
investissement. Aucune sortie de la plateforme ne doit être formulée comme une
recommandation financière.
