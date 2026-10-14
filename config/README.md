# 共通設定

`paths.py` はアプリと運用スクリプトのファイルパスを、リポジトリ位置から解決します。実行時の作業ディレクトリには依存しません。

Firebase の認証鍵は `credentials/firebase_key.json`（新 DB）と `credentials/firebase_key_notuse.json`（旧 DB）に配置します。`credentials/` は Git 管理対象外です。鍵の内容はこの文書やソースへ転記しません。

アプリの既存設定値とログ初期化は `webapp/config.py` にあります。
