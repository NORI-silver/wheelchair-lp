"""data/areas.json（wheelchair-db の export_pages.py が書き出す）から地域ページを作る。
build.py から呼ばれる。中身は公開情報だけ。対応可否・料金・来られる日時は事業者に確認するよう必ず書く。
"""
import html
import json
import pathlib

E = html.escape
CONTACT = {"phone": "電話", "web_form": "フォーム", "email": "メール", "fax": "FAX", "line": "LINE"}
KEY_COND = [("onsite", "出張修理"), ("individual", "個人宅"), ("same_day", "当日対応"), ("weekend", "土日対応"),
            ("other_store", "他店購入品"), ("any_maker", "メーカー不問")]
MARK = {"yes": "○", "conditional": "△", "no": "×", None: "要確認", "unknown": "要確認"}


def yen(n):
    return f"{n:,}円"


def cap(p, key, code):
    for c in p[key]:
        if c["code"] == code:
            return c["level"]
    return None


def fee_text(p):
    f = p.get("area_travel_fee")
    if f and f.get("min") is not None:
        t = "無料" if f["min"] == 0 and (f["max"] or 0) == 0 else (yen(f["min"]) if f["min"] == f["max"] else f"{yen(f['min'])}〜{yen(f['max'])}")
        return t + (f"（料金表の区分{E(f['zone'])}）" if f.get("zone") else "")
    if p.get("travel_fee_notes"):
        return E(p["travel_fee_notes"][0]) + "（この地域の金額は要確認）"
    return "公式サイトに記載なし（要確認）"


PARTNER_LABEL = "提携事業者（紹介手数料あり）"


def partner_first(ps):
    """提携事業者を同じ一覧の先頭に出す（表示には必ず「提携事業者（紹介手数料あり）」を付ける）。"""
    return sorted(ps, key=lambda p: not p.get("partner"))


def partner_block(p):
    pt = p.get("partner")
    if not pt:
        return ""
    rows = []
    if pt.get("same_day"):
        rows.append(("当日対応", E(pt["same_day"])))
    if pt.get("lead_time"):
        rows.append(("来られる目安", E(pt["lead_time"])))
    if pt.get("note"):
        rows.append(("事業者から", E(pt["note"])))
    extra = "".join(f"<li>{k}：{v}（事業者回答 {E(pt.get('answered_at') or '')}）</li>" for k, v in rows)
    return (f'<p class="badge">{PARTNER_LABEL}</p>'
            + (f"<ul>{extra}</ul>" if extra else "")
            + '<p class="mention">電話の際は「車いす修理ナビを見た」とお伝えいただくとスムーズです。</p>')


def card(p, local=True):
    prods = [c["label"] for c in p["products"] if c["level"] == "yes"]
    reps = [c["label"] for c in p["repairs"] if c["level"] == "yes"]
    conds = " ／ ".join(f"{lab}{MARK.get(cap(p, 'conditions', code), '要確認')}" for code, lab in KEY_COND)
    contact = []
    if p.get("phone"):
        contact.append(f'<a href="tel:{E(p["phone"].replace("-", ""))}">{E(p["phone"])}</a>')
    if p.get("website"):
        contact.append(f'<a href="{E(p["website"])}" rel="nofollow noopener" target="_blank">公式サイト</a>')
    methods = "・".join(CONTACT.get(m, m) for m in p.get("contact_methods", []))
    prices = "".join(f"<li>{E(x['item'] or '')}：{yen(x['price_jpy'])}{'（出張費込み）' if x.get('includes_travel') else ''}</li>"
                     for x in p.get("price_items", [])[:4] if x.get("price_jpy"))
    src = p["sources"][0]["url"] if p.get("sources") else p.get("website")
    rows = [
        ("この地域への出張費" if local else "出張費", fee_text(p)),
        ("対応する車いす", "、".join(prods) or "要確認"),
        ("修理内容（記載あり）", "、".join(reps) or "公式サイトに詳しい記載なし"),
        ("対応条件", conds),
        ("営業時間", E(p.get("hours_text") or "公式サイトに記載なし")),
        ("問い合わせ", " ／ ".join(contact) + (f"（{methods}）" if methods else "")),
    ]
    if p.get("tax_basis"):
        rows.insert(1, ("料金の税表示", E(p["tax_basis"])))
    if p.get("credentials"):
        rows.append(("資格・認定", E("、".join(p["credentials"]))))
    body = "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in rows)
    pr = f"<p>公開されている料金の例</p><ul>{prices}</ul>" if prices else ""
    reason = f'<p class="updated">{E(p["area_reason"])}</p>' if p.get("area_reason") else ""
    cls = "provider partner" if p.get("partner") else "provider"
    return (f'<section class="{cls}" data-provider="{E(p.get("slug") or "")}"><h3>{E(p["name"])}</h3>{partner_block(p)}{reason}<div class="table"><table>{body}</table></div>{pr}'
            f'<p class="updated">最終確認：{E(p.get("last_verified_at") or "—")}（<a href="{E(src or "")}" rel="nofollow noopener" target="_blank">出典</a>）</p></section>')


