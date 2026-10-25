"""Patch du dashboard : onglet Actus + onglet Macro alimenté par portfolio-data.

Usage : python3 patch_dashboard.py <entrée.html> <latest.json> <sortie.html>
Remplacements chirurgicaux uniquement (jamais de réécriture des gros blocs de données).
Chaque remplacement est vérifié : s'il ne s'applique pas exactement une fois, le script échoue.
"""
import json
import re
import sys

src_path, data_path, out_path = sys.argv[1:4]
html = open(src_path, encoding="utf-8").read()


def once(old, new, label):
    global html
    n = html.count(old)
    if n != 1:
        sys.exit(f"ÉCHEC {label} : {n} occurrence(s)")
    html = html.replace(old, new)


# ------------------------------------------------------------------ données
doc = json.load(open(data_path, encoding="utf-8"))
slim = {"generated_at": doc["generated_at"], "datasets": {}}
for name, d in doc["datasets"].items():
    slim["datasets"][name] = {k: d.get(k) for k in
                              ("status", "provider", "attribution", "fetched_at", "last_success_at", "message", "data")}
market_js = json.dumps(slim, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

# ------------------------------------------------------------------ CSS
once("  .a-src a { color: var(--ink-3); }\n</style>", """  .a-src a { color: var(--ink-3); }

  /* ---------- actus & sources de données ---------- */
  .src-line { font-size: 11px; color: var(--ink-3); margin-top: 6px; }
  .src-line.warn { color: var(--accent); font-weight: 600; }
  .filter-row { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 12px; }
  .news-list { display: flex; flex-direction: column; }
  .news-item { display: grid; grid-template-columns: 92px 1fr; gap: 12px; padding: 11px 0; border-bottom: 1px solid var(--border); }
  .news-item:last-child { border-bottom: none; }
  .news-when { font-size: 12px; color: var(--ink-3); font-family: "IBM Plex Mono", monospace; line-height: 1.5; }
  .news-body { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
  .news-title { font-size: 14px; font-weight: 600; color: var(--ink); text-decoration: none; line-height: 1.35; }
  .news-title:hover { text-decoration: underline; }
  .news-meta { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; font-size: 11.5px; color: var(--ink-3); }
  .sym-chip { font-family: "IBM Plex Mono", monospace; font-size: 11px; font-weight: 600; background: var(--surface-2); color: var(--ink-2); border-radius: 6px; padding: 1px 7px; }
  .sent-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; background: var(--ink-3); }
  .sent-dot.good { background: var(--good); }
  .sent-dot.bad { background: var(--bad); }
  .news-empty { font-size: 13px; color: var(--ink-3); padding: 12px 0; }
  @media (max-width: 560px) {
    .news-item { grid-template-columns: 1fr; gap: 4px; }
    .tabnav { flex-wrap: wrap; }
  }
</style>""", "css")

# ------------------------------------------------------------------ onglet
once('    <button class="tab-btn" id="tabBtnMacro" type="button">Marché &amp; Macro</button>\n',
     '    <button class="tab-btn" id="tabBtnMacro" type="button">Marché &amp; Macro</button>\n'
     '    <button class="tab-btn" id="tabBtnNews" type="button">Actus</button>\n', "bouton Actus")

once("""      <div class="methodology-note" id="macroSourcesNote"></div>
    </footer>

  </div>

</div>

<script>""", """      <div class="methodology-note" id="macroSourcesNote"></div>
    </footer>

  </div>

  <div class="view" id="viewNews" hidden>

    <div class="src-line" id="newsUpdated"></div>

    <section class="panel">
      <h2>Actualités de mes lignes <span class="hint">articles qui citent tes titres — CTO 1 et actions du PEA (les ETF n'ont pas d'actus propres)</span></h2>
      <div class="filter-row" id="newsEnvRow"></div>
      <div class="filter-row" id="newsSymRow"></div>
      <div class="news-list" id="newsPortfolioList"></div>
      <div class="src-line" id="newsPortfolioSrc"></div>
    </section>

    <section class="panel">
      <h2>Communiqués des banques centrales <span class="hint">BCE, Fed, Banque d'Angleterre — flux officiels</span></h2>
      <div class="filter-row" id="newsBankRow"></div>
      <div class="news-list" id="newsBankList"></div>
      <div class="src-line" id="newsBankSrc"></div>
    </section>

    <footer class="foot">
      <span>Liens vers les sources originales (nouvel onglet). Sélection automatique, pas un conseil en investissement.</span>
    </footer>

  </div>

</div>

<script>""", "vue Actus")

once("""    var viewM = document.getElementById("viewMacro");
    function show(which) {
      viewP.hidden = which !== "portfolio";
      viewPerf.hidden = which !== "perf";
      viewA.hidden = which !== "analysis";
      viewM.hidden = which !== "macro";
      btnP.className = "tab-btn" + (which === "portfolio" ? " active" : "");
      btnPerf.className = "tab-btn" + (which === "perf" ? " active" : "");
      btnA.className = "tab-btn" + (which === "analysis" ? " active" : "");
      btnM.className = "tab-btn" + (which === "macro" ? " active" : "");
    }""", """    var viewM = document.getElementById("viewMacro");
    var btnN = document.getElementById("tabBtnNews");
    var viewN = document.getElementById("viewNews");
    function show(which) {
      viewP.hidden = which !== "portfolio";
      viewPerf.hidden = which !== "perf";
      viewA.hidden = which !== "analysis";
      viewM.hidden = which !== "macro";
      viewN.hidden = which !== "news";
      btnP.className = "tab-btn" + (which === "portfolio" ? " active" : "");
      btnPerf.className = "tab-btn" + (which === "perf" ? " active" : "");
      btnA.className = "tab-btn" + (which === "analysis" ? " active" : "");
      btnM.className = "tab-btn" + (which === "macro" ? " active" : "");
      btnN.className = "tab-btn" + (which === "news" ? " active" : "");
    }
    btnN.addEventListener("click", function () { show("news"); });""", "initTabs")

once("    renderMacroTab();\n    renderPerfTab();", "    renderMacroTab();\n    renderNewsTab();\n    renderPerfTab();", "init")

# ------------------------------------------------------------------ taux 10 ans (dernière valeur)
Y = json.load(open(sys.argv[4], encoding="utf-8")) if len(sys.argv) > 4 else None
if Y:
    for code, v in Y["yields"].items():
        pat = re.compile(r'(\{ code: "' + code + r'", flag: [^\n]*?yield10y: )[\d.]+(, isBund)')
        html, n = pat.subn(lambda m: m.group(1) + f'{v["value"]}, yieldAsOf: "{v["as_of"]}", yieldSrc: "{v["src"]}"' + m.group(2), html, count=1)
        if n != 1:
            sys.exit(f"ÉCHEC taux {code}")
    html, n = re.subn(r'var MACRO_RATES_UPDATED_AT = "[^"]*";', f'var MACRO_RATES_UPDATED_AT = "{Y["updated_at"]}";', html, count=1)
    if n != 1:
        sys.exit("ÉCHEC MACRO_RATES_UPDATED_AT")

# ------------------------------------------------------------------ JS : données + rendus
start = html.index("  function renderMacroRates() {")
end = html.index("  function renderMacroTab() {")
NEW_JS = r'''  // ---------------------------------------------------------------------
  // Données automatiques — dépôt privé clementbada/portfolio-data, rafraîchi chaque soir
  // par GitHub Actions (Frankfurter/BCE/Eurostat/BLS/flux RSS/MarketAux) puis injecté ici par
  // la tâche planifiée du soir. Chaque jeu porte son statut (ok / secours / ancienne valeur),
  // sa source à citer et son heure de récupération : jamais de chiffre sans date.
  var MARKET_DATA = __MARKET_DATA__;

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function mdSet(name) { return (MARKET_DATA && MARKET_DATA.datasets && MARKET_DATA.datasets[name]) || null; }
  function mdPoint(name, key) { var s = mdSet(name); return s && s.data && s.data[key] ? s.data[key] : null; }
  var MONTHS_FR = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."];
  function periodFr(asOf) {
    if (!asOf) return "";
    var p = asOf.split("-");
    return p.length === 2 ? MONTHS_FR[+p[1] - 1] + " " + p[0] : isoToFr(asOf);
  }
  function parisShort(iso) {
    if (!iso) return "—";
    try { return new Date(iso).toLocaleString("fr-FR", { timeZone: "Europe/Paris", day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }); }
    catch (e) { return iso; }
  }
  function srcLine(names) {
    var parts = [], warns = [];
    names.forEach(function (n) {
      var s = mdSet(n);
      if (!s) return;
      if (s.attribution && parts.indexOf(s.attribution) === -1) parts.push(s.attribution);
      if (s.status !== "ok" && s.message) warns.push(s.message);
    });
    return { text: parts.join(" · "), warn: warns.join(" — ") };
  }
  function fillSrc(id, names, extra) {
    var el = document.getElementById(id);
    if (!el) return;
    var s = srcLine(names);
    var when = MARKET_DATA && MARKET_DATA.generated_at ? " — mis à jour le " + parisShort(MARKET_DATA.generated_at) + " (Paris)" : "";
    el.className = "src-line" + (s.warn ? " warn" : "");
    el.textContent = (s.warn ? "⚠ " + s.warn + " · " : "") + s.text + (extra || "") + when;
  }

  function renderMacroRates() {
    var body = document.getElementById("macroRatesBody");
    if (!body) return;
    var bundRow = MACRO_RATES.filter(function (r) { return r.isBund; })[0];
    var dfr = mdPoint("ecb_deposit_rate", "ECB_DFR");
    body.innerHTML = "";
    MACRO_RATES.forEach(function (r) {
      var spread = bundRow && r.isEurozone && !r.isBund ? (r.yield10y - bundRow.yield10y) : null;
      var policy = r.isEurozone && dfr ? dfr.value.toFixed(2).replace(".", ",") + " %" : r.policyRate;
      var tr = document.createElement("tr");
      tr.innerHTML =
        '<td>' + r.flag + ' ' + r.zone + '</td>' +
        '<td class="num">' + policy + ' <span class="hint">' + r.policyLabel + '</span></td>' +
        '<td class="num">' + r.yield10y.toFixed(2) + ' % <span class="hint">' + r.yieldLabel +
          (r.yieldAsOf ? ' · ' + isoToFr(r.yieldAsOf) : '') + (r.yieldSrc ? ' · ' + esc(r.yieldSrc) : '') + '</span></td>' +
        '<td class="num">' + (spread == null ? (r.isEurozone ? "réf. Bund" : "—") : (spread >= 0 ? "+" : "") + Math.round(spread * 100) + " pb") + '</td>';
      body.appendChild(tr);
    });
    var note = document.getElementById("macroRatesNote");
    if (note) note.textContent =
      "Taux 10 ans : dernière clôture disponible pour chaque pays (date à côté du chiffre) — États-Unis via IBKR (indice TNX), autres pays via tradingeconomics.com ; relevés chaque soir par la tâche planifiée, dernier relevé le " +
      new Date(MACRO_RATES_UPDATED_AT).toLocaleString("fr-FR", { timeZone: "Europe/Paris", dateStyle: "short", timeStyle: "short" }) +
      " (Paris). Taux de dépôt BCE : " + (dfr ? "Source : BCE, au " + isoToFr(dfr.as_of) : "relevé manuel") +
      ". Spread vs Bund limité aux pays de la zone euro. Fed, BoE, BoJ : voir cartes banques centrales ci-dessus.";
  }

  // Lignes inflation/emploi : les valeurs automatiques (Eurostat IPCH harmonisé, BLS) remplacent
  // les relevés manuels quand elles existent ; Royaume-Uni et Japon restent en relevé manuel.
  var CPI_AUTO = {
    US: { cpi: ["inflation_us", "CPI_US"], un: ["unemployment_us", "UNEMP_US"], label: "BLS" },
    EZ: { cpi: ["inflation_eu", "HICP_EA"], un: ["unemployment_eu", "UNEMP_EA"], label: "Eurostat (IPCH)" },
    DE: { cpi: ["inflation_eu", "HICP_DE"], un: ["unemployment_eu", "UNEMP_DE"], label: "Eurostat (IPCH)" },
    FR: { cpi: ["inflation_eu", "HICP_FR"], un: ["unemployment_eu", "UNEMP_FR"], label: "Eurostat (IPCH)" },
    ES: { cpi: ["inflation_eu", "HICP_ES"], un: ["unemployment_eu", "UNEMP_ES"], label: "Eurostat (IPCH)" },
    IT: { cpi: ["inflation_eu", "HICP_IT"], un: ["unemployment_eu", "UNEMP_IT"], label: "Eurostat (IPCH)" }
  };
  function cpiRows() {
    var rows = MACRO_CPI.map(function (r) { return Object.assign({}, r); });
    if (!rows.some(function (r) { return r.code === "DE"; })) {
      var at = rows.findIndex(function (r) { return r.code === "FR"; });
      rows.splice(at < 0 ? rows.length : at, 0, { code: "DE", flag: "🇩🇪", zone: "Allemagne", cpi: null, core: null, cpiMonth: "", unemployment: null, unempPeriod: "", src: "" });
    }
    rows.forEach(function (r) {
      var a = CPI_AUTO[r.code];
      if (!a) { r.auto = false; return; }
      var c = mdPoint(a.cpi[0], a.cpi[1]), u = mdPoint(a.un[0], a.un[1]);
      if (c) { r.cpi = c.value; r.cpiMonth = periodFr(c.as_of); r.auto = true; r.src = a.label; }
      if (u) { r.unemployment = u.value; r.unempPeriod = periodFr(u.as_of); r.auto = true; if (!c) r.src = a.label; }
      if (c && r.core != null) r.coreNote = true; // cœur = relevé manuel, période possiblement différente
    });
    return rows;
  }

  function renderMacroCpi() {
    var body = document.getElementById("macroCpiBody");
    if (!body) return;
    body.innerHTML = "";
    cpiRows().forEach(function (r) {
      var tr = document.createElement("tr");
      tr.innerHTML =
        '<td>' + r.flag + ' ' + r.zone + '</td>' +
        (r.cpi == null ? '<td class="num">—</td>' : '<td class="num ' + (r.cpi >= 3 ? "bad" : "good") + '">' + (r.cpi >= 0 ? "+" : "") + r.cpi.toFixed(1) + ' %</td>') +
        '<td class="num">' + (r.core == null ? "—" : "+" + r.core.toFixed(1) + " %" + (r.coreNote ? ' <span class="hint">manuel</span>' : "")) + '</td>' +
        '<td class="num">' + (r.unemployment == null ? "—" : r.unemployment.toFixed(1) + ' %') + '</td>' +
        '<td><span class="hint">' + esc(r.src) + (r.cpiMonth ? ' — ' + esc(r.cpiMonth) : '') +
          (r.unempPeriod && r.unempPeriod !== r.cpiMonth ? " · chômage : " + esc(r.unempPeriod) : "") +
          (r.auto ? " · auto" : " · relevé manuel") + '</span></td>';
      body.appendChild(tr);
    });
    var note = document.getElementById("macroCpiNote");
    if (note) note.textContent =
      "États-Unis, zone euro, Allemagne, France, Espagne, Italie : automatique (Eurostat — inflation harmonisée IPCH, comparable entre pays, qui peut différer de l'indice national INSEE/Istat/INE — et BLS), dernière publication disponible. Royaume-Uni, Japon et inflation « cœur » : relevé manuel hebdomadaire. Chômage : dernier mois publié (souvent un mois de décalage avec l'inflation).";
    fillSrc("macroCpiNote2", ["inflation_eu", "unemployment_eu", "inflation_us", "unemployment_us"]);
  }

  // ---------------------------------------------------------------------
  // Onglet Actus — actualités des lignes (MarketAux) et communiqués officiels (RSS).
  var newsState = { env: "ALL", sym: null, bank: "ALL" };
  function sentClass(v) { return v == null ? "" : v > 0.15 ? "good" : v < -0.15 ? "bad" : ""; }
  function newsItemHtml(a, chips) {
    var safeUrl = /^https:\/\//.test(a.url || "") ? a.url : "#";
    return '<div class="news-item">' +
      '<div class="news-when">' + esc(parisShort(a.published)) + '</div>' +
      '<div class="news-body">' +
        '<a class="news-title" href="' + esc(safeUrl) + '" target="_blank" rel="noopener noreferrer">' + esc(a.title) + '</a>' +
        '<div class="news-meta">' + chips + '<span>' + esc(a.source || "") + '</span></div>' +
      '</div></div>';
  }
  function filterButtons(hostId, options, current, onPick) {
    var host = document.getElementById(hostId);
    if (!host) return;
    host.innerHTML = "";
    options.forEach(function (o) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "period-btn" + (o.key === current ? " active" : "");
      b.textContent = o.label;
      b.addEventListener("click", function () { onPick(o.key); });
      host.appendChild(b);
    });
  }
  function renderNewsTab() {
    var upd = document.getElementById("newsUpdated");
    if (upd) upd.textContent = MARKET_DATA && MARKET_DATA.generated_at
      ? "Dernière mise à jour : " + parisShort(MARKET_DATA.generated_at) + " (Paris) — rafraîchi chaque soir."
      : "Pas encore de données.";

    var pf = (mdSet("news_portfolio") && mdSet("news_portfolio").data) || [];
    filterButtons("newsEnvRow", [{ key: "ALL", label: "Toutes mes lignes" }, { key: "CTO 1", label: "CTO 1" }, { key: "PEA", label: "PEA" }],
      newsState.env, function (k) { newsState.env = k; newsState.sym = null; renderNewsTab(); });
    var inEnv = pf.filter(function (a) { return newsState.env === "ALL" || a.envelope === newsState.env; });
    var syms = [];
    inEnv.forEach(function (a) { (a.symbols || [a.symbol]).forEach(function (s) { if (syms.indexOf(s) === -1) syms.push(s); }); });
    syms.sort();
    filterButtons("newsSymRow", [{ key: null, label: "Tous les titres" }].concat(syms.map(function (s) { return { key: s, label: s }; })),
      newsState.sym, function (k) { newsState.sym = k; renderNewsTab(); });
    var shown = inEnv.filter(function (a) { return !newsState.sym || (a.symbols || [a.symbol]).indexOf(newsState.sym) !== -1; }).slice(0, 40);
    var list = document.getElementById("newsPortfolioList");
    if (list) list.innerHTML = shown.length ? shown.map(function (a) {
      var chips = (a.symbols || [a.symbol]).map(function (s) { return '<span class="sym-chip">' + esc(s) + '</span>'; }).join("") +
        (a.sentiment == null ? "" : '<span class="sent-dot ' + sentClass(a.sentiment) + '" title="Sentiment MarketAux : ' + esc(a.sentiment) + '"></span>');
      return newsItemHtml(a, chips);
    }).join("") : '<div class="news-empty">Aucun article récent pour cette sélection.</div>';
    fillSrc("newsPortfolioSrc", ["news_portfolio"], " — 3 articles max. par titre et par jour (plan gratuit)");

    var banks = [];
    ["news_bce", "news_fed", "news_boe"].forEach(function (n) { var s = mdSet(n); if (s && s.data) banks = banks.concat(s.data); });
    banks.sort(function (a, b) { return (b.published || "").localeCompare(a.published || ""); });
    filterButtons("newsBankRow", [{ key: "ALL", label: "Toutes" }, { key: "BCE", label: "BCE" }, { key: "Fed", label: "Fed" }, { key: "BoE", label: "BoE" }],
      newsState.bank, function (k) { newsState.bank = k; renderNewsTab(); });
    var bshown = banks.filter(function (a) { return newsState.bank === "ALL" || a.source === newsState.bank; }).slice(0, 24);
    var blist = document.getElementById("newsBankList");
    if (blist) blist.innerHTML = bshown.length ? bshown.map(function (a) {
      return newsItemHtml(Object.assign({}, a, { source: "" }), '<span class="sym-chip">' + esc(a.source) + '</span>');
    }).join("") : '<div class="news-empty">Aucun communiqué disponible.</div>';
    fillSrc("newsBankSrc", ["news_bce", "news_fed", "news_boe"]);
  }

'''
html = html[:start] + NEW_JS.replace("__MARKET_DATA__", market_js) + html[end:]

# Note de source sous le tableau inflation (nouvel élément).
once('      <div class="methodology-note" id="macroCpiNote" style="margin-top:8px;"></div>',
     '      <div class="methodology-note" id="macroCpiNote" style="margin-top:8px;"></div>\n'
     '      <div class="src-line" id="macroCpiNote2"></div>', "note source inflation")

# Note des sources de l'onglet Macro.
html, n = re.subn(r'(    if \(srcNote\) srcNote\.textContent =\n      )"[^\n]*";',
                  lambda m: m.group(1) + '"Banques centrales (cartes) : recherche web hebdomadaire, sites officiels + presse financière. '
                  'Taux 10 ans : relevés chaque soir (IBKR pour les US, tradingeconomics.com pour les autres pays). '
                  'Taux de dépôt BCE, inflation et chômage US/zone euro/Allemagne/France/Espagne/Italie : automatiques chaque soir '
                  '(Source : BCE, Source : Eurostat, Source : U.S. Bureau of Labor Statistics). Royaume-Uni et Japon : relevé manuel.";',
                  html, count=1)
if n != 1:
    sys.exit("ÉCHEC note sources macro")

open(out_path, "w", encoding="utf-8").write(html)
print("OK", len(html))
