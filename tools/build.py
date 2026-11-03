"""content/ の各ページ（先頭にJSONのメタ情報、"---" の行の後に本文HTML）から、
共通のヘッダー・フッター・構造化データ付きの index.html と sitemap.xml を作る。
使い方: python3 tools/build.py
"""
import json,sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
BASE="https://wheelchair.shiokonbu.com"
def jdate(d):
    y,mo,da=d.split("-")
    return f"{int(y)}年{int(mo)}月{int(da)}日"

def wrap(m,body):
    crumbs=[("ホーム","/")]+m["crumbs"]
    bc_html=" › ".join(f'<a href="{u}">{n}</a>' for n,u in crumbs[:-1])+(" › " if len(crumbs)>1 else "")+crumbs[-1][0]
    bc_ld={"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":i+1,"name":n,"item":BASE+u} for i,(n,u) in enumerate(crumbs)]}
    art_ld={"@context":"https://schema.org","@type":"Article","headline":m["h1"],"dateModified":m["updated"],"datePublished":m["updated"],"publisher":{"@type":"Organization","name":"車いす修理ナビ"},"mainEntityOfPage":BASE+m["path"]}
    return f'''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="google-site-verification" content="MmM3OGz9LIPxBOmE4jR8GdP4vACP_FrchZwBLT3W0sM" />
<title>{m["title"]}</title>
<meta name="description" content="{m["desc"]}">
<link rel="canonical" href="{BASE}{m["path"]}">
<meta property="og:type" content="article">
<meta property="og:title" content="{m["title"]}">
<meta property="og:description" content="{m["desc"]}">
<meta property="og:url" content="{BASE}{m["path"]}">
<meta property="og:site_name" content="車いす修理ナビ">
<link rel="stylesheet" href="/assets/style.css">
<script src="/assets/ga.js" defer></script>
<script type="application/ld+json">{json.dumps(bc_ld,ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(art_ld,ensure_ascii=False)}</script>
</head>
<body>
<header class="site"><div class="wrap"><a href="/">車いす修理ナビ｜車いすの出張修理を探す</a></div></header>
<main class="wrap">
{f'<nav class="crumbs" aria-label="パンくず">{bc_html}</nav>' if len(crumbs)>1 else ""}
<h1>{m["h1"]}</h1>
<p class="updated">最終更新：{jdate(m["updated"])}</p>
{body}
</main>
<footer class="site"><div class="wrap">
<p>掲載している事業者の情報は、各社の公式サイトなどで確認した時点のものです。対応可否・料金・来られる日時は、必ず事業者に直接ご確認ください。誤りの訂正は運営までお知らせください。</p>
<p>車いす修理ナビ</p>
</div></footer>
</body>
</html>
'''
def build():
    root=pathlib.Path(__file__).resolve().parent.parent
    urls=[]
    for src in sorted((root/"content").rglob("*.html")):
        head,body=src.read_text().split("\n---\n",1)
        m=json.loads(head)
        out=root/m["path"].strip("/")/"index.html" if m["path"]!="/" else root/"index.html"
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(wrap(m,body))
        if not m.get("noindex"):
            urls.append((m["path"],m["updated"]))
        print("built",out.relative_to(root))
    import areas
    for m,body in areas.pages(root):
        out=root/m["path"].strip("/")/"index.html"
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(wrap(m,body))
        urls.append((m["path"],m["updated"]))
        print("built",out.relative_to(root))
    sm=['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm+=[f"  <url><loc>{BASE}{u}</loc><lastmod>{d}</lastmod></url>" for u,d in urls]
    sm.append("</urlset>")
    (root/"sitemap.xml").write_text("\n".join(sm)+"\n")

if __name__=="__main__":
    build()
