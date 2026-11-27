# LYTORA MVP — 無料スタート手順

## このパッケージに入っているもの
- `index.html`: iPhone / PC対応のニュース画面
- `collect.py`: RSSと国別Google News RSSを取得する収集プログラム
- `sources.json`: 地域別フィードと重点国リスト
- `.github/workflows/collect.yml`: GitHub Actionsで3時間ごとに自動収集する設定
- `data/articles.json`: 収集結果の保存先（初回実行で生成）

## 重要な注意
これは実際のニュース記事をRSSから収集するMVPです。自動収集された記事は公開前に人が確認してください。見出し・短い説明・出典リンクの表示を想定し、記事本文の転載はしません。Google News RSSの利用条件や各配信元の利用規約・著作権表示条件を確認してください。BBCのフィードは個人利用と商用利用で条件が異なる場合があります。商用公開前に各社の許諾・利用条件を確認してください。
自動翻訳・日本との関連性の評価・10〜15本への編集選定はまだ自動化していません。誤訳や誤った関連付けを避けるため、編集確認の工程を残しています。

## 公開までの手順（無料枠を利用）
1. GitHubアカウントを作成 / ログイン。
2. 新しいPublic repositoryを作成（例: `lytora-news`）。
3. このZIPの中身をすべてリポジトリ直下へアップロードしてCommit。
4. リポジトリの `Actions` を開き、ワークフロー実行を許可。
5. `Actions` → `Collect LYTORA news` → `Run workflow` を押して初回収集。
6. `Settings` → `Pages` → `Deploy from a branch` → `main` / `/(root)` を選んで保存。
7. 数分後に表示されるGitHub Pages URLをiPhone / PCで開く。

## ローカルで収集テスト
Python 3.10以上で:
```bash
python collect.py
```
RSS取得ができれば `data/articles.json` が生成されます。

## いまの仕様
- 3時間ごとに自動実行（GitHub Actionsのスケジュール。遅延する場合あり）
- BBC地域別RSS / Al Jazeera / Guardian World / 国別Google News RSS
- 重点国は `sources.json` で追加・変更可能
- 同じURLの重複を簡易除去
- 最大100件を画面表示
- 画面は原文見出しと配信元の短い要約を表示

## 次に必要な開発
1. 日本語翻訳と要約（翻訳API等の費用・利用条件を確認してから）
2. 事実確認 / 日本との関連性 / 国の偏りを評価する編集画面
3. 1日10〜15本に絞る編集ワークフロー
4. 商用利用条件・ブランド名・ドメイン・アプリストア審査の確認
