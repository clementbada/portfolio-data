# Intégration au dashboard

- `patch_dashboard.py` : ajoute l'onglet Actus et branche l'onglet Macro sur `data/latest.json`
  (+ `yields.json`, taux 10 ans du jour). Appliqué le 25/10/2026 → version 78 du dashboard.
- `smoke.js` : test jsdom (onglets, filtres, absence de NaN/undefined/erreurs).

Pour rafraîchir seulement les données dans une page déjà patchée, remplacer le bloc
`var MARKET_DATA = {...};` (json.JSONDecoder().raw_decode) — jamais Read/Edit sur le fichier entier.
