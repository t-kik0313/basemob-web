# API・フォーム定義

[設計書トップ](README.md) / [データ定義](data-model.md) / [ビジネスルール](business-rules.md)

## 共通仕様

ベースパスは `/t/{slug}`。以下のパスにこの接頭辞を付けます。パラメーター `{player_id}` は Flask の integer converter、`{game_id}` は文字列です。JSON API と HTML フォーム処理の両方を記載します。

JSON API の入力は `Content-Type: application/json`。フォームは `application/x-www-form-urlencoded`、画像を含むものは `multipart/form-data`。フォーム保存の成功は原則302です。画面を取得する GET は [画面定義](screens.md) を参照します。

認証は HTTP Basic または署名付き `team_login` Cookie。Bearer トークン方式ではありません。認証フックが返す401は HTML/テキストと `WWW-Authenticate` を伴い、API の JSON エラーとは形式が異なります。チーム接頭辞なしの経路は認証後302になるため、クライアントはチーム別 URL を指定してください。

### 登録 API と権限

「公開」はチームが存在する未ログイン状態でも到達できる action を意味します。

| ID | メソッド・パス | action | 権限 | 成功 |
| --- | --- | --- | --- | --- |
| A-01 | GET `/api/schedule` | — | 公開 | 200、日程状態 |
| A-02 | POST `/api/schedule/poll` | answer | 公開 | 200、日程状態 |
| A-02 | 同上 | people | 会員 | 同上 |
| A-02 | 同上 | add / remove / game / clear-game | 公開（現実装） | 同上 |
| A-03 | GET `/api/events` | — | 公開 | 200、イベント状態 |
| A-04 | POST `/api/events` | answer | 公開 | 200、イベント状態 |
| A-04 | 同上 | create / update / confirm / delete / people | 会員 | 同上 |
| A-05 | POST `/api/update_abilities` | — | 会員 | 200、`{"ok":true}` |

日程の編集操作が公開である点は、画面の表示制御から推定した権限ではなく `routes/schedule.py` の実際の検証条件です。

## A-01 日程取得

`GET /api/schedule`。クエリ・ボディなし。

### レスポンス

| フィールド | 型 | 内容 |
| --- | --- | --- |
| `removed` / `added` | array of string | 除外日 / 追加日 |
| `answers` | map | 日程回答 |
| `games` | map | 日付別試合カード |
| `events` | map | 同じ poll 内のイベントも含む |
| `answerPeople` / `eventPeople` | array / null | 保存された回答者設定 |
| `people` | array of map | 日程で表示する回答者 `{id,name}` |
| `peopleCustom` | boolean | 日程の回答者をカスタム設定しているか |

文書がない場合は空状態を正規化して返します。Firestore・名簿取得に失敗すると500 `{"error":"読み込めませんでした。"}`。

## A-02 日程更新

`POST /api/schedule/poll`。ボディは JSON オブジェクト。`action` は以下のいずれか。成功レスポンスは A-01 と同形式です。

### action 入力定義

| action | 入力 | 処理 |
| --- | --- | --- |
| `answer` | `answers` 必須、回答者として `person_id` / `player_id` / `name` | 回答更新。person_id が非空なら優先、次に player_id、両方なければ name |
| `people` | `people`: array of `{id?,name}` | 日程の回答者リストを設定。ログイン必須 |
| `add` | `iso`: 日付、`routine`: boolean（任意） | 手動追加、または除外された基本日の復帰 |
| `remove` | `iso`: 日付 | 日付を除外、回答・試合カードも削除 |
| `game` | `iso`: 日付、`game`: 試合カード | カードを正規化し保存 |
| `clear-game` | `iso`: 日付 | 試合カードだけ削除 |

`answers` は `{日付: {status, by?}}`。最大62日、当日～来月末。status は `all/am/pm/pending/out`、空は削除。pending は by 必須です。

`person_id` は回答者リストの ID（数字文字列または `m:{hex}`）。カスタムリスト未設定なら名簿 ID を検証します。`player_id` は整数変換して名簿またはカスタムリストを検証します。`name` は名簿・設定名に照合し、未一致ならゲストとして保存します。

### 回答例

```json
{
  "action": "answer",
  "player_id": 1,
  "answers": {
    "2026-10-25": {"status": "all"},
    "2026-11-01": {"status": "pending", "by": "2026-10-28"}
  }
}
```

日付は例です。実行時の受付期間に合わせて変更します。

### 試合カード保存例

