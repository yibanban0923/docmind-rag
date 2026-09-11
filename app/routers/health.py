from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/live")
def live() -> dict[str, str]:
    return {"status": "ok"}
