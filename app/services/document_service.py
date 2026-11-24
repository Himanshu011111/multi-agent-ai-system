import gc
from pathlib import Path
from typing import List, Tuple
from pypdf import PdfReader
from docx import Document
from app.rag.vector_store import vector_store_manager
from app.utils.logger import logger

MAX_PDF_PAGES = 40
MAX_CHUNKS_PER_DOC = 80
BATCH_SIZE = 20


class DocumentService:
    def process_file(self, file_path: str, filename: str) -> bool:
        ext = Path(filename).suffix.lower()
        page_sections: List[Tuple[int, str]] = []

        try:
            if ext == ".pdf":
                reader = PdfReader(file_path)
                total_pages = len(reader.pages)
                pages_to_read = min(total_pages, MAX_PDF_PAGES)
                if total_pages > MAX_PDF_PAGES:
                    logger.info(
                        f"{filename} has {total_pages} pages; indexing first {MAX_PDF_PAGES} pages for cloud RAM safety."
                    )
                for i in range(pages_to_read):
                    page_text = reader.pages[i].extract_text()
                    if page_text and page_text.strip():
                        page_sections.append((i + 1, page_text.strip()))
                del reader
                gc.collect()

            elif ext == ".docx":
                doc = Document(file_path)
                full_text = "\n".join(p.text for p in doc.paragraphs if p.text)
                if full_text.strip():
                    page_sections.append((1, full_text.strip()))
                del doc
                gc.collect()

            elif ext in [".txt", ".csv"]:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    raw_text = f.read()
                if raw_text.strip():
                    page_sections.append((1, raw_text.strip()))

            else:
                logger.error(f"Unsupported file extension: {ext}")
                return False

            if not page_sections:
                logger.warning(f"No extractable text found in {filename}")
                return False

            # Overlapping chunks with exact page numbers for citations
            chunk_size = 800
            overlap = 100
            step = chunk_size - overlap

            documents: List[str] = []
            metadatas: List[dict] = []
            ids: List[str] = []

            chunk_counter = 0
            for page_num, p_text in page_sections:
                for start in range(0, len(p_text), step):
                    segment = p_text[start : start + chunk_size].strip()
                    if not segment:
                        continue
                    documents.append(f"[Page {page_num}] {segment}")
                    metadatas.append(
                        {
                            "filename": filename,
                            "page": page_num,
                            "chunk_index": chunk_counter,
                        }
                    )
                    ids.append(f"{filename}_p{page_num}_c{chunk_counter}")
                    chunk_counter += 1
                    if chunk_counter >= MAX_CHUNKS_PER_DOC:
                        break
                if chunk_counter >= MAX_CHUNKS_PER_DOC:
                    break

            del page_sections
            gc.collect()

            if not documents:
                logger.warning(f"No valid chunks created for {filename}")
                return False

            # Index in small batches to keep peak RAM usage low
            for b_start in range(0, len(documents), BATCH_SIZE):
                b_end = b_start + BATCH_SIZE
                vector_store_manager.add_documents(
                    documents[b_start:b_end],
                    metadatas[b_start:b_end],
                    ids[b_start:b_end],
                )
                gc.collect()

            logger.info(
                f"Successfully processed and indexed {len(documents)} chunks from {filename}"
            )
            return True

        except Exception as e:
            logger.error(f"Error processing file {filename}: {str(e)}")
            return False


document_service = DocumentService()