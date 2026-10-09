import hashlib
import os
import re

import numpy as np
from PIL import Image, ImageOps
import torch


def natural_key(path):
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", path.lower())]


def normalize_extension(extension):
    extension = extension.strip()
    return extension if extension.startswith(".") else "." + extension


def collect_files(folder_path, extension, recursive):
    folder_path = os.path.abspath(os.path.expanduser(folder_path))
    extension = normalize_extension(extension)
    if not os.path.isdir(folder_path):
        raise FileNotFoundError(f"Folder does not exist: {folder_path}")

    matches = []
    for root, _, files in os.walk(folder_path) if recursive else [(folder_path, [], os.listdir(folder_path))]:
        for file in files:
            full_path = os.path.join(root, file)
            if os.path.isfile(full_path) and file.lower().endswith(extension.lower()):
                matches.append(full_path)
    return sorted(matches, key=natural_key)


def folder_state_hash(folder_path, extension, recursive, *settings):
    try:
        paths = collect_files(folder_path, extension, recursive)
    except FileNotFoundError:
        return f"missing:{folder_path}:{settings}"

    digest = hashlib.sha256(str((normalize_extension(extension).lower(), recursive) + settings).encode())
    for path in paths:
        stat = os.stat(path)
        digest.update(path.encode())
        digest.update(str(stat.st_mtime_ns).encode())
        digest.update(str(stat.st_size).encode())
    return digest.hexdigest()


def load_image_file(path):
    image = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)


class ArtSawPromptFromFolderByIndex:
    CATEGORY = "Loads a text prompt from a folder using its sorted file index. Keywords: text, prompt, file, folder, index, loader."
    SEARCH_ALIASES = ["text", "prompt", "file", "folder", "index", "loader"]
    DESCRIPTION = "Loads a text prompt from a selected folder position, with optional recursive search and index wrapping."

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "folder_path": ("STRING", {"default": "", "multiline": False}),
            "index": ("INT", {"default": 0, "min": 0, "max": 999999999}),
            "extension": ("STRING", {"default": ".txt", "multiline": False}),
            "recursive": ("BOOLEAN", {"default": False}),
            "wrap_index": ("BOOLEAN", {"default": True}),
            "include_extension_in_filename": ("BOOLEAN", {"default": True}),
            "encoding": ("STRING", {"default": "utf-8", "multiline": False}),
        }}

    RETURN_TYPES = ("STRING", "STRING", "INT")
    RETURN_NAMES = ("prompt", "filename", "file_count")
    FUNCTION = "load_prompt"

    def load_prompt(self, folder_path, index, extension=".txt", recursive=False, wrap_index=True, include_extension_in_filename=True, encoding="utf-8"):
        files = collect_files(folder_path, extension, recursive)
        if not files:
            raise FileNotFoundError(f"No '{extension}' files found in folder: {folder_path}")
        selected = files[index % len(files)] if wrap_index else files[index]
        with open(selected, "r", encoding=encoding) as handle:
            prompt = handle.read().lstrip("\ufeff").strip()
        raw_filename = os.path.basename(selected)
        filename = raw_filename if include_extension_in_filename else os.path.splitext(raw_filename)[0]
        return prompt, filename, len(files)

    @classmethod
    def IS_CHANGED(cls, folder_path, index, extension=".txt", recursive=False, wrap_index=True, include_extension_in_filename=True, encoding="utf-8"):
        return folder_state_hash(folder_path, extension, recursive, index, wrap_index, include_extension_in_filename, encoding)


