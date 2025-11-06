from openai import AsyncOpenAI
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
import traceback

# Cargar variables de entorno
load_dotenv()

class OpenAIService:
    def __init__(self):
        # Obtener API key desde .env
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("❌ No se encontró la variable de entorno OPENAI_API_KEY.")
        
        # Mostrar configuración detectada
        print("✅ Clave API de OpenAI detectada correctamente.")
        
        # Configurar modelo (por defecto: GPT-4-turbo-nano)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4.1-nano")  # 'gpt-4o-mini' es el equivalente actual al GPT-4-turbo-nano
        print(f"🧠 Modelo configurado: {self.model}")

        # Instanciar cliente asincrónico
        self.client = AsyncOpenAI(api_key=api_key)

    async def get_chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        Envía una conversación al modelo y devuelve la respuesta.
        """
        try:
            print(f"📡 Enviando {len(messages)} mensajes al modelo {self.model}...")
            for m in messages:
                role = m.get("role", "user")
                content_preview = m.get("content", "")[:80].replace("\n", " ")
                print(f" - {role}: {content_preview}...")

            # Llamada al modelo
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
            )

            if response.choices and response.choices[0].message:
                content = response.choices[0].message.content
                print(f"✅ Respuesta recibida ({len(content)} caracteres)")
                print("🗣️ Resumen:", content[:120], "...")
                return content

            print("⚠️ La respuesta no contiene 'choices'.")
            return None

        except Exception as e:
            print("❌ Error al comunicarse con OpenAI:")
            traceback.print_exc()
            return None
