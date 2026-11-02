from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.ingestion.pdf_parser import PDFParser
from app.services.ingestion.chunker import TextChunker
from app.services.ingestion.embedder import Embedder
from app.services.rag.retriever import Retriever

router = APIRouter(prefix="/documents", tags=["documents"])

# One of each, shared by every request
parser = PDFParser()
chunker = TextChunker()
embedder = Embedder()
retriever = Retriever(embedder)


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    data = await file.read()
    try:
        pages = parser.extract_pages(data)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    if len(pages) == 0:
        raise HTTPException(status_code=422, detail="No text found (scanned PDF?)")

    chunks = chunker.chunk(pages)
    retriever.add_chunks(chunks, file.filename)

    return {
        "filename": file.filename,
        "pages_with_text": len(pages),
        "chunk_count": len(chunks),
    }


@router.get("/search")
def search_documents(query: str, top_k: int = 3):
    results = retriever.search(query, top_k)
    if not results:
        raise HTTPException(status_code=404, detail="Nothing uploaded yet")
    return {"query": query, "results": results}