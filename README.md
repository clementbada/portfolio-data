# portfolio-data

Données de marché, taux, inflation et communiqués de banques centrales pour le
dashboard portefeuille (PEA + CTO). Dépôt privé, tout tourne dans GitHub Actions.

## Fonctionnement

1. **`Rafraîchir les données`** (chaque jour à 20:10 UTC) appelle les sources,
   applique le cache et le repli, puis commite :
   - `data/latest.json` — format stable lu par le dashboard ;
   - `data/latest.csv` — export tabulaire ;
   - `data/summary.md` — résumé court en français.
2. **`Tests des sources`** (à chaque push et chaque lundi) vérifie que chaque API
   répond encore avec les champs utilisés.

Chaque jeu de données a un statut : `ok` (source principale), `secours`
(source de secours), `ancienne valeur` (toutes les sources en panne : dernière
valeur connue + date + message), `indisponible` (jamais obtenue).

## Sources

| Jeu | Principale | Secours | Clé | Fraîcheur visée |
|---|---|---|---|---|
| `fx_eur` | Frankfurter | Currency-api (2 adresses) | non | 20 h |
| `ecb_deposit_rate` | BCE Data Portal | dernière valeur | non | 20 h |
| `yield_10y_ea_aaa_daily` | BCE (courbe AAA 10 ans) | dernière valeur | non | 20 h |
| `inflation_eu` | Eurostat `prc_hicp_minr` | dernière valeur | non | 20 h |
| `unemployment_eu` | Eurostat `une_rt_m` | dernière valeur | non | 20 h |
| `inflation_us`, `unemployment_us` | BLS v1 | dernière valeur | non | 20 h |
| `news_bce`, `news_fed`, `news_boe` | flux RSS officiels | dernière valeur | non | 6 h |
| `news_portfolio` | MarketAux (1 requête par ligne, 16/jour) | dernière valeur | oui, gratuite | 20 h |

Les 10 ans par pays (US, FR, DE, IT, ES, UK, JP) ne sont pas ici : aucune API gratuite
testée ne donne la valeur quotidienne par pays. Ils sont relevés par la tâche du dashboard
(IBKR pour les US, Trading Economics pour les autres).

Mentions à afficher là où la donnée apparaît : champ `attribution` de chaque jeu
(ex. « Source : BCE », « Source : Eurostat », « Actualités : MarketAux »).

## Lancer

```bash
python -m portfolio_data.fetch          # --force pour ignorer le cache
python -m unittest tests.test_fallback  # hors ligne
python -m unittest tests.test_sources   # appelle les vraies API
```

Bibliothèque standard Python 3.12 uniquement, aucune dépendance.

## Secrets

Voir `.env.example`. En production : *Settings → Secrets and variables → Actions*.
Aucune clé dans le code ni dans le dépôt.
