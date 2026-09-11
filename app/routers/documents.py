from fastapi import APIRouter, Depends, File, Request, Response, UploadFile, status

from app.container import AppContainer
from app.core.exceptions import DocumentNotFoundError
from app.deps import get_container
from app.schemas.documents import DocumentListResponse, DocumentResponse

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),  # noqa: B008
    container: AppContainer = Depends(get_container),  # noqa: B008
):
    return await container.ingestion_service.ingest_upload(
        file,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("", response_model=DocumentListResponse)
def list_documents(container: AppContainer = Depends(get_container)):  # noqa: B008
    return {"items": container.document_repo.list()}


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, container: AppContainer = Depends(get_container)):  # noqa: B008
    record = container.document_repo.get(document_id)
    if record is None:
        raise DocumentNotFoundError()
    return record


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str, container: AppContainer = Depends(get_container)):  # noqa: B008
    container.document_service.delete(document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
