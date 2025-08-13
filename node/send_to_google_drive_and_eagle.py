import os
import json
import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from datetime import datetime
from dotenv import load_dotenv

import folder_paths  # ComfyUI環境に依存
from ..core.util import util
from ..core.eagle_api import EagleAPI
from ..core.prompt_info_extractor import PromptInfoExtractor
from ..core.google_drive_uploader import GoogleDriveUploader

# 環境変数の読み込み
#load_dotenv("ParamW.env")

class SendToGoogleDriveAndEagleNode:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        self.client_secret_path = os.path.join(os.path.dirname(__file__), "..","config", 'client_secret.json')
        self.scopes = ['https://www.googleapis.com/auth/drive.file']

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                "format": (["webp", "png"],),
                "lossless_webp": (
                    "BOOLEAN",
                    {"default": False, "label_on": "lossless", "label_off": "lossy"},
                ),
                "compression": (
                    "INT",
                    {"default": 80, "min": 1, "max": 100, "step": 1},
                ),
                "env_file": (
                    ["Param.env", "ParamW.env"],
                    {"default": "ParamW.env"},
                ),

            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    
    RETURN_TYPES = ("IMAGE", "JSON")
    RETURN_NAMES = ("preview", "upload_info")
    OUTPUT_NODE = True
    CATEGORY = "EagleTools"
    FUNCTION = "process_images"

    def process_images(
        self,
        images,
        format="webp",
        lossless_webp=False,
        compression=80,
        env_file="ParamW.env",
        prompt=None,
        extra_pnginfo=None,
    ):
        
        env_path = os.path.join(os.path.dirname(__file__), "..", "config", env_file)
        load_dotenv(env_path)

        self.folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        subfolder_name = datetime.now().strftime("%Y-%m-%d")
        full_output_folder = os.path.join(self.output_dir, subfolder_name)
        os.makedirs(full_output_folder, exist_ok=True)

        eagle_api = EagleAPI()
        extractor = PromptInfoExtractor(prompt)
        prompt_info = extractor.extract_prompt_info()
        prompt_text = prompt_info.get("prompt", "")
        negative_text = prompt_info.get("negative", "")
        meta_text = extractor.format_info(extractor.info)

        uploader = GoogleDriveUploader(self.client_secret_path, self.scopes, self.folder_id)

        results = []

        for image in images:
            img = Image.fromarray(
                np.clip(255.0 * image.cpu().numpy(), 0, 255).astype(np.uint8)
            )
            width, height = img.size
            file_name = f"{util.get_datetime_str_msec()}-{width}-{height}.{format}"
            file_full_path = os.path.join(full_output_folder, file_name)

            if format == "webp":
                exif_data = util.get_exif_from_prompt(img.getexif(), prompt, extra_pnginfo)
                img.save(file_full_path, quality=compression, exif=exif_data, lossless=lossless_webp)
            else:
                metadata = PngInfo()
                if prompt is not None:
                    metadata.add_text("prompt", json.dumps(prompt))
                if extra_pnginfo is not None:
                    for x in extra_pnginfo:
                        metadata.add_text(x, json.dumps(extra_pnginfo[x]))
                img.save(file_full_path, pnginfo=metadata, compress_level=4)

            file_id = uploader.upload_file(file_full_path, file_name)
            drive_url = uploader.get_file_url(file_id)

            item = {
                "path": drive_url,
                "name": file_name,
                "annotation": util.make_annotation_text(prompt_text, negative_text, meta_text),
                "tags": util.get_prompt_tags(prompt_text),
            }

            eagle_api.add_item_from_url(data=item)

            # 画像のメタデータを保存
            results.append({
                "filename": file_name,
                "subfolder": subfolder_name, 
                "type": self.type,
                "format": format, #追加
                "drive_file_id": file_id,
                "used_path": drive_url,
                "tags": util.get_prompt_tags(prompt_text), #追加
                "annotation": util.make_annotation_text(prompt_text, negative_text, meta_text) #追加
            })


        return (images, results)