def city_page(c, all_cities):
    pref, city = c["prefecture"], c["city"]
    ps = c["providers"]
    n_ind = sum(1 for p in ps if cap(p, "conditions", "individual") == "yes")
    n_elec = sum(1 for p in ps if cap(p, "products", "electric_wheelchair") == "yes")
    fees = [p["area_travel_fee"]["min"] for p in ps if p.get("area_travel_fee") and p["area_travel_fee"].get("min") is not None]
    fee_line = ""
    if fees:
        fee_line = f"出張費を地域別に公開している業者では、{E(city)}への出張費は{('無料' if min(fees) == 0 else yen(min(fees)))}からです。"
    names = "、".join(E(p["name"]) for p in ps)
    neighbors = [x for x in all_cities if x["prefecture"] == pref and x["city"] != city]
    nb = "".join(f'<li><a href="/repair/{x["pref_slug"]}/{x["city_slug"]}/">{E(x["city"])}の車いす出張修理</a></li>' for x in neighbors)
    confirm = "".join(f'<li>{E(p["name"])}（{E(p.get("area_reason") or "")}）</li>' for p in c["to_confirm"])
    offices = "".join(f'<li>{E(o.get("name") or "")}{(" " + E(o["phone"])) if o.get("phone") else ""}</li>' for o in c["municipal_offices"])
    elec_note = ("電動車いすに対応すると明記しているのは" + f"{n_elec}社です。" if n_elec else
                 "この中に電動車いすへの対応を明記している業者はありません。電動の方は<a href=\"/repair/electric/\">電動車いすの修理</a>をご覧ください。")
    body = f'''<div class="answer">
<p><strong>{E(city)}に出張して車いすを修理してくれる業者は、確認できた範囲で{len(ps)}社です。</strong></p>
<p>{names}。うち個人宅への対応を明記しているのは{n_ind}社です。{fee_line}{elec_note}</p>
</div>
<p class="note">各社の公式サイトで確認した情報です（最終確認日は各社の欄）。対応できるか、料金、来られる日時は、必ず電話などで直接確かめてください。</p>

<h2>{E(city)}に来てくれる車いす出張修理業者</h2>
{"".join(card(p) for p in partner_first(ps))}

<h2>ほかに対応の可能性がある業者（要確認）</h2>
<p>対応地域や出張の可否が公式サイトだけでは確かめきれなかった業者です。</p>
<ul>{confirm or "<li>現在ありません</li>"}</ul>

<h2>介護保険・補装具の車いすを使っている方へ</h2>
<p>介護保険でレンタルしている車いすは、まずレンタル事業者かケアマネジャーに連絡してください。障害者手帳の補装具で作った車いすは、修理も補装具費の対象なので、{E(city)}の障害福祉の窓口に先に相談するのが確実です。くわしくは<a href="/guide/broken-wheelchair/">車いすが壊れたときの依頼先</a>へ。</p>
{f"<ul>{offices}</ul>" if offices else ""}

<h2>料金の目安</h2>
<p>パンク修理は出張費込みで片側6,000円前後、タイヤとチューブの交換は1台1.5〜2万円台が目安です。業者ごとの比較は<a href="/repair/puncture/">パンク修理・タイヤ交換の料金相場</a>にまとめています。</p>

<h2>近くの地域から探す</h2>
<ul>{nb}<li><a href="/repair/{c["pref_slug"]}/">{E(pref)}の車いす出張修理</a></li></ul>
'''
    meta = {"path": f"/repair/{c['pref_slug']}/{c['city_slug']}/",
            "title": f"{city}の車いす出張修理｜自宅に来てくれる{len(ps)}社と出張費",
            "desc": f"{city}で車いす（車椅子）を自宅まで修理に来てくれる業者{len(ps)}社を、出張費・対応する車いす・個人宅対応・営業時間で比べられます。パンク修理やタイヤ交換の料金の目安と、最終確認日つきの連絡先をまとめました。",
            "h1": f"{city}の車いす出張修理（自宅まで来てくれる業者）",
            "updated": max(p.get("last_verified_at") or "" for p in ps) or None,
            "crumbs": [["地域から探す", "/repair/"], [pref, f"/repair/{c['pref_slug']}/"], [city, f"/repair/{c['pref_slug']}/{c['city_slug']}/"]]}
    return meta, body


