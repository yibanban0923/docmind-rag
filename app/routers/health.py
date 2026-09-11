from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from app.container import AppContainer
from app.deps import get_container

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


def _is_writable(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".ready_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except OSError:
        return False


@router.get("/ready")
def ready(container: AppContainer = Depends(get_container)) -> dict:  # noqa: B008
    checks: dict[str, object] = {}
    try:
        checks["sqlite"] = container.document_repo.ping()
    except Exception:  # noqa: BLE001
        checks["sqlite"] = False
    try:
        checks["chroma"] = container.vector_store.ping()
    except Exception:  # noqa: BLE001
        checks["chroma"] = False
    checks["data_dir"] = _is_writable(container.settings.DATA_DIR)
    missing = container.settings.missing_real_model_config()
    checks["model_config"] = not missing
    if missing:
        checks["missing_model_config"] = missing

    if not checks["sqlite"] or not checks["chroma"] or not checks["data_dir"] or missing:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "checks": checks},
        )
    return {"status": "ready", "checks": checks}
