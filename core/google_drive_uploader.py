from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os
import json
import sys

sys.path.append('/content/drive/MyDrive/ComfyUI/custom_nodes/comfyui_send_to_eagle_sync')
base_dir=os.path.dirname(os.path.abspath(__file__))

class GoogleDriveUploader:
    def __init__(self,  client_secret_path=os.path.join(base_dir, "..","config", "client_secret.json"), scopes=None, folder_id=None, token_path=os.path.join(base_dir, "..","config", "token.json")):
        self.base_dir = base_dir
        self.client_secret_path = client_secret_path
        self.scopes = scopes
        self.folder_id = folder_id
        self.token_path = token_path
        self.service = self.authenticate()

    def authenticate(self):
        creds = None

        # トークンファイルの存在確認
        if os.path.exists(self.token_path):
            print(f"✅ トークンファイル '{self.token_path}' が見つかりました。")
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, self.scopes)
                print("✅ トークンの読み込みに成功しました。")
            except Exception as e:
                print(f"⚠️ トークンの読み込みに失敗しました: {e}")
                creds = None
        else:
            print(f"⚠️ トークンファイル '{self.token_path}' が存在しません。ローカルで取得してアップロードしてください。")

        # トークンの更新
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                print("🔄 トークンを更新しました。")
            except Exception as e:
                print(f"⚠️ トークンの更新に失敗しました: {e}")
                creds = None

        # 認証フローの開始
        if not creds or not creds.valid:
            print("🔐 新しい認証フローを開始します。")
            flow = InstalledAppFlow.from_client_secrets_file(self.client_secret_path, self.scopes)
            creds = flow.run_local_server(port=0)

            # トークンの保存
            with open(self.token_path, 'w') as token_file:
                token_file.write(creds.to_json())
            print(f"✅ 新しいトークンを '{self.token_path}' に保存しました。")

        return build('drive', 'v3', credentials=creds)



    def upload_file(self, file_path, filename):
        metadata = {'name': filename}
        if self.folder_id:
            metadata['parents'] = [self.folder_id]

        media = MediaFileUpload(file_path, resumable=True)
        file = self.service.files().create(body=metadata, media_body=media, fields='id').execute()
        self.make_file_public(file['id'])
        return file['id']

    def make_file_public(self, file_id):
        permission = {'type': 'anyone', 'role': 'reader'}
        self.service.permissions().create(fileId=file_id, body=permission).execute()

    def get_file_url(self, file_id):
        #return f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
        return f"https://drive.google.com/uc?export=view&id={file_id}"
        #return f"https://drive.usercontent.google.com/download?id={file_id}&export=view&authuser=0"
