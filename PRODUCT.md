# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Un utilisateur unique, propriétaire du projet, non développeur. Usage
strictement personnel : aucune diffusion à des tiers n'est prévue ni permise
(en France, conseiller autrui en investissement relève de l'AMF).

Deux situations d'usage confirmées, toutes deux à servir :

- **Coup d'œil quotidien, au téléphone.** Quelques secondes, en mobilité. La
  réponse doit tomber sans manipulation.
- **Session d'analyse, à l'ordinateur.** Plus rare, plus longue : comparaison
  entre actifs, zoom, changement de méthode de calcul.

## Product Purpose

Situer le cycle de marché en cours face aux cycles passés, pour un actif donné,
afin de savoir *où l'on se trouve* — jamais pour deviner la suite.

**La question à laquelle la page doit répondre en premier, dès l'ouverture :
« Où en est le cycle ? »** Une lecture de synthèse immédiate — phase, position
par rapport aux cycles précédents — avant tout graphique et avant toute
manipulation. C'est le manque principal de la version actuelle, qui ouvre sur
une explication puis des réglages, et laisse l'utilisateur composer lui-même sa
réponse.

## Positioning

L'alignement sur les halvings du Bitcoin permet de comparer des moments
équivalents entre cycles, plutôt que des dates absolues. Le produit affiche
systématiquement la dispersion entre cycles et le nombre d'observations, là où
les outils comparables affichent un chiffre unique sans son incertitude.

## Operating Context

- Données Coin Metrics Community, actualisées chaque jour à 6h30 UTC par GitHub
  Actions, publiées sur GitHub Pages et Vercel (crypto-cockpit.vercel.app).
- Les données s'arrêtent toujours à la veille : une journée n'est consolidée
  qu'une fois terminée.
- La page est un fichier HTML unique, ouvrable par double-clic hors ligne.

## Capabilities and Constraints

**Actifs, par ordre d'importance confirmé :**

1. **Bitcoin** — point de départ systématique.
2. **Vue Marché** (part du BTC dans un panier figé, ratio ETH/BTC) — sert à
   savoir si la saison des alts a commencé.
3. **Ethereum** — au même niveau d'importance que BTC.
4. LTC, XRP, DOGE, XLM — secondaires, consultés occasionnellement.

**Métriques :** MVRV, Mayer Multiple, drawdown depuis l'ATH, prix réalisé, jours
depuis le halving. Pour la vue Marché : dominance et ratio ETH/BTC, en brut et
en base 100 au halving.

**Contraintes dures :**

- 0 € par mois, aucun service payant, aucune carte bancaire.
- Licence des données Creative Commons BY-NC : usage non commercial uniquement.
- HTML/CSS/JS vanilla, sans build ni framework. L'utilisateur ne code pas et
  doit pouvoir ouvrir le fichier et comprendre grossièrement ce qu'il fait.
- Aucun serveur, aucune base de données.
- Nombre de cycles de référence très faible : 3 pour BTC, 2 pour les autres.

## Brand Commitments

Nom : **Crypto Cockpit**. Logo existant (`docs/favicon.svg`, `docs/logo.svg`) :
pastille sombre, courbe de cycle claire, point orange de position actuelle.
Interface en français. Thème clair et sombre suivant le système.

Contrainte visuelle formulée par l'utilisateur pour cette refonte : « moderne et
dynamique, et surtout un UX pratique ». Enregistrée telle quelle ; la traduction
en direction visuelle relève du travail de conception, pas de ce document.

## Evidence on Hand

Données réelles et vérifiées, aucune donnée d'exemple :

- BTC depuis 2010-07-18, ETH depuis 2015-08-08, et quatre altcoins.
- Trois cycles complets pour BTC (creux aux jours 777, 889, 912), deux pour les
  autres.
- Position au 2026-08-07 : BTC au jour 839, drawdown -48,0 %, MVRV 1,23.

Aucun témoignage, aucun chiffre d'usage, aucune performance à afficher : ce
produit n'a qu'un utilisateur et rien de tel ne doit être inventé.

## Product Principles

1. **Répondre avant de faire manipuler.** La synthèse d'abord, l'exploration
   ensuite. Une page qui exige un réglage avant de dire quoi que ce soit a
   échoué.
2. **L'incertitude est une donnée, pas une note de bas de page.** Fourchettes,
   dispersion et nombre d'observations s'affichent avec le chiffre, jamais
   après.
3. **Aucune prédiction de date ni de prix.** Le repère théorique de creux est la
   seule exception, décidée explicitement, et reste étiqueté comme tel.
4. **Aucun signal opaque.** Toute règle doit rester lisible et modifiable par
   l'utilisateur, qui doit pouvoir répondre à « pourquoi ce chiffre » six mois
   plus tard.
5. **Servir les deux scènes d'usage.** Le téléphone doit répondre en un coup
   d'œil ; l'ordinateur doit permettre de creuser. Ni l'un ni l'autre n'est un
   sous-produit de la version faite pour l'autre.

## Accessibility & Inclusion

Aucune exigence de conformité formelle n'a été établie. Contraintes de fait :
lecture au téléphone en extérieur (contraste et taille de texte), et interface
utilisable au doigt comme à la souris.