def pref_page(pf, all_cities):
    pref = pf["prefecture"]
    ps = sorted(pf["providers"], key=lambda p: (not p.get("partner"), not p["whole_prefecture"], p["name"]))
    whole = [p for p in ps if p["whole_prefecture"]]
    cities = [x for x in all_cities if x["prefecture"] == pref]
    cl = "".join(f'<li><a href="/repair/{x["pref_slug"]}/{x["city_slug"]}/">{E(x["city"])}</a>（{len(x["providers"])}社）</li>' for x in cities)

    def cov(p):
        if p["whole_prefecture"]:
            return f"{E(pref)}全域"
        cs = p["cities"]
        return E("、".join(cs[:12])) + (f" ほか{len(cs) - 12}市区町村" if len(cs) > 12 else "")
    cards = "".join(card(dict(p, area_reason="対応地域：" + cov(p)), local=False) for p in ps)
    body = f'''<div class="answer">
<p><strong>{E(pref)}で車いすの出張修理をしている業者は、確認できた範囲で{len(ps)}社です。</strong></p>
<p>うち{E(pref)}全域を対応地域にしているのは{len(whole)}社です。ほかの業者は対応する市区町村が決まっているので、ご自宅が入っているか各社の欄で確かめてください。</p>
</div>
<p class="note">各社の公式サイトで確認した情報です。対応できるか、料金、来られる日時は、必ず直接確かめてください。</p>
{f"<h2>市区町村から探す</h2><ul>{cl}</ul>" if cl else ""}
<h2>{E(pref)}の車いす出張修理業者</h2>
{cards}
<h2>壊れたときに最初にすること</h2>
<p>介護保険でレンタルしている車いすはレンタル事業者へ、補装具で作った車いすは市区町村の窓口へ先に連絡します。くわしくは<a href="/guide/broken-wheelchair/">車いすが壊れたときの依頼先</a>へ。</p>
'''
    meta = {"path": f"/repair/{pf['pref_slug']}/",
            "title": f"{pref}の車いす出張修理｜自宅に来てくれる{len(ps)}社",
            "desc": f"{pref}で車いす（車椅子）の出張修理をしている業者{len(ps)}社を、対応地域・出張費・対応する車いす・営業時間で比べられます。市区町村別のページと、最終確認日つきの連絡先をまとめました。",
            "h1": f"{pref}の車いす出張修理（自宅まで来てくれる業者）",
            "updated": max(p.get("last_verified_at") or "" for p in ps),
            "crumbs": [["地域から探す", "/repair/"], [pref, f"/repair/{pf['pref_slug']}/"]]}
    return meta, body


