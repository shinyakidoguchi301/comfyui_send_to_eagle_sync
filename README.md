## 📘 README.md（提案）


# ComfyUI Send to Eagle Sync

このプロジェクトは、ComfyUI のカスタムノードを通じて、生成された画像を **Eagle** や **Google Drive** に自動アップロード・整理するためのツールです。

---

## 🚀 主な機能

- 📤 ComfyUIノードから画像を **Eagle** にアップロード
- ☁️ **Google Drive** へのアップロード（OAuth2対応）
- 🏷️ Eagle API を使ったタグ付け・整理
- 🧪 GUIによる手動操作・テスト機能
- ⚙️ `.env` による柔軟な設定管理
- 🧩 モジュール化された拡張性の高いコードベース

---

## 🛠️ インストールとセットアップ

1. リポジトリをクローン：

```bash
git clone https://github.com/shinyakidoguchi301/comfyui_send_to_eagle_sync.git
cd comfyui_send_to_eagle_sync
```

2. 必要な環境変数を `.env` または `Param.env` に設定します。

3. Google Drive連携には `client_secret.json` と `credentials.json` が必要です。

---

## 📂 ディレクトリ構成（抜粋）

```
├── gui/                  # GUI関連ファイル
├── output/               # 出力画像
├── test/                 # テスト用スクリプト
├── ver/                  # バージョン管理関連
├── generate_style_tree.py  # スタイルツリー生成スクリプト
├── Param.env             # 環境変数ファイル
├── client_secret.json    # Google API認証情報
└── ...
```

---

## 📄 ライセンス

このプロジェクトは **MITライセンス** のもとで公開されています。詳細は `LICENSE` ファイルをご確認ください。

---