"""公開前のSEOチェック。PR ごとに GitHub Actions（.github/workflows/seo-check.yml）でも動く。
使い方: python3 tools/seo_check.py [リポジトリの場所]
NG があれば終了コード 1。注意（WARN）は止めない。
見ること：
- build.py を流し直しても index.html・sitemap.xml が変わらないこと（content/ を直したのに生成し忘れ、を防ぐ）
- 各ページの title・description・canonical・h1・Google のサイト確認タグ・GA の読み込み
- sitemap.xml のURLとページの一致（noindex のページは載せない、載っているページは存在する）
- サイト内リンク（/ で始まるもの）の行き先が存在すること
- 秘密情報らしき文字列が公開ファイルにないこと
"""
import pathlib, re, subprocess, sys, html

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
BASE = "https://wheelchair.shiokonbu.com"
ng, warn = [], []

# 1. 生成物が最新か
before = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True).stdout
subprocess.run([sys.executable, str(root / "tools" / "build.py")], cwd=root, check=True, capture_output=True)
after = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True).stdout
if before != after:
    changed = sorted(set(after.splitlines()) - set(before.splitlines()))
    ng.append("build.py の生成物が最新ではありません（python3 tools/build.py を流してコミット）: " + ", ".join(changed[:8]))

# 2. ページごと
pages = {}
for f in sorted(root.rglob("index.html")):
    if ".git" in f.parts or "content" in f.relative_to(root).parts[:1]:
        continue
    rel = "/" + str(f.parent.relative_to(root)).strip(".") + "/"
    rel = "/" if rel in ("//", "/./") else rel.replace("//", "/")
    pages[rel] = f.read_text()

def one(pattern, text):
    m = re.search(pattern, text, re.S)
    return html.unescape(m.group(1).strip()) if m else None

for path, t in pages.items():
    noindex = 'name="robots" content="noindex"' in t
    title = one(r"<title>(.*?)</title>", t)
    desc = one(r'<meta name="description" content="(.*?)">', t)
    canon = one(r'<link rel="canonical" href="(.*?)">', t)
    h1s = re.findall(r"<h1[ >]", t)
    if not title:
        ng.append(f"{path}: title がない")
    elif not noindex and not (20 <= len(title) <= 45):
        warn.append(f"{path}: title {len(title)}字（目安28〜35字）")
    if not desc:
        ng.append(f"{path}: description がない")
    elif not noindex and not (60 <= len(desc) <= 140):
        warn.append(f"{path}: description {len(desc)}字（目安80〜120字）")
    if canon != BASE + path:
        ng.append(f"{path}: canonical が {canon}（{BASE + path} のはず）")
    if len(h1s) != 1:
        ng.append(f"{path}: h1 が {len(h1s)} 個")
    if "google-site-verification" not in t:
        ng.append(f"{path}: Search Console の確認タグがない")
    if "/assets/ga.js" not in t:
        ng.append(f"{path}: GA（/assets/ga.js）を読み込んでいない")
    for href in set(re.findall(r'href="(/[^"#?]*)', t)):
        target = root / href.strip("/")
        if href.startswith("/assets/") or href in ("/",):
            ok = target.exists() or href == "/"
        else:
            ok = (target / "index.html").exists() or target.is_file()
        if not ok:
            ng.append(f"{path}: リンク切れ {href}")

# 3. sitemap
sm = (root / "sitemap.xml").read_text()
locs = [l.replace(BASE, "") for l in re.findall(r"<loc>(.*?)</loc>", sm)]
for p in locs:
    if p not in pages:
        ng.append(f"sitemap: {p} のページがない")
    elif 'content="noindex"' in pages[p]:
        ng.append(f"sitemap: noindex の {p} が載っている")
for p, t in pages.items():
    if 'content="noindex"' not in t and p not in locs:
        warn.append(f"sitemap: {p} が載っていない（index のページ）")

# 4. 秘密情報らしきもの
SECRET = re.compile(r"(ghp_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_\-]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY|docs\.google\.com/spreadsheets/d/)")
for f in root.rglob("*"):
    if ".git" in f.parts or not f.is_file() or f.suffix not in (".html", ".js", ".json", ".xml", ".css", ".md", ".py", ".csv"):
        continue
    if SECRET.search(f.read_text(errors="ignore")):
        ng.append(f"秘密情報らしき文字列: {f.relative_to(root)}")

for w in warn:
    print("WARN", w)
for n in ng:
    print("NG  ", n)
print(f"ページ {len(pages)}・sitemap {len(locs)}件・NG {len(ng)}・WARN {len(warn)}")
sys.exit(1 if ng else 0)
