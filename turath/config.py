"""الإعدادات وأنماط التشغيل الثلاثة.

solo — مستخدم واحد على حاسوب واحد: الخادم على 127.0.0.1 فقط، ودخول برمز عشوائي يتولد عند كل تشغيل.
lan  — مستخدم واحد على أجهزة متعددة من خادم محلي: الخادم على الشبكة المحلية، ودخول بكلمة مرور، وTLS اختياري.
team — عدة مستخدمين: حساب لكل باحث، وبحوث خاصة لا يراها غيره، ومشاركة المصادر والتأليف المشترك بالدعوة.
"""
from __future__ import annotations
import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path

MODES = {
    "solo": {"label": "مستخدم واحد — حاسوب واحد", "host": "127.0.0.1"},
    "lan": {"label": "مستخدم واحد — أجهزة متعددة من خادم محلي", "host": "0.0.0.0"},
    "team": {"label": "عدة مستخدمين — حسابات خاصة ومشاركة", "host": "0.0.0.0"},
}


def default_home() -> Path:
    return Path(os.environ.get("TURATH_HOME") or Path.home() / "Turath")


@dataclass
class Config:
    home: Path = field(default_factory=default_home)
    mode: str = "solo"
    host: str = ""
    port: int = 8765
    tls_cert: str = ""
    tls_key: str = ""
    session_hours: int = 72
    admin_sees_all: bool = False     # المدير لا يرى بحوث الآخرين الخاصة افتراضياً
    allow_explicit_ids: bool = False
    engine: str = "manual"           # manual · claude_code · api
    institution: str = "إدارة الدراسات والبحوث التراثية الإماراتية"

    @property
    def db_path(self) -> Path:
        return self.home / "turath.db"

    @property
    def vault(self) -> Path:
        return self.home / "vault"

    @property
    def backups(self) -> Path:
        return self.home / "backups"

    @property
    def exports(self) -> Path:
        return self.home / "exports"

    @property
    def file(self) -> Path:
        return self.home / "turath.json"

    def bind_host(self) -> str:
        return self.host or MODES[self.mode]["host"]

    def load(self) -> "Config":
        if self.file.exists():
            data = json.loads(self.file.read_text(encoding="utf-8"))
            for k, v in data.items():
                if k != "home" and hasattr(self, k):
                    setattr(self, k, v)
        return self

    def save(self) -> None:
        self.home.mkdir(parents=True, exist_ok=True)
        d = asdict(self)
        d.pop("home")
        self.file.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

    def use_home(self, home: Path | str) -> "Config":
        self.home = Path(home)
        return self.load()


CFG = Config().load()
