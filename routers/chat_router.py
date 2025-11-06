from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from models.chat_models import ChatRequest, ChatResponse, Message, ChatRole, QuickAction
from models.untels_models import UntelsInformation
from services.openai_service import OpenAIService
from services.untels_service import UntelsService
import traceback
import json

router = APIRouter()

# ==========================================================
# DEPENDENCIAS
# ==========================================================

def get_openai_service():
    return OpenAIService()

def get_untels_service():
    try:
        return UntelsService()
    except Exception as e:
        print("[FATAL ERROR] Fallo al inicializar UntelsService:")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error inicializando servicio Untels: {str(e)}"
        )

# ==========================================================
# ENDPOINT PRINCIPAL DEL ASISTENTE VRI-UNTELS
# ==========================================================

@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_with_bot(
    request: ChatRequest,
    openai_service: OpenAIService = Depends(get_openai_service),
    untels_service: UntelsService = Depends(get_untels_service)
):
    print("📥 Nueva solicitud recibida:")
    print("→ message:", request.message)
    print("→ chat_history:", [m.dict() for m in request.chat_history or []])

    chat_history_messages = request.chat_history or []
    user_message_content = (
        request.message.strip()
        if request.message and request.message.strip().lower() != "string"
        else (chat_history_messages[-1].content if chat_history_messages else "")
    )

    if not user_message_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message content cannot be empty."
        )

    # ==========================================================
    # CONFIGURACIÓN DEL ASISTENTE (Prompt del sistema)
    # ==========================================================
    llm_messages: List[Message] = [
        Message(
            role=ChatRole.system,
            content=(
                "Eres un asistente experto en normativa universitaria y en la gestión de investigación del "
                "Vicerrectorado de Investigación de la Universidad Nacional Tecnológica de Lima Sur (VRI-UNTELS). "
                "Tu tarea es responder basándote estrictamente en los documentos institucionales oficiales del VRI-UNTELS, como:\n"
                "- Reglamento de Investigación UNTELS\n"
                "- Reglamento del Docente Investigador\n"
                "- Reglamento del Comité de Ética\n"
                "- Código Nacional de Integridad Científica\n"
                "- Reglamento de Propiedad Intelectual\n"
                "- PEI 2024-2030, PIA 2025, directivas, guías y manuales del VRI\n"
                "- Estatuto y Ley Universitaria\n\n"
                "Debes devolver SIEMPRE la respuesta en formato JSON con dos campos:\n"
                "{\n"
                "  \"respuesta\": \"texto explicativo y formal, breve pero técnico, adaptado al contexto académico\",\n"
                "  \"referencias\": [\"Documento — Página o Artículo\"]\n"
                "}\n\n"
                "Si no existe información suficiente, responde igualmente en formato JSON con un mensaje de orientación, por ejemplo:\n"
                "{\n"
                "  \"respuesta\": \"No se encontró información específica en los documentos oficiales. Puede consultar directamente al VRI-UNTELS.\",\n"
                "  \"referencias\": []\n"
                "}\n\n"
                "El tono debe ser cordial, institucional y claro. Nunca inventes información ni cites documentos inexistentes."
            )
        )
    ]

    llm_messages += chat_history_messages
    llm_messages.append(Message(role=ChatRole.user, content=user_message_content))

    # ==========================================================
    # BÚSQUEDA EN FAISS (DOCUMENTOS VRI-UNTELS)
    # ==========================================================
    vri_keywords = [
        "investigación", "proyecto", "propiedad intelectual", "ética", "docente investigador",
        "subvención", "fondo editorial", "líneas de investigación", "grupo de investigación",
        "centro", "instituto", "rendición", "viáticos", "grado académico", "título profesional",
        "convenio", "pei", "pia", "plan", "directiva", "guía", "manual", "código", "reglamento",
        "untels", "vri", "comité de ética", "publicación", "tesis", "ensayo", "innovación", "artículo", "ley", "estatuto",
    ]
    should_search = any(keyword in user_message_content.lower() for keyword in vri_keywords)

    if should_search:
        print("🔎 Buscando información VRI-UNTELS en índice FAISS...")
        try:
            vri_results = untels_service.search_untels_info(user_message_content, max_results=20)
            if vri_results:
                context_message_content = "Basado en documentos oficiales del VRI-UNTELS:\n"
                for info in vri_results:
                    context_message_content += f"📘 {info.title}:\n{info.content[:800]}\n\n"
                llm_messages.append(Message(role=ChatRole.system, content=context_message_content.strip()))
            else:
                llm_messages.append(Message(
                    role=ChatRole.system,
                    content="No se hallaron documentos relevantes en el índice FAISS."
                ))
        except Exception as e:
            print("❌ Error durante búsqueda FAISS:")
            traceback.print_exc()
            llm_messages.append(Message(
                role=ChatRole.system,
                content="Error al acceder a la base de datos documental del VRI-UNTELS."
            ))

    # ==========================================================
    # RESPUESTA DEL MODELO OPENAI
    # ==========================================================
    try:
        llm_response = await openai_service.get_chat_completion(
            messages=[msg.dict() for msg in llm_messages]
        )

        print("✅ Respuesta recibida desde OpenAI.")

        try:
            parsed = json.loads(llm_response)
            respuesta = parsed.get("respuesta", "")
            print("→ respuesta (parsed):", llm_response)
            referencias = parsed.get("referencias", [])
        except Exception:
            print("⚠️ La respuesta no vino en formato JSON, se usará texto plano.")
            respuesta = llm_response
            referencias = []

        # ==========================================================
        # ACCIONES RÁPIDAS
        # ==========================================================
        quick_actions: List[QuickAction] = []
        if "requisito" in respuesta.lower():
            quick_actions.append(QuickAction(text="Ver requisitos"))
        if "reglamento" in respuesta.lower():
            quick_actions.append(QuickAction(text="Consultar reglamento"))
        if not quick_actions:
            quick_actions.append(QuickAction(text="Contactar al VRI-UNTELS"))

        # 🔹 Devuelve JSON real, no texto
        return {
            "response": respuesta,
            "references": referencias,
            "is_typing": False,
            "quick_actions": [qa.dict() for qa in quick_actions]
        }

    except Exception as e:
        print("❌ Error al procesar respuesta del modelo:")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generando respuesta del asistente."
        )

# ==========================================================
# RECONSTRUCCIÓN DEL ÍNDICE FAISS
# ==========================================================

@router.get("/rebuild-index", status_code=status.HTTP_200_OK)
def rebuild_index(untels_service: UntelsService = Depends(get_untels_service)):
    """🔄 Reconstruye el índice FAISS con los documentos institucionales del VRI-UNTELS."""
    try:
        msg = untels_service.rebuild_index()
        print("✅ Índice FAISS reconstruido correctamente.")
        return {"message": msg}
    except Exception as e:
        print("❌ Error reconstruyendo índice:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error reconstruyendo índice: {e}")
