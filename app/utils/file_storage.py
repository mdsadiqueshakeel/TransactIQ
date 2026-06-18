import uuid
from pathlib import Path


class FileStorage:
    def __init__(self, upload_dir: Path) -> None:
        self.upload_dir = upload_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save_job_upload(self, *, job_id: uuid.UUID, content: bytes) -> Path:
        destination = self.upload_dir / f"{job_id}.csv"
        destination.write_bytes(content)
        return destination
