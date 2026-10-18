from abc import ABC, abstractmethod
from typing import Generator, List, Dict, Any, Optional, Callable

class AIProvider(ABC):
    """
    Abstract AI Provider Interface.
    Decouples UI and Voice Engine from specific AI backends.
    """
    @abstractmethod
    def initialize(self, api_key: str, model_name: str, **kwargs) -> bool:
        """Initializes the AI client."""
        pass

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """Tests API key and endpoint health."""
        pass

    @abstractmethod
    def generate_response(self, prompt: str,
                          context: Optional[List[Dict[str, str]]] = None,
                          system_instruction: Optional[str] = None,
                          stream: bool = True,
                          tools: Optional[List[Callable]] = None) -> Generator[Dict[str, Any], None, None]:
        """
        Generates streaming or batch response.
        Yields dicts with:
        - type: 'chunk' | 'tool_call' | 'tool_result' | 'complete' | 'error'
        - content: str or dict
        """
        pass

    @abstractmethod
    def cancel_request(self):
        """Cancels an in-flight request if supported."""
        pass
