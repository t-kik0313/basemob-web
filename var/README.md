# 実行時ファイル

- `cache/players_data.json`: チーム未指定・RYUNEN の既存集計キャッシュ。
- `cache/players_data_{team_id}.json`: その他チームの集計キャッシュ。
- `log/debug_log.txt`: アプリの追記ログ。

アプリ起動時にキャッシュ・ログのディレクトリを作成します。チーム別の生成キャッシュとログは Git 管理対象外です。移動した既存の `players_data.json` は従来どおりリポジトリのデータとして保持します。
