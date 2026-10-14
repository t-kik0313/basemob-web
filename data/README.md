# 入力・参照データ

| 配置 | ファイル | 用途 |
| --- | --- | --- |
| `imports/` | `basic_info_input.csv` | 基本情報の取り込み |
| `imports/` | `game_records.csv` | 打席記録の取り込み |
| `imports/` | `annual_stats_input.csv` | 年度成績の取り込み・再登録 |
| `imports/` | `record_meeting_data.csv` | 測定記録の取り込み |
| `reference/` | `schedule_data.csv` | 従来予定のフォールバック・チーム移行。内容は JSON 配列 |
| `reference/` | `data_2025_matsushita.csv` | 既存の参考データ。アプリ内からの参照はない |

運用コマンドは `scripts/` にあります。フォルダ整理ではデータ内容や DB の保存先は変更していません。
