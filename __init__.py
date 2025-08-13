from .node.send_to_google_drive_and_eagle import SendToGoogleDriveAndEagleNode
from .node.hybrid_image_uploader_node import HybridImageUploaderNode

NODE_CLASS_MAPPINGS = {
    "Send to Google Drive and Eagle": SendToGoogleDriveAndEagleNode,
    "Hybrid Image Uploader": HybridImageUploaderNode,
}
__all__ = ["NODE_CLASS_MAPPINGS"]
