// アクセス解析：見られたページ数と、電話・公式サイトへのリンクが押された数を集計する（入力内容などは送らない）。
// 本番の wheelchair.shiokonbu.com 以外（手元での確認など）では何もしない。
(function(){
  // 2つに送る（Nori 2026-11-03）：shiokonbu.com 総合（サブドメインも全部入る）と、wheelchair.shiokonbu.com だけのプロパティ。
  var IDS = ["G-ZYX17VBTWB", "G-6332JJ4PDX"]; // 1つ目＝shiokonbu.com 総合（消さない）、2つ目＝wheelchair だけ
  IDS = IDS.filter(function(x){ return x; });
  if (!IDS.length || location.hostname !== "wheelchair.shiokonbu.com") return;
  window.dataLayer = window.dataLayer || [];
  window.gtag = function(){ dataLayer.push(arguments); };
  gtag("js", new Date());
  IDS.forEach(function(id){ gtag("config", id); });
  var s = document.createElement("script"); s.async = true;
  s.src = "https://www.googletagmanager.com/gtag/js?id=" + IDS[0];
  document.head.appendChild(s);
  // 送客の計測：事業者への電話・外部サイトのクリック
  document.addEventListener("click", function(e){
    var a = e.target.closest && e.target.closest("a[href]");
    if (!a) return;
    var href = a.getAttribute("href");
    // どの事業者への送客か（提携事業者への紹介件数の照合に使う）
    var card = a.closest(".provider");
    var provider = card ? (card.getAttribute("data-provider") || "") : "";
    var partner = card && card.classList.contains("partner") ? "yes" : "no";
    if (href.indexOf("tel:") === 0) {
      gtag("event", "provider_call", {link_text: a.textContent.trim().slice(0,60), page_path: location.pathname, provider: provider, partner: partner});
    } else if (a.hostname && a.hostname !== location.hostname) {
      gtag("event", "provider_site", {link_domain: a.hostname, page_path: location.pathname, provider: provider, partner: partner});
    }
  });
})();
