from typing import List
from services.faiss_service import FaissSearchService
from models.untels_models import UntelsInformation

class UntelsService:
    def __init__(self):
        self._faiss = None

    def _get_faiss(self) -> FaissSearchService:
        if self._faiss is None:
            print("⚙️ Cargando FaissSearchService...")
            self._faiss = FaissSearchService(index_dir="vector_index")
        return self._faiss

    def search_untels_info(self, query: str, max_results: int = 5) -> List[UntelsInformation]:
        return self._get_faiss().search(query, k=max_results)

    def rebuild_index(self) -> str:
        """Elimina y recrea el índice FAISS."""
        faiss_service = self._get_faiss()
        faiss_service.create_index()
        return "✅ Índice FAISS reconstruido correctamente."

    def get_untels_info_by_title(self, title: str) -> UntelsInformation | None:
        return None  # Por implementar si se desea búsqueda exacta
