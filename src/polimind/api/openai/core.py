import json
from openai import OpenAI
from typing import Optional, Any

from .content import ContentPart
from .history import ConversationHistory
from .metrics import Metrics


class Chat:
    """
    Clase para manejar una conversación (chat) con un modelo de OpenAI.
    Gestiona el historial mediante nodos con IDs y delega las métricas
    de uso a una clase especializada.
    """

    def __init__(self, openia: OpenAI, model: str = "gpt-5-mini", system_prompt: Optional[str] = None):
        """
        Inicializa la instancia de chat.

        Args:
            openia: Instancia de OpenAI a utilizar para este chat.
            model: Identificador del modelo a utilizar por defecto.
            system_prompt: Instrucciones base opcionales para definir el comportamiento del asistente.
        """
        self.openia = openia
        self.model = model

        self.history = ConversationHistory()
        self.metrics = Metrics()

        if system_prompt:
            self.history.add_system(system_prompt)

    def set_openia(self, openia: OpenAI) -> None:
        """Cambia la instancia activa de OpenAI utilizada para conectarse a la API."""
        self.openia = openia

    def set_system_prompt(self, system_prompt: Optional[str]) -> None:
        """
        Establece un nuevo prompt de sistema en el historial.
        Si se recibe None, desactiva el system prompt activo actual (si existe).
        Cada cambio de system prompt genera un nuevo nodo con su propio ID.
        """
        if system_prompt is None:
            for node in self.history._nodes:
                if node["role"] == "system" and node["active"]:
                    node["active"] = False
            return

        self.history.add_system(system_prompt)

    def set_model(self, model: str) -> None:
        """Cambia el modelo de lenguaje de OpenAI utilizado para las siguientes interacciones."""
        self.model = model

    def copy(self, openia: Optional[OpenAI] = None) -> "Chat":
        """
        Crea y devuelve una copia exacta e independiente del chat actual.
        Alterar la copia no afectará el historial ni las métricas del chat original.

        Args:
            openia: Instancia opcional de OpenAI para usar en la copia.
                    Si es None, se usa la misma instancia del chat original.
        """
        new_chat = Chat(
            openia=openia if openia else self.openia,
            model=self.model
        )

        new_chat.history = self.history.deepcopy()
        new_chat.metrics = self.metrics.deepcopy()

        return new_chat

    def chat(self, *messages: Any) -> str:
        """
        Recibe uno o múltiples mensajes del usuario, los envía al modelo manteniendo el flujo
        de la conversación y devuelve la respuesta.

        Args:
            *messages: Los componentes del mensaje del usuario de forma posicional.

        Returns:
            La respuesta en texto generada por el modelo.
        """
        if not messages:
            raise ValueError("Debes proporcionar al menos un mensaje.")

        if len(messages) == 1 and isinstance(messages[0], str):
            content = messages[0]
        else:
            content = []
            for msg in messages:
                if isinstance(msg, str):
                    content.append({"type": "text", "text": msg})
                elif isinstance(msg, ContentPart):
                    content.append(msg.encode())
                else:
                    raise ValueError(
                        f"Tipo de mensaje no soportado: {type(msg)}")

        user_node_id = self.history.add_user(content)

        try:
            api_messages = self.history.build_messages()
            api_messages.append({"role": "user", "content": content})
            active_ids = self.history.get_active_node_ids() + [user_node_id]

            response = self.openia.chat.completions.create(
                model=self.model,
                messages=api_messages
            )

            assistant_reply = response.choices[0].message.content
            self.history.add_assistant(user_node_id, assistant_reply)

            if response.usage:
                usage_dict = response.usage.model_dump(exclude_none=True)
                self.metrics.log(
                    usage_dict=usage_dict,
                    model=self.model,
                    active_node_ids=active_ids
                )

            return assistant_reply

        except Exception as e:
            raise RuntimeError(
                f"Error al comunicarse con la API de OpenAI: {e}")

    def clear(self, include_system: bool = False) -> None:
        """
        Desactiva los nodos del historial sin eliminarlos y reinicia las métricas.

        Args:
            include_system: Si es True, también desactiva los nodos de sistema.
                            Si es False (por defecto), conserva el system activo actual.
        """
        self.history.clear(include_system=include_system)
        self.metrics.clear()

    def __str__(self) -> str:
        return f"Chat(model='{self.model}', history={self.history}, metrics={self.metrics})"

    def __repr__(self) -> str:
        return self.__str__()

    def save(self, path: str) -> None:
        """
        Guarda el estado completo de la conversación y las métricas en un archivo JSON.
        """
        data = {
            "model": self.model,
            "history": self.history.to_dict(),
            "metrics": self.metrics.to_dict()
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    @classmethod
    def load(cls, path: str, openia: OpenAI) -> "Chat":
        """
        Reconstruye una instancia de Chat desde un archivo JSON guardado previamente.

        Args:
            path: Ruta al archivo JSON con el estado de la conversación.
            openia: Instancia de OpenAI a inyectar en este nuevo objeto.

        Returns:
            Una nueva instancia de Chat completamente hidratada.
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        new_instance = cls(
            openia=openia, model=data.get("model", "gpt-4o-mini"))

        new_instance.history = ConversationHistory.from_dict(
            data.get("history", {}))
        new_instance.metrics = Metrics.from_dict(data.get("metrics", {}))

        return new_instance