def index_page(data):
    pl = ""
    for pf in data["prefectures"]:
        cs = "、".join(f'<a href="/repair/{c["pref_slug"]}/{c["city_slug"]}/">{E(c["city"])}</a>' for c in data["cities"] if c["prefecture"] == pf["prefecture"])
        pl += f'<li><a href="/repair/{pf["pref_slug"]}/">{E(pf["prefecture"])}</a>（{len(pf["providers"])}社）{"：" + cs if cs else ""}</li>'
    body = f'''<div class="answer"><p><strong>近くで車いす（車椅子）の修理先を探すなら、まずお住まいの都道府県・市区町村を選んでください。</strong></p>
<p>自宅への出張対応地域・出張費・対応する車いすを比べ、各社の電話・公式サイトから問い合わせできます。掲載地域は東京都・千葉県・神奈川県・埼玉県です。</p></div>
<p class="note">現在地からの距離順や、当日の空き状況を表示する一覧ではありません。近くに拠点があるかだけでなく、自宅が出張対応地域に入るかを確認してください。掲載地域以外の方は<a href="/guide/broken-wheelchair/">車いすが壊れたときの依頼先</a>をご覧ください。</p>
<a class="cta" href="#areas">近くの出張修理業者を地域から探す</a>
<h2 id="areas">お住まいの都道府県・市区町村を選ぶ</h2><ul>{pl}</ul>
<h2>修理を問い合わせるまでの3ステップ</h2>
<ol>
<li><strong>自宅の地域を選ぶ。</strong>市区町村が一覧になければ、都道府県ページで各社の対応地域を確認してください。</li>
<li><strong>条件を比べる。</strong>個人宅への出張、手動・電動の対応、修理内容、出張費を各社の欄で確認します。「要確認」の項目は直接問い合わせてください。</li>
<li><strong>電話・公式サイトから相談する。</strong>メーカー・機種名、故障の症状、市区町村、希望日時を伝え、対応可否・修理代と出張費の総額・来られる日時を確かめてから依頼してください。</li>
</ol>
<p>出張対応地域や料金の条件は各社で異なります。たとえば<a href="https://bfserv.co.jp/area_prices/wheelchair/">バイシクルフィールドサービスの公式料金表</a>と<a href="https://www.ccar.tv/unit_price/index.html">オーデンの公式料金表</a>で、それぞれの条件を確認できます（2026年11月3日確認）。</p>
<p>依頼先に迷う場合は<a href="/guide/broken-wheelchair/">入手方法別の最初の連絡先</a>、費用を確認したい場合は<a href="/guide/repair-cost/">車いすの修理費用</a>をご覧ください。</p>
<h2>症状から探す</h2><ul><li><a href="/repair/puncture/">パンク修理・タイヤ交換</a></li><li><a href="/repair/caster/">キャスター（前輪）交換</a></li><li><a href="/guide/maintenance/">点検・メンテナンス</a></li><li><a href="/repair/electric/">電動車いすの修理</a></li><li><a href="/repair/brake/">ブレーキが効かない</a></li><li><a href="/guide/broken-wheelchair/">どこに頼めばいいか分からない</a></li></ul>
'''
    meta = {"path": "/repair/", "title": "近くの車いす修理・出張修理を探す｜東京・千葉・神奈川・埼玉",
            "desc": "近くの車いす（車椅子）修理先を探す方へ。東京・千葉・神奈川・埼玉の出張修理業者を地域から選び、対応する車いす・修理内容・出張費・個人宅対応を確認。各社の電話・公式サイトから問い合わせできます。",
            "h1": "近くの車いす修理・出張修理を地域から探す", "updated": max(data["generated_at"], "2026-11-03"), "crumbs": [["地域から探す", "/repair/"]]}
    return meta, body


def pages(root):
    path = pathlib.Path(root) / "data" / "areas.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    out = [index_page(data)]
    out += [pref_page(p, data["cities"]) for p in data["prefectures"]]
    out += [city_page(c, data["cities"]) for c in data["cities"]]
    return out


def providers_for(root, repairs, products=None):
    """症状ページ用：指定の修理内容（どれか）を公式サイトに明記している業者の一覧HTML。
    本文中の <!--providers:puncture,tire--> を build.py がこれで置き換える。"""
    path = pathlib.Path(root) / "data" / "areas.json"
    if not path.exists():
        return ""
    data = json.loads(path.read_text())
    seen = {}
    for pf in data["prefectures"]:
        for p in pf["providers"]:
            q = seen.setdefault(p["slug"], dict(p, prefs=[]))
            q["prefs"].append((pf["prefecture"], pf["pref_slug"]))
    hit = [p for p in seen.values() if any(cap(p, "repairs", r) == "yes" for r in repairs)
           and (not products or any(cap(p, "products", x) == "yes" for x in products))]
    if not hit:
        return ""
    rows = ""
    for p in sorted(hit, key=lambda p: p["name"]):
        labs = "、".join(c["label"] for c in p["repairs"] if c["level"] == "yes" and c["code"] in repairs)
        area = "・".join(f'<a href="/repair/{s}/">{E(n)}</a>' for n, s in p["prefs"])
        contact = []
        if p.get("phone"):
            contact.append(f'<a href="tel:{E(p["phone"].replace("-", ""))}">{E(p["phone"])}</a>')
        if p.get("website"):
            contact.append(f'<a href="{E(p["website"])}" rel="nofollow noopener" target="_blank">公式サイト</a>')
        rows += (f'<tr><td><strong>{E(p["name"])}</strong><br><span class="updated">最終確認：{E(p.get("last_verified_at") or "—")}</span></td>'
                 f'<td>{labs}</td><td>{area}</td><td>{" ／ ".join(contact) or "要確認"}</td></tr>')
    return (f'<div class="table"><table><tr><th>業者</th><th>記載のある作業</th><th>出張先（詳しくは地域ページ）</th><th>問い合わせ</th></tr>{rows}</table></div>'
            '<p class="note">各社の公式サイトに作業の記載がある業者だけを載せています（掲載順は名前順）。ご自宅が対応地域に入るか、機種に対応できるか、料金と来られる日時は、必ず直接確かめてください。</p>')
