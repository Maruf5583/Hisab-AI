import os
import hashlib
import uuid
from typing import Tuple
import pymupdf
from PIL import Image
import io
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings


class StorageService:
    def __init__(self, base_upload_dir: str = settings.UPLOAD_DIR):
        self.base_dir = os.path.abspath(base_upload_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def validate_file(self, file: UploadFile) -> str:
        """Validate filename extension and return normalized lowercase extension."""
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename cannot be empty",
            )

        ext = os.path.splitext(file.filename)[1].lower().lstrip(".")
        if not ext or ext not in settings.allowed_extensions_set:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '.{ext}' is not supported. Allowed extensions: {', '.join(sorted(settings.allowed_extensions_set))}",
            )
        return ext

    def compute_hash_and_inspect(self, content: bytes, ext: str) -> Tuple[str, int, int]:
        """Compute SHA256, verify content integrity, and return (hash, size_bytes, page_count)."""
        size_bytes = len(content)
        if size_bytes > settings.max_upload_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB} MB",
            )

        if size_bytes == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes)",
            )

        file_hash = hashlib.sha256(content).hexdigest()
        page_count = 1

        if ext == "pdf":
            try:
                doc = pymupdf.open(stream=content, filetype="pdf")
                page_count = len(doc)
                doc.close()
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid or corrupted PDF file: {str(e)}",
                )
        else:
            # Validate image with Pillow
            try:
                img = Image.open(io.BytesIO(content))
                img.verify()
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid or corrupted image file: {str(e)}",
                )

        return file_hash, size_bytes, page_count

    def save_file(self, business_id: uuid.UUID, content: bytes, ext: str) -> Tuple[str, str]:
        """Save file bytes to private directory: {base_dir}/{business_id}/{uuid}.{ext}"""
        doc_uuid = uuid.uuid4()
        biz_dir = os.path.join(self.base_dir, str(business_id))
        os.makedirs(biz_dir, exist_ok=True)

        target_filename = f"{doc_uuid}.{ext}"
        target_path = os.path.join(biz_dir, target_filename)

        # Path traversal guard
        normalized_path = os.path.abspath(target_path)
        if not normalized_path.startswith(self.base_dir):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Security violation: Invalid storage path detected",
            )

        with open(target_path, "wb") as f:
            f.write(content)

        return target_path, target_filename

    def get_secure_path(self, business_id: uuid.UUID, stored_path: str) -> str:
        """Resolve and verify that stored path belongs to the given business."""
        normalized_path = os.path.abspath(stored_path)
        biz_dir = os.path.abspath(os.path.join(self.base_dir, str(business_id)))

        if not normalized_path.startswith(biz_dir):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to requested file",
            )

        if not os.path.exists(normalized_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Stored document file not found on disk",
            )

        return normalized_path


storage_service = StorageService()
