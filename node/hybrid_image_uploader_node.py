import os
import json
import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from datetime import datetime
from dotenv import load_dotenv

import folder_paths  # ComfyUI dependency
from ..core.util import util
from ..core.eagle_api import EagleAPI
from ..core.prompt_info_extractor import PromptInfoExtractor
from ..core.google_drive_uploader import GoogleDriveUploader

# Load environment variables
#load_dotenv("Param.env")

class HybridImageUploaderNode:
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
                "send_prompt": (
                    "BOOLEAN",
                    {"default": True, "label_on": "enabled", "label_off": "disabled"},
                ),
                "upload_to_drive": (
                    "BOOLEAN",
                    {"default": True, "label_on": "enabled", "label_off": "disabled"},
                ),
                "include_model_name": (
                    "BOOLEAN",
                    {"default": True, "label_on": "include", "label_off": "exclude"},
                ),
                "include_steps": (
                    "BOOLEAN",
                    {"default": True, "label_on": "include", "label_off": "exclude"},
                ),
                "include_seed": (
                    "BOOLEAN",
                    {"default": True, "label_on": "include", "label_off": "exclude"},
                ),
                "env_file": (
                    ["Param.env", "ParamW.env"],
                    {"default": "Param.env"},
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
        send_prompt=True,
        upload_to_drive=True,
        include_model_name=True,
        include_steps=True,
        include_seed=True,
        env_file="Param.env",
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
        uploader = GoogleDriveUploader(self.client_secret_path, self.scopes, self.folder_id)

        if send_prompt:
            extractor = PromptInfoExtractor(prompt)
            prompt_info = extractor.extract_prompt_info()
            prompt_text = prompt_info.get("prompt", "")
            negative_text = prompt_info.get("negative", "")
            meta_text = extractor.format_info(extractor.info)
            tags = util.get_prompt_tags(prompt_text)
            annotation = util.make_annotation_text(prompt_text, negative_text, meta_text)

            model_name = extractor.info.get("model_name", "model")
            steps = extractor.info.get("steps", "steps")
            seed = extractor.info.get("seed", "seed")
        else:
            tags = []
            annotation = ""
            model_name = "model"
            steps = "steps"
            seed = "seed"

        results = []

        for image in images:
            img = Image.fromarray(
                np.clip(255.0 * image.cpu().numpy(), 0, 255).astype(np.uint8)
            )
            width, height = img.size

            filename_parts = [util.get_datetime_str_msec()]
            if send_prompt:
                if include_model_name:
                    filename_parts.append(model_name)
                if include_steps:
                    filename_parts.append(f"S{steps}")
                if include_seed:
                    filename_parts.append(f"Seed{seed}")
            filename_parts.append(f"{width}x{height}")
            file_name = "-".join(filename_parts) + f".{format}"
            file_full_path = os.path.join(full_output_folder, file_name)

            if format == "webp":
                exif_data = util.get_exif_from_prompt(img.getexif(), prompt, extra_pnginfo) if send_prompt else img.getexif()
                img.save(file_full_path, quality=compression, exif=exif_data, lossless=lossless_webp)
            else:
                metadata = PngInfo()
                if send_prompt and prompt is not None:
                    metadata.add_text("prompt", json.dumps(prompt))
                if send_prompt and extra_pnginfo is not None:
                    for x in extra_pnginfo:
                        metadata.add_text(x, json.dumps(extra_pnginfo[x]))
                img.save(file_full_path, pnginfo=metadata, compress_level=4)

            if upload_to_drive:
                file_id = uploader.upload_file(file_full_path, file_name)
                file_path = uploader.get_file_url(file_id)
            else:
                file_id = None
                file_path = file_full_path

            item = {
                "path": file_path,
                "name": file_name,
            }

            if send_prompt:
                item["annotation"] = annotation
                item["tags"] = tags

            if upload_to_drive:
                eagle_api.add_item_from_url(data=item)
            else:
                eagle_api.add_item_from_path(data=item)

            results.append({
                "filename": file_name,
                "subfolder": subfolder_name,
                "type": self.type,
                "format": format,
                "drive_file_id": file_id,
                "used_path": file_path,
                "tags": tags,
                "annotation": annotation
            })

        return (images, results)
