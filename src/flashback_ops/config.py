from dataclasses import dataclass
import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    app_name: str
    memory_backend: str
    data_file: Path
    max_recall: int
    hindsight_base_url: str
    hindsight_api_key: str
    hindsight_bank_id: str


def load_settings() -> Settings:
    file_override = os.getenv("FLASHBACK_DATA_FILE", "").strip()
    data_file = Path(file_override) if file_override else ROOT_DIR / "data" / "memory.json"
    return Settings(
        app_name=os.getenv("FLASHBACK_APP_NAME", "Flashback Ops"),
        memory_backend=os.getenv("FLASHBACK_MEMORY_BACKEND", "local"),
        data_file=data_file,
        max_recall=int(os.getenv("FLASHBACK_MAX_RECALL", "5")),
        hindsight_base_url=os.getenv("HINDSIGHT_BASE_URL", "").strip(),
        hindsight_api_key=os.getenv("HINDSIGHT_API_KEY", "").strip(),
        hindsight_bank_id=os.getenv("HINDSIGHT_BANK_ID", "flashback-ops"),
    )