```json
{
  "action": "game",
  "iso": "2026-10-25",
  "game": {
    "slot": "am", "opponent": "チームA", "eventName": "練習試合",
    "stadium": "球場A", "address": "", "uniform": "黒", "bat": "情報なし",
    "timeGather": "08:00", "timePB": "09:00", "bench": "",
    "lineup": [{"n": "選手A", "p": "遊"}]
  }
}
```

不足打順枠は空欄で10枠へ補完、11枠目以降は破棄します。`slot` の無効値は400、その他の列挙値・時刻の無効値は規定値/空へ補正します。フィールド別の文字数は [データ定義](data-model.md) を参照します。

### エラー

| 状況 | HTTP | JSON |
| --- | --- | --- |
| JSON がオブジェクトでない / 未知 action | 400 | `{"error":"形式が違います。"}` |
| 期間外の日付、不正な選択肢、未定期日なし、対象者不明等 | 400 | `{"error":"各検証メッセージ"}` |
| 未ログインで people 操作 | 401 | `{"error":"ログインが必要です。"}` |
| 保存・取得等の例外 | 500 | `{"error":"保存に失敗しました。"}` |

## A-03 イベント取得

`GET /api/events`。クエリ・ボディなし。

```json
{
  "events": {},
  "people": [{"id": "1", "name": "選手A"}],
  "peopleCustom": false
}
```

`events` の各値はイベント定義（名称・候補日・回答等）。`people` はイベント用回答者リスト。取得失敗は500 `{"error":"読み込めませんでした。"}`。

## A-04 イベント更新

`POST /api/events`。ボディは JSON オブジェクト。成功レスポンスは A-03 と同形式です。

| action | 入力 | 処理 |
| --- | --- | --- |
| `create` | `event` | 新規作成。ID はサーバーで生成 |
| `update` | `id`: event ID、`event` | 既存編集、回答を保持・必要に応じ移動 |
| `confirm` | `id` | confirmed を true にする |
| `delete` | `id` | イベントと全回答を削除 |
| `people` | `people`: array of `{id?,name}` | イベント用の回答者設定 |
| `answer` | `id`、`answers`、`person_id` / `player_id` / `name` | 候補日ごとの出欠更新 |

`event` の入力は `name`（必須）、`dates`（必須）、`place`、`address`、`timeStart`、`note`。`confirmed` や `answers` をこの入力に含めても更新値には採用しません。

`id` は `[a-f0-9]{8}` で既存イベントに一致する必要があります。候補日は1～14、新規日付は当日～6か月先月末、イベント最大40。回答は候補日に含まれる日付が対象で `in/pending/out`、空で削除。pending は回答期日必須です。

### 作成・回答例

```json
{
  "action": "create",
  "event": {
    "name": "懇親会", "place": "会場A", "address": "", "timeStart": "18:00",
    "note": "", "dates": ["2026-11-01", "2026-11-08"]
  }
}
```

```json
{
  "action": "answer", "id": "a1b2c3d4", "name": "ゲストA",
  "answers": {"2026-11-01": {"status": "in"}}
}
```

作成された ID は応答の events のキーで確認します。上記 ID は架空の例です。person_id は設定リストを検証しますが、player_id は名簿を検証する経路であり、同じ検証条件ではありません。

### エラー

| 状況 | HTTP | JSON |
| --- | --- | --- |
| JSON がオブジェクトでない / 未知 action | 400 | `{"error":"形式が違います。"}` |
| 名称・日付・回答・イベント ID 等の検証失敗 | 400 | `{"error":"各検証メッセージ"}` |
| 未ログインで answer 以外 | 401 | `{"error":"ログインが必要です。"}` |
| 保存等の例外 | 500 | `{"error":"保存に失敗しました。"}` |

## A-05 能力補正更新

`POST /api/update_abilities`。ログイン必須。

| フィールド | 型 | 条件 |
| --- | --- | --- |
| `player_id` | string / number | None 以外。文書存在・整数・名簿所属の検証はなし |
| `abilities` | object | 6つの対応キーのうち更新するものを指定 |

対応キー: `plus_meet,plus_power,plus_speed,plus_arm,plus_defense,plus_catching`。各値は Python `int()` で変換可能かつ0～16。小数を送ると整数化される場合があります。未対応キーは無視します。空の更新でも200です。

```json
{"player_id": 1, "abilities": {"plus_meet": 3, "plus_power": 2}}
```

