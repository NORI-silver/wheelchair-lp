// アクセス解析：見られたページ数と、電話・公式サイトへのリンクが押された数を集計する（入力内容などは送らない）。
// 本番の wheelchair.shiokonbu.com 以外（手元での確認など）では何もしない。
(function(){
  var ID = "G-ZYX17VBTWB";
  if (!ID || location.hostname !== "wheelchair.shiokonbu.com") return;
  window.dataLayer = window.dataLayer || [];
  window.gtag = function(){ dataLayer.push(arguments); };
  gtag("js", new Date());
  gtag("config", ID);
  var s = document.createElement("script"); s.async = true;
  s.src = "https://www.googletagmanager.com/gtag/js?id=" + ID;
  document.head.appendChild(s);
  // 送客の計測：事業者への電話・外部サイトのクリック
  document.addEventListener("click", function(e){
    var a = e.target.closest && e.target.closest("a[href]");
    if (!a) return;
    var href = a.getAttribute("href");
    if (href.indexOf("tel:") === 0) {
      gtag("event", "provider_call", {link_text: a.textContent.trim().slice(0,60), page_path: location.pathname});
    } else if (a.hostname && a.hostname !== location.hostname) {
      gtag("event", "provider_site", {link_domain: a.hostname, page_path: location.pathname});
    }
  });
})();
