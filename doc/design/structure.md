# 構成変更の対応表

[設計書トップ](README.md)

この章は既存処理の配置・分割・ファイル名の整理を記録します。その後の API＋JS 移行は [API＋JS の画面構成](api-client.md) を参照してください。URL、endpoint 名、認証・権限、入力検証、成績の計算式、Firestore の読取・書込先、ローカルファイルの保存先を維持します。設計書に記載した現行の制約・不整合も、今回の構成変更では修正していません。

## Python の分割先

| 旧ファイル | 新しい実装ファイル | 役割 |
| --- | --- | --- |
| `webapp/tenant.py` | `teams/context.py` | チーム情報の取得・リクエスト内キャッシュ・照合・設定 |
| 同上 | `teams/urls.py` | チーム URL ミドルウェア、url_for、画面共通情報 |
| 同上 | `repositories/references.py` | チーム別 Firestore 参照 |
| 同上 | `repositories/players.py` | 名簿取得・背番号ソート・選手 ID 採番 |
| 同上 | `repositories/schedule.py` | 従来予定の読取・保存、poll のトランザクション更新 |
| 同上 | `services/player_view.py` | JSON とチーム名簿を重ねた選手データ |
| 同上 | `services/schedule_view.py` | 従来予定への選手 ID 関連付け、公開予定の投影 |
| `webapp/schedule_poll.py` | `scheduling/common.py` | 列挙値、例外、ID 解析 |
| 同上 | `scheduling/dates.py` | 日付・時刻・文字列処理 |
| 同上 | `scheduling/normalization.py` | poll 全体の正規化 |
| 同上 | `scheduling/people.py` | 回答者リストの設定・表示 |
| 同上 | `scheduling/answers.py` | 日程回答 |
| 同上 | `scheduling/days.py` | 日程の追加・削除 |
| 同上 | `scheduling/games.py` | 試合カード・打順の正規化と更新 |
| 同上 | `scheduling/events.py` | イベントとイベント回答 |
| `routes/misc.py` | `routes/players.py` | 選手登録・編集、画像処理 |
| 同上 | `routes/abilities.py` | パワプロ風能力一覧 |
| 同上 | `routes/meeting.py` | 記録会まとめ |
| `routes/annual_tally.py` | `stats/annual_tally.py` | 年度集計 |
| `routes/annual_tables.py` | `stats/annual_tables.py` | 年度成績表の組み立て |
| `routes/game_detail_batters.py` | `stats/game_batters.py` | 試合の打者集計 |
| `routes/current_year_game.py` | `stats/current_year_game.py` | 当年個人成績の試合集計 |
| `routes/player_detail_form.py` | `stats/player_form.py` | 月別成績・直近の調子 |
| `routes/player_detail_records.py` | `services/player_records.py` | 選手詳細の試合記録取得 |
| `routes/current_year_records.py` | `services/season_records.py` | 試合番号・打席・盗塁の取得 |
| `routes/history_current.py` | `services/player_history.py` | 過去成績への新試合集計の追加 |

表内の `teams/`、`repositories/`、`services/`、`scheduling/`、`routes/`、`stats/` は `webapp/` 配下です。旧 Python モジュールは import の互換入口として残し、新規のアプリ内 import は分割先を参照します。Flask は既存の単一 app インスタンスを使用します。

## 運用スクリプト

| 旧コマンド（引き続き利用可能） | 実装 | 新しい実行方法 |
| --- | --- | --- |
| `python migrate.py` | `scripts/import_csv.py` | `python -m scripts.import_csv` |
| `python upload_csv.py` | `scripts/replace_annual_stats.py` | `python -m scripts.replace_annual_stats` |
| `python -m webapp.create_team ...` | `scripts/create_team.py` | `python -m scripts.create_team ...` |
| `python -m webapp.migrate_team` | `scripts/migrate_team.py` | `python -m scripts.migrate_team` |

CSV は `data/imports/`、認証鍵は `config/credentials/` に配置します。共通の `config/paths.py` が配置を解決するため、ファイル参照は作業ディレクトリに依存しません。運用コマンドはリポジトリ直下から実行してください。

## Vue SPA への移行

フロントエンドは `client/src/` に集約しました。画面は `views/`、共通 UI は `components/`、API 保存・終了処理は `composables/`、共有画面データは `stores/`、日付計算は `scheduling/` に分割します。Vite の出力先は `static/spa/` です。

旧 `client/views/` の Nunjucks テンプレート、`static/app/` の描画ランタイム、`static/vendor/` の Nunjucks、日程の旧 JavaScript 部品・結合ファイル、旧イベント JavaScript、対応する Python ビルドスクリプトは廃止しました。既存の共通 CSS・画像と Python の業務処理は継続しています。

画面遷移は Vue Router、共有状態は Pinia、操作は Vue のイベントとフォームに置き換えます。詳細は [SPA と API の設計](api-client.md) を参照してください。

## ファイル分割時の検証

- 既存196関数・クラスの処理を、import の移動を除いて AST 比較し、一致を確認。
- 日程 JavaScript の関数処理と初期化文の順序を AST 比較し、一致を確認。
- 模擬 DB を使った13件のテストで、認証、リダイレクト、公開画面、JSON API、入力エラー、日付・イベント処理、テンプレート、旧 import・コマンドを確認。
- 分割前後の登録ルート、公開画面 HTML、日程・イベント JSON 応答が一致することを確認。

テストは実 Firestore に接続せず、実認証鍵も読みません。本番データを使った操作・運用スクリプトの実書き込みは検証対象外です。

## ディレクトリ全体の整理

| 配置 | 役割 |
| --- | --- |
| 直下 | README・requirements・Git 設定・app.py・旧運用コマンドの互換入口 |
| `webapp/` | Flask。routes・presentation・services・repositories・teams・scheduling・stats に役割分割 |
| `client/src/` | Vue の画面・部品・API・状態・日付計算 |
| `client/tests/` | Vue / JavaScript のテスト。src の階層に対応 |
| `tests/` | モック DB を使う Python テスト |
| `scripts/` | チーム作成・移行・CSV 取り込みなどの運用処理 |
| `config/paths.py` | アプリと運用スクリプトで共有するパス。DB 接続を行わない |
| `config/credentials/` | Firebase 認証鍵。Git 管理対象外 |
| `data/imports/` | 基本情報・打席・年度成績・測定の入力 CSV |
| `data/reference/` | 従来予定と既存の参考 CSV |
| `var/cache/` | 集計 JSON。既存 RYUNEN データを保持し、チーム別キャッシュも同じ場所に生成 |
| `var/log/` | 実行ログ。Git 管理対象外 |
| `static/` | ビルド済み SPA・CSS・画像。既存 URL と DB の画像パスを維持 |
| `01.doc/design/` | 設計書 |
| `01.doc/assets/` | 参考画像（調子.png） |
| `backups/` | 移行処理のバックアップ。Git 管理対象外 |

直下の11ファイルを上記へ移動し、内容は保持しました。app.py、requirements.txt、README.md、.gitignore、migrate.py、upload_csv.py は入口・案内・互換性のため直下に残します。既存 Python の互換 import も継続します。画像の DB 保存値や公開 URL に影響するため、既存 static 資産の移動は行いません。実行時の cache・log ディレクトリはアプリ起動時に作成します。
