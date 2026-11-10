# 毎日のSEO担当（wheelchair.shiokonbu.com）

Nori さん 2026-11-10「全部担当つけて」により、毎日1回このサイトのSEOを1つずつ良くする担当（定期作業「wheelchair SEO 毎日の改善」）を置く。ルールの正本は [AGENTS.md](../AGENTS.md) と [seo-playbook.md](seo-playbook.md)。この手順と食い違うときは、そちらが優先（マージの扱いも AGENTS.md に従う）。

利用上限はアカウント全体で共有なので、読むのは AGENTS.md・この手順・seo-playbook.md・`docs/seo-log.md` の最後の10行・直すページの元ファイルだけ。

## 1回の手順
1. `main` を取り込む。開いているSEOのPRがあれば先に片付ける（SEO check が赤なら直す）。2本以上残っていたら新しい作業はしない。
2. 最新の `main` が公開されているか確かめる（Actions の pages の結果、または本番の title）。止まっていたら原因を調べる。
3. `python3 tools/seo_check.py .` の NG を最優先で直す。
4. 数字を見る（1日1回）：SHIOKONBU_SEO の `gsc_query`／`gsc_opportunities`（site=wheelchair）で直近28日の表示・クリック・順位、`ga_report`（site=wheelchair）で `provider_site`・`provider_call`。取れないときは推測せず「未取得」とログに書く。
5. 改善は1つだけ。選ぶ順（Nori さん 2026-11-10 承認の優先順位。定期作業の文面と食い違うときはこちら）：
   1. 表示はあるのにクリック0で、平均順位8〜20くらいのページ → `gsc_query`（dimensions page と query）でそのページの検索語を見て、title・description・冒頭の答えをその検索語に合わせて書き直す
   2. そのページの検索語に本文で答えていない → 足りない問い・情報を本文とよくある質問に足す
   3. 順位11〜20のページ → 上位にあって自ページにない情報を足して強める
   4. 強いページから弱いページへの内部リンク
   5. 上のどれもないとき：表示がゼロの index ページ（内部リンク・title の語・sitemap を見直す）→ [seo/keyword-map.csv](seo/keyword-map.csv) の `page_action` が「既存改善候補」「既存拡充候補」の行を優先度 S → A の順 → seo_check の WARN（title・description の長さ）
   - 新しいページは計画どおりでよいが、質を先にする。順位が下がっても慌ててページを消したり作り直したりしない。seo-log には「どのページを・どの検索語に合わせたか」を書く。
6. `content/` を直して `python3 tools/build.py` → `python3 tools/seo_check.py .`（NG 0）→ `main` から新しいブランチで PR（題名は `[B] SEO：…`）。`docs/seo-log.md` に1行足す。
7. SEO check が緑ならマージし、本番に出たのを確かめる（AGENTS.md）。変更の効果は14日以上たってから同じ表で判定し、ログに追記する。

## しないこと
- 事業者への連絡・外部への送信、`data/areas.json` の手での編集（正本は wheelchair-db）、地域ページの新規追加（index 条件は seo-playbook 3章）。
- 新しい記事の量産。新規ページは keyword-map で「新規候補」で、一次情報と業者への導線がそろうときだけ、1本ずつ。
- 公式に確認できない料金・対応地域・営業時間を書くこと。危険な作業を勧めること（seo-playbook 4章）。
- 直近14日以内に直したページを、数字を見ずにまた直すこと。

## 報告
マージして公開を確かめたとき、または Nori さんの確認・手が要るときだけ、担当スレッドに1〜2行（何を・なぜ・PRリンク）。それ以外は報告しない。