正常: `200 {"ok":true}`。不正補正・player_id 未指定: `400 {"ok":false}`。保存は `players/{str(player_id)}` の merge set なので、文書が未存在なら補正項目だけの文書を作る可能性があります。持ち点・補正合計は検証しません。保存例外を JSON にする専用処理や JSON の厳密な型検証はなく、500となる場合があります。

## HTML フォームの更新経路

全経路がチームログイン必須です。JSON API とは別の入力形式です。

| ID | メソッド・パス | 入力 | 成功時・主なエラー |
| --- | --- | --- | --- |
| F-01 | POST `/register_player` | multipart: name,number,position,throw_hand,bat_hand,image? | 一覧へ302。検証失敗はフォーム再表示200 |
| F-02 | POST `/edit_player/{player_id}` | multipart: name,number,pos1,pos2,pos3,pitch_bat,birth_date,image_path,image? | 詳細へ302。画像エラーはフォーム再表示200 |
| F-03 | POST `/game/{game_id}/scoreboard_image` | multipart: scoreboard_image | 試合詳細へ302。画像不正も302、試合なし404 |
| F-04 | POST `/game/{game_id}/youtube` | youtube_url | 試合詳細へ302。URL不正も302、試合なし404 |
| F-05 | POST `/admin/regulation` | pa_coef | `?saved=1` へ302。検証・接続不備は設定画面200 |
| F-06 | POST `/admin/qualitative_abilities` | kind_keys（複数）、new_kind、各能力キーの選手ID（複数） | 同一設定画面へ302 |
| F-07 | POST `/save_record/{player_id}` | 試合属性・打席配列・試合合計 | 選手詳細へ302 |
| F-08 | POST `/update_game_record/{player_id}` | csv_index、打席更新項目・チェック項目 | 選手詳細へ302 |
| F-09 | POST `/delete_game_record/{player_id}/{csv_index}` | URLの文書ID、ボディ不要 | 選手詳細へ302 |

フォームの入力検証は [画面定義](screens.md) と [業務ルール](business-rules.md) を参照します。保存・ファイル I/O 等の例外には統一ハンドラーがありません。

### F-07 従来打席保存の詳細

| 入力 | 既定値・扱い |
| --- | --- |
| `game_date,game_id,stadium` | 未指定は None。必須・日付のサーバー検証なし |
| `game_type` | official |
| `batting_order` | sub |
| `fielding_position` | PR |
| `game_sb,game_runs,game_rbi,game_errors,game_gidp` | 各0、int変換。試合合計として最初の打席にだけ保存 |
| `result[]` | 打席ごとの結果。要素数分を新規保存 |
| `direction[],runner[]` | 同じ打席インデックスで参照。配列長不足は検証せず例外になり得る |
| `vs_left[],sayonara[]` | 配列不足時0 |
| `s1,s2,...` | 打席番号ごとのストライク、既定0 |

保存先は新 DB のトップレベル `game_records`。自動 ID を発行してバッチ保存後、キャッシュ再生成を呼びます。空の result 配列では打席は保存されません。

### F-08 従来打席更新の詳細

`csv_index` は Firestore 文書 ID。更新可能な通常項目は `game_date,game_id,result,direction,runner,strikes,stadium,game_type,batting_order,fielding_position`。送信したものだけ更新します。

チェック項目 `is_official,is_4th_bat,is_hr,advancing_runner,vs_left,multi_hit,sayonara` は毎回送信有無で文字列 `1` または `0` にします。試合合計項目はこの更新処理に含まれません。URL の player_id と対象文書の選手 ID 一致は検証しません。削除経路も同じ新 DB トップレベルを操作します。

## 外部連携と未登録経路

| 経路 | 現状 |
| --- | --- |
| 外部成績入力 URL | 別タブで開くリンク。外部側 API・権限・保存処理の詳細は本リポジトリでは確定できない |
| 国土地理院住所検索 | ブラウザから `https://msearch.gsi.go.jp/address-search/AddressSearch?q={検索語}` に GET。Flask のプロキシ API はなし |
| `/api/update_attr` | 能力一覧部品から呼ぶが Flask に未登録 |
| `/update_game_score/{game_id}` | 試合スコア編集フォームから呼ぶが Flask に未登録 |
| POST `/api/schedule` | 古い日程部品に記載があるが GET のみ登録 |

チーム認証済みの場合、未登録パスは原則404、既存パスの非対応メソッドは405です。認証フックは先に動くため、未ログイン状態では401が先に返る場合があります。
