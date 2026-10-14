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

CSV 取り込みの BASE_DIR はリポジトリ直下を維持します。年度成績の再取り込みスクリプトは従来どおり実行時のカレントディレクトリにある鍵・CSV を参照します。運用コマンドはリポジトリ直下から実行してください。

## JavaScript

日程の編集元は `static/js/schedule/` です。ブラウザの配信入口は従来の `static/schedule_board.js` を維持します。

| ファイル | 内容 |
| --- | --- |
| `bootstrap.js` | 共通定数・状態変数・初期化 |
| `dates.js` | 日付、祝日、候補日、試合日 |
| `state.js` | 回答・下書き・人数・表示状態の補助処理 |
| `api.js` | 日程更新の JSON 通信 |
| `render.js` | HTML・画面描画 |
| `forms.js` | 入力・イベントハンドラー・住所検索 |
| `main.js` | 初回読込の起動処理 |

部品は単体でブラウザへ読み込まず、`python scripts/build_schedule_js.py` で同じ関数スコープに結合します。関数の巻き上げと状態変数の初期化順を維持するため、モジュール読み込み方式への変更は行っていません。結合済みファイルも Git 管理し、通常起動にビルドを必須としません。

## テンプレート

旧 `templates/parts/` の数字ファイル名を内容に応じた名称へ変更しました。例: `pc_profile_and_abilities.html`、`mobile_profile_and_navigation.html`、`pitcher_table.html`、`monthly_chart.html`。既存の部品境界と include 順は維持します。タグ・CSS・JavaScript の途中で分かれる既存部品もあるため、ファイル単独での描画は想定しません。API＋JS 移行後は `client/views/parts/` の `.njk` ファイルとしてブラウザが利用します。

## ファイル分割時の検証

- 既存196関数・クラスの処理を、import の移動を除いて AST 比較し、一致を確認。
- 日程 JavaScript の関数処理と初期化文の順序を AST 比較し、一致を確認。
- 模擬 DB を使った13件のテストで、認証、リダイレクト、公開画面、JSON API、入力エラー、日付・イベント処理、テンプレート、旧 import・コマンドを確認。
- 分割前後の登録ルート、公開画面 HTML、日程・イベント JSON 応答が一致することを確認。

テストは実 Firestore に接続せず、実認証鍵も読みません。本番データを使った操作・運用スクリプトの実書き込みは検証対象外です。
