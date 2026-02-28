# ZuelData

このリポジトリは、ブログ及びタスク閲覧・投稿・検索・ファイル管理を行うための Web アプリケーションです。

---

## 主な機能

アプリは :Flaskで実装されており、主に次の機能を提供します。

### 認証・ユーザー管理

- ログイン（`/api/login`）
- 新規登録（`/api/regester`）
- 招待コードの発行/表示（`/api/code`）
- アカウント停止 / 停止解除（`/api/block`, `/api/unblock`）
- 退会（`/api/write_off`）
- パスワード変更（申請 `/api/change_pwd_request`、画面 `/user/change_pwd`、反映 `/api/change_pwd`）
- ユーザー設定（画面 `/user/setting`、更新 `/api/user/setting`）
- 権限チェック（`/api/checklevel`） :contentReference[oaicite:3]{index=3}

### コンテンツ（投稿・閲覧）

- 授業と資料（Lesson）
  - 一覧（`/lesson/list`）
  - 詳細（`/lesson/content`）
  - アップロード（`/api/upload/lesson`）
- ブログ（Blog）
  - 投稿画面（`/blog/publish`）
  - 投稿（`/api/upload/blog`）
  - 一覧ページ（`/blog/page`）
  - 詳細（`/blog/content`）
  - カバー取得（`/api/cover`）
  - おすすめ取得（`/api/random`）
- お知らせ（Notice）
  - 一覧（`/notice/page`）
  - 詳細（`/notice/content`）
  - 投稿画面（`/notice/publish`）
  - 投稿（`/api/upload/notice`）

### タスク/返信

- タスク詳細（`/task/content`）
- タスク投稿画面（`/task/publish`）
- タスク一覧（`/task/list`）
- 返信（`/task/reply`）
- タスク投稿 API（`/api/task/publish`）
- メールによるお知らせ機能

### 検索・管理者向け

- 検索 API（`/api/search`）と検索画面（`/search`）
- 管理画面（`/backstage`）
- 削除（`/api/delete`）
- 重複/冗長データの整理（`/api/clear_redundancy`） :contentReference[oaicite:6]{index=6}

### ファイル管理（ダウンロード/アップロード）

- ダウンロード（`/api/download/file`）
- ダウンロード一覧（`/api/download/list`）
- 画像アップロード（`/api/upload/image`）
- 各種データアップロード（`/api/upload/arrange`, `/api/upload/horo`, `/api/upload/quota`, `/api/upload/lawsuit` など）
- オンラインストレージ 画面（`/netdisk`）とアップロード（`/netdisk/upload`, `/api/upload/file`）
- Word/Powerpointに対するフルテキスト検索機能

### 検証コード

- 検証コード（`/api/v_code`）

---

## ディレクトリ / ファイル構成

リポジトリ直下は主に次の構成です。  
  
├─ app.py # エントリ（main.py の app を読み込み）  
├─ main.py # ルーティング・画面/ API 実装、Flask 起動  
├─ datasys.py # DB モデル/データ操作（SQLAlchemy）  
├─ configs.py # DB 接続設定  
├─ config.ini # uWSGI 設定  
├─ util.py # ユーティリティ  
├─ globalv.py # グローバル値/ヘルパ  
├─ static/ # 静的ファイル  
└─ templates/ # HTML テンプレート  
