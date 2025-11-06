import os
import re
import io
import logging
import unicodedata
from pathlib import Path
from uuid import uuid4
from typing import Optional, List

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from pdf2image import convert_from_path

from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document

from models.untels_models import UntelsInformation

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def limpiar_texto(texto: str) -> str:
    texto = unicodedata.normalize('NFKC', texto)
    texto = re.sub(r'[\x00-\x1F\x7F]', '', texto)
    texto = re.sub(r'[^\w\s.,;:¿?!¡\(\)\[\]áéíóúÁÉÍÓÚñÑüÜ\-]', '', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto.strip()

class FaissSearchService:
    def __init__(self, index_dir: str = "vector_index"):
        self.index_dir = index_dir
        Path(self.index_dir).mkdir(parents=True, exist_ok=True)
        self.vectorstore = None
        self._embedding = None  # Lazy load

        index_file = os.path.join(self.index_dir, "index.faiss")
        if os.path.exists(index_file):
            logger.info(f"[FAISS] Cargando índice existente desde {self.index_dir}...")
            try:
                self.vectorstore = FAISS.load_local(
                    self.index_dir,
                    self.get_embedding(),
                    allow_dangerous_deserialization=True
                )
            except Exception as e:
                logger.error(f"[FAISS] Error cargando índice existente: {e}")
                self.vectorstore = None
        else:
            logger.warning("[FAISS] No existe índice FAISS, aún no creado.")

    def get_embedding(self):
        if self._embedding is None:
            logger.info("[Embeddings] Cargando modelo 'all-MiniLM-L6-v2'...")
            self._embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        return self._embedding

    def _extract_text_or_ocr(self, path: str) -> List[tuple[int, str]]:
        """Devuelve lista de tuplas (número de página, texto)"""
        logger.info(f"[PDF] Extrayendo texto de {path}...")
        doc = fitz.open(path)
        pages_text = []

        for i, page in enumerate(doc):
            page_number = i + 1
            text = page.get_text().strip()
            if len(text) < 20:
                logger.info(f"[PDF] Página {page_number}: sin texto visible. Aplicando OCR...")
                pix = page.get_pixmap(dpi=300)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                text = pytesseract.image_to_string(img, lang="spa")
            pages_text.append((page_number, limpiar_texto(text)))

        return pages_text

    def create_index(self):
        """Reconstruye el índice FAISS desde cero"""
        logger.info("[FAISS] Reconstruyendo índice completo...")

        # Borrar índice existente si hay
        if os.path.exists(os.path.join(self.index_dir, "index.faiss")):
            for f in Path(self.index_dir).glob("*"):
                f.unlink()
            logger.info("[FAISS] Índice anterior eliminado.")

        splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        data_dir = os.path.join(BASE_DIR, "data")

        pdf_files = [f for f in Path(data_dir).glob("*.pdf")]
        if not pdf_files:
            raise ValueError("[FAISS] No se encontraron PDFs en la carpeta /data.")

        docs = []
        for pdf_path in pdf_files:
            source_name = pdf_path.stem.upper()
            logger.info(f"📄 Procesando {source_name}...")
            try:
                pages = self._extract_text_or_ocr(str(pdf_path))
                for page_num, text in pages:
                    if not text.strip():
                        continue
                    splits = [s for s in splitter.split_text(text) if len(s.strip()) > 20]
                    for chunk in splits:
                        docs.append(
                            Document(
                                page_content=chunk,
                                metadata={
                                    "source": source_name,
                                    "page": page_num,
                                    "id": str(uuid4())
                                }
                            )
                        )
            except Exception as e:
                logger.error(f"[ERROR] Falló extracción en {source_name}: {e}")

        if not docs:
            raise ValueError("[FAISS] No se extrajo texto de ningún PDF.")

        # Crear índice FAISS
        self.vectorstore = FAISS.from_documents(docs, self.get_embedding())
        self.vectorstore.save_local(self.index_dir)
        logger.info(f"[FAISS] ✅ Índice creado con {len(docs)} fragmentos.")

    def search(self, query: str, k: int = 3) -> List[UntelsInformation]:
        if not self.vectorstore:
            return [
                UntelsInformation(
                    title="Fuente de datos inexistente",
                    content="El índice FAISS no está disponible. Por favor, contacte soporte técnico.",
                    source=None,
                    section=None,
                    keywords=[]
                )
            ]

        results = self.vectorstore.similarity_search(query, k=k)
        output = []
        for doc in results:
            metadata = doc.metadata or {}
            output.append(UntelsInformation(
                title=f"{metadata.get('source', 'Documento Untels')} (pág. {metadata.get('page', '?')})",
                content=doc.page_content,
                source=metadata.get("source"),
                section=None,
                keywords=[]
            ))

        logger.info(f"[FAISS] {len(output)} resultados encontrados para '{query}'.")
        return output
