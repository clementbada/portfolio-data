// Test de fumée : charge le dashboard patché dans jsdom, sans IBKR (aperçu statique),
// vérifie l'absence d'erreur, l'onglet Actus et l'onglet Macro.
const fs = require("fs");
const { JSDOM, VirtualConsole } = require("jsdom");
const html = fs.readFileSync(process.argv[2], "utf8");
const errors = [];
const vc = new VirtualConsole();
vc.on("jsdomError", (e) => errors.push("jsdomError: " + (e.message || e)));
vc.on("error", (e) => errors.push("console.error: " + e));
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, virtualConsole: vc,
  beforeParse(w) { w.addEventListener("error", (ev) => errors.push("window.error: " + ev.message)); } });
const w = dom.window, d = w.document;
setTimeout(() => {
  const out = {};
  d.getElementById("tabBtnMacro").click();
  out.ratesRows = d.querySelectorAll("#macroRatesBody tr").length;
  out.ratesFirst = d.querySelector("#macroRatesBody tr").textContent.replace(/\s+/g, " ").trim();
  out.ratesFR = [...d.querySelectorAll("#macroRatesBody tr")].map(t => t.textContent.replace(/\s+/g, " ").trim()).find(t => t.includes("France"));
  out.cpiRows = [...d.querySelectorAll("#macroCpiBody tr")].map(t => t.textContent.replace(/\s+/g, " ").trim());
  out.cpiSrc = d.getElementById("macroCpiNote2").textContent;
  out.ratesNote = d.getElementById("macroRatesNote").textContent.slice(0, 160);
  d.getElementById("tabBtnNews").click();
  out.newsVisible = !d.getElementById("viewNews").hidden && d.getElementById("viewMacro").hidden;
  out.newsPf = d.querySelectorAll("#newsPortfolioList .news-item").length;
  out.newsBank = d.querySelectorAll("#newsBankList .news-item").length;
  out.symButtons = d.querySelectorAll("#newsSymRow button").length;
  // filtre PEA
  [...d.querySelectorAll("#newsEnvRow button")].find(b => b.textContent === "PEA").click();
  out.newsPEA = d.querySelectorAll("#newsPortfolioList .news-item").length;
  out.peaChips = [...new Set([...d.querySelectorAll("#newsPortfolioList .sym-chip")].map(c => c.textContent))];
  // filtre BCE
  [...d.querySelectorAll("#newsBankRow button")].find(b => b.textContent === "BCE").click();
  out.bankBCE = d.querySelectorAll("#newsBankList .news-item").length;
  out.firstBank = d.querySelector("#newsBankList .news-title") && d.querySelector("#newsBankList .news-title").textContent;
  out.newsSrc = d.getElementById("newsPortfolioSrc").textContent;
  out.links = [...d.querySelectorAll(".news-title")].every(a => a.href.startsWith("https://") && a.target === "_blank");
  // retour aux autres onglets
  d.getElementById("tabBtnPortfolio").click();
  out.portfolioBack = !d.getElementById("viewPortfolio").hidden && d.getElementById("viewNews").hidden;
  out.posRows = d.querySelectorAll("#posBody tr").length;
  d.getElementById("tabBtnPerf").click();
  out.perfRows = d.querySelectorAll("#perfTableBody tr").length;
  const text = d.body.textContent;
  out.badText = ["NaN", "undefined", "[object Object]"].filter(t => {
    const vis = [...d.querySelectorAll(".view")].map(v => v.textContent).join(" ");
    return vis.includes(t);
  });
  out.errors = errors;
  console.log(JSON.stringify(out, null, 1));
  process.exit(errors.length || out.badText.length ? 1 : 0);
}, 2500);