class ArtSawImageFromFolderByIndex:
    CATEGORY = "Loads one image from a folder using its sorted file index. Keywords: image, file, folder, index, loader."
    SEARCH_ALIASES = ["image", "file", "folder", "index", "loader"]
    DESCRIPTION = "Loads one image from a selected folder position, with optional recursive search and index wrapping."

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "folder_path": ("STRING", {"default": "", "multiline": False}),
            "index": ("INT", {"default": 0, "min": 0, "max": 999999999}),
            "extension": ("STRING", {"default": ".jpg", "multiline": False}),
            "recursive": ("BOOLEAN", {"default": False}),
            "wrap_index": ("BOOLEAN", {"default": True}),
            "include_extension_in_filename": ("BOOLEAN", {"default": True}),
        }}

    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "filename", "file_count")
    FUNCTION = "load_image"

    def load_image(self, folder_path, index, extension=".jpg", recursive=False, wrap_index=True, include_extension_in_filename=True):
        files = collect_files(folder_path, extension, recursive)
        if not files:
            raise FileNotFoundError(f"No '{extension}' files found in folder: {folder_path}")
        selected = files[index % len(files)] if wrap_index else files[index]
        raw_filename = os.path.basename(selected)
        filename = raw_filename if include_extension_in_filename else os.path.splitext(raw_filename)[0]
        return load_image_file(selected), filename, len(files)

    @classmethod
    def IS_CHANGED(cls, folder_path, index, extension=".jpg", recursive=False, wrap_index=True, include_extension_in_filename=True):
        return folder_state_hash(folder_path, extension, recursive, index, wrap_index, include_extension_in_filename)


class ArtSawImageBatchFromFolder:
    CATEGORY = "Loads a sorted batch of images from a folder for batch workflows. Keywords: image, batch, sequence, folder, file, loader."
    SEARCH_ALIASES = ["image", "batch", "sequence", "folder", "file", "loader"]
    DESCRIPTION = "Loads a sorted set of equally sized images from a folder as one ComfyUI image batch."

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "folder_path": ("STRING", {"default": "", "multiline": False}),
            "extension": ("STRING", {"default": ".png", "multiline": False}),
            "recursive": ("BOOLEAN", {"default": False}),
            "limit": ("INT", {"default": 0, "min": 0, "max": 999999999}),
        }}

    RETURN_TYPES = ("IMAGE", "INT")
    RETURN_NAMES = ("images", "file_count")
    FUNCTION = "load_images"

    def load_images(self, folder_path, extension=".png", recursive=False, limit=0):
        files = collect_files(folder_path, extension, recursive)
        if not files:
            raise FileNotFoundError(f"No '{extension}' files found in folder: {folder_path}")
        if limit > 0:
            files = files[:limit]
        images = [load_image_file(path) for path in files]
        sizes = {tuple(image.shape[1:3]) for image in images}
        if len(sizes) > 1:
            raise ValueError("All images in a batch must have the same dimensions.")
        return torch.cat(images), len(files)

    @classmethod
    def IS_CHANGED(cls, folder_path, extension=".png", recursive=False, limit=0):
        return folder_state_hash(folder_path, extension, recursive, limit)


class ArtSawPathInfo:
    CATEGORY = "Shows a folder name, its parent directory, and its immediate subfolders. Keywords: path, folder, directory, parent, subfolders, inspector."
    SEARCH_ALIASES = ["path", "folder", "directory", "parent", "subfolders", "inspector"]
    DESCRIPTION = "Inspects a filesystem path and returns the folder name, parent directory, and immediate subfolders."

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"path": ("STRING", {"default": "", "multiline": False})}}

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("folder_name", "parent_path", "subfolders")
    FUNCTION = "get_path_info"

    def get_path_info(self, path):
        path = os.path.abspath(os.path.expanduser(path))
        subfolders = []
        if os.path.isdir(path):
            subfolders = sorted(
                [entry for entry in os.listdir(path) if os.path.isdir(os.path.join(path, entry))],
                key=natural_key,
            )
        return os.path.basename(path), os.path.dirname(path), "\n".join(subfolders)


NODE_CLASS_MAPPINGS = {
    "ArtSawPromptFromFolderByIndex": ArtSawPromptFromFolderByIndex,
    "ArtSawImageFromFolderByIndex": ArtSawImageFromFolderByIndex,
    "ArtSawImageBatchFromFolder": ArtSawImageBatchFromFolder,
    "ArtSawPathInfo": ArtSawPathInfo,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ArtSawPromptFromFolderByIndex": "Load Prompt from Folder by Index | 🎨🪚 ArtSaw",
    "ArtSawImageFromFolderByIndex": "Load Image from Folder by Index | 🎨🪚 ArtSaw",
    "ArtSawImageBatchFromFolder": "Load Image Batch from Folder | 🎨🪚 ArtSaw",
    "ArtSawPathInfo": "Inspect Folder Path | 🎨🪚 ArtSaw",
}
