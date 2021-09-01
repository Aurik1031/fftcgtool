from __future__ import annotations

from dataclasses import dataclass, InitVar, field


@dataclass(frozen=True)
class Language:
    short: str = field(init=False)
    short_init: InitVar[str] = field(default="")

    def __post_init__(self, short_init: str):
        short_init = short_init.lower()

        # supported languages
        if short_init in ["de", "es", "fr", "ja", "it"]:
            object.__setattr__(self, "short", short_init)
        else:
            # everything else is english
            object.__setattr__(self, "short", "en")

    @property
    def image_suffix(self):
        # supported languages for face URLs
        if self.short in ["de", "es", "fr", "it"]:
            return self.short
        else:
            return "eg"

    @property
    def key_suffix(self):
        # supported languages for Square API
        if self.short in ["de", "es", "fr", "it"]:
            return f"_{self.short.upper()}"
        elif self.short == "ja":
            return ""
        else:
            return "_EN"

    @classmethod
    def all_api_langs(cls) -> set[Language]:
        return set([
            cls(short)
            for short in ["de", "en", "es", "fr", "it", "ja"]
        ])
