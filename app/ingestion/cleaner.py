import re
import unicodedata

from app.ingestion.types import LoadedUnit


def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    cleaned: list[str] = []
    last_blank = False
    for line in lines:
        if line:
            cleaned.append(line)
            last_blank = False
        elif cleaned and not last_blank:
            cleaned.append("")
            last_blank = True
    return "\n".join(cleaned).strip()


def clean_units(units: list[LoadedUnit]) -> list[LoadedUnit]:
    result: list[LoadedUnit] = []
    for unit in units:
        text = clean_text(unit.text)
        if text:
            result.append(LoadedUnit(text=text, page=unit.page, section=unit.section))
    return result
