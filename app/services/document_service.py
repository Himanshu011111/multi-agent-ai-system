import os
from pathlib import Path
from pypdf import PdfReader
from docx import Document
from app.config import settings
from app.rag.vector_store import vector_store_manager
from app.utils.logger import logger

class DocumentService:
    def process_file(self, file_path: str, filename: str) -> bool:
        ext = Path(filename).suffix.lower()
        text = ""
        
        try:
            if ext == ".pdf":
                reader = PdfReader(file_path)
                for i, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            elif ext == ".docx":
                doc = Document(file_path)
                for para in doc.paragraphs:
                    if para.text:
                        text += para.text + "\n"
            elif ext in [".txt", ".csv"]:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
            else:
                logger.error(f"Unsupported file extension: {ext}")
                return False
                
            # Chunk text into ~500 character segments
            chunk_size = 500
            chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
            
            if not chunks:
                logger.warning(f"No extractable text found in {filename}")
                return False
                
            documents = []
            metadatas = []
            ids = []
            
            for idx, chunk in enumerate(chunks):
                documents.append(chunk)
                metadatas.append({"filename": filename, "chunk_index": idx})
                ids.append(f"{filename}_chunk_{idx}")
                
            vector_store_manager.add_documents(documents, metadatas, ids)
            logger.info(f"Successfully processed and indexed document: {filename}")
            return True
        except Exception as e:
            logger.error(f"Error processing file {filename}: {str(e)}")
            return False

document_service = DocumentService()