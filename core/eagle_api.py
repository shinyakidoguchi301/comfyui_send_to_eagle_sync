import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables from Param.env
load_dotenv("./config/Param.env")

class EagleAPI:
    def __init__(self):
        self.base_url = os.getenv("EAGLE_API_URL", "http://localhost:41595")
        self.token = os.getenv("EAGLE_API_TOKEN")
        self.folder_id = os.getenv("EAGLE_FOLDER_ID")

    def add_item_from_url(self, data, folder_id=None):
        folder_id = folder_id or self.folder_id
        if folder_id:
            data["folderId"] = folder_id

        # Ensure 'url' key is present instead of 'path'
        if "path" in data:
            data["url"] = data.pop("path")

        print("=== Eagle API に送信するデータ (add_item_from_url) ===")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        return self._send_request("/api/item/addFromURL", method="POST", data=data)

    def add_item_from_path(self, data, folder_id=None):
        """
        指定されたパスから Eagle にアイテムを追加する。
        folder_id が指定されていない場合は self.folder_id を使用。
        """
        folder_id = folder_id or self.folder_id
        if folder_id:
            data["folderId"] = folder_id

        # デバッグ用ログ出力
        print("=== Eagle API に送信するデータ (add_item_from_path) ===")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        return self._send_request("/api/item/addFromPath", method="POST", data=data)

    
    def _send_request(self, endpoint, method="GET", data=None):
        url = self.base_url.rstrip("/") + endpoint

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                print("=== リクエスト送信先 URL ===")
                print(url)
                print("=== リクエストヘッダー ===")
                print(headers)
                print("=== リクエストボディ ===")
                print(json.dumps(data, indent=2, ensure_ascii=False))

                response = requests.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            print("=== レスポンスステータスコード ===")
            print(response.status_code)
            print("=== レスポンス内容 ===")
            print(response.text)

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"HTTPリクエストエラー: {e}")
            return {"status": "error", "message": str(e)}
