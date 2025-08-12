"""
Consolidated DSPy and Embeddings Service
Centralizes DSPy initialization logic and embedding provider setup
for all agents in the tendering application.
"""

import os
import logging
import requests
import subprocess
from typing import Optional, Tuple, Dict, Any

import dspy
from .embedding import get_embeddings_provider

logger = logging.getLogger(__name__)


class DSPyService:
    """
    Centralized service for DSPy and embeddings initialization.
    Handles thread safety, provider selection, and configuration management.
    """
    
    _instance = None
    _initialized = False
    _embeddings_provider = None
    _provider_info = {}
    
    def __new__(cls):
        """Singleton pattern to ensure thread safety"""
        if cls._instance is None:
            cls._instance = super(DSPyService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the service only once"""
        if not DSPyService._initialized:
            self.dspy_configured = False
            self.llm_provider = None
            self.llm_model = None
            DSPyService._initialized = True
    
    def initialize_dspy_and_embeddings(self, 
                                     provider: str = "auto", 
                                     model: Optional[str] = None,
                                     llm_provider: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Initialize both DSPy and embeddings with the specified providers.
        
        Args:
            provider: Embedding provider ("auto", "openai", "ollama")
            model: Specific model to use for embeddings
            llm_provider: LLM provider for DSPy ("auto", "openai", "ollama")
            
        Returns:
            Tuple of (success: bool, info: dict)
        """
        try:
            # Initialize embeddings first
            if not DSPyService._embeddings_provider:
                embeddings, used_provider, used_model = get_embeddings_provider(provider, model)
                DSPyService._embeddings_provider = embeddings
                DSPyService._provider_info = {
                    "embedding_provider": used_provider, 
                    "embedding_model": used_model
                }
                logger.info(f"Proveedor de embeddings inicializado: {used_provider} ({used_model})")
            
            # Initialize DSPy based on provider preference
            if not self.dspy_configured:
                effective_llm_provider = llm_provider or provider or "auto"
                
                if effective_llm_provider == "auto":
                    if DSPyService._provider_info.get("embedding_provider") == "ollama":
                        success = self._initialize_dspy_ollama(model)
                    else:
                        success = self._initialize_dspy_openai(model)
                elif effective_llm_provider == "ollama":
                    success = self._initialize_dspy_ollama(model)
                elif effective_llm_provider == "openai":
                    success = self._initialize_dspy_openai(model)
                else:
                    raise ValueError(f"Proveedor LLM no soportado: {effective_llm_provider}")
                
                if success:
                    self.dspy_configured = True
                    DSPyService._provider_info["llm_provider"] = self.llm_provider
                    DSPyService._provider_info["llm_model"] = self.llm_model
            
            return True, DSPyService._provider_info
            
        except Exception as e:
            logger.error(f"Error inicializando DSPy y embeddings: {e}")
            return False, {"error": str(e)}
    
    def _initialize_dspy_ollama(self, model: Optional[str] = None) -> bool:
        """Initialize DSPy with Ollama LLM"""
        try:
            # Check if DSPy is already configured to avoid thread conflicts
            try:
                if hasattr(dspy.settings, 'lm') and dspy.settings.lm is not None:
                    logger.info("DSPy ya está configurado, reutilizando configuración existente")
                    self.llm_provider = "ollama"
                    self.llm_model = "existing_configuration"
                    return True
            except Exception:
                pass  # Settings not configured yet
            
            # Verify available models in Ollama
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            
            if response.status_code == 200:
                models_data = response.json()
                available_models = [model_info["name"] for model_info in models_data.get("models", [])]
                
                # Filter embedding models and choose appropriate language model
                language_models = [
                    model for model in available_models 
                    if not any(embed_keyword in model.lower() 
                              for embed_keyword in ['embed', 'embedding'])
                ]
                
                # Choose appropriate language model
                if model and model in language_models:
                    chosen_model = model
                elif any("llama" in model.lower() for model in language_models):
                    chosen_model = next(model for model in language_models if "llama" in model.lower())
                elif language_models:
                    chosen_model = language_models[0]
                else:
                    # If no language models available, download a lightweight one
                    logger.info("No se encontraron modelos de lenguaje. Descargando llama3.2:1b...")
                    subprocess.run(["ollama", "pull", "llama3.2:1b"], check=True)
                    chosen_model = "llama3.2:1b"
                
                # Initialize DSPy with Ollama LLM
                try:
                    from dspy import LM
                    lm = LM(model=f"ollama/{chosen_model}", api_base="http://localhost:11434")
                    dspy.settings.configure(lm=lm)
                    self.llm_provider = "ollama"
                    self.llm_model = chosen_model
                    logger.info(f"DSPy inicializado con Ollama: {chosen_model}")
                    return True
                except RuntimeError as e:
                    if "can only be changed by the thread that initially configured it" in str(e):
                        logger.warning("DSPy ya configurado en otro hilo, continuando con configuración existente")
                        self.llm_provider = "ollama"
                        self.llm_model = "existing_configuration"
                        return True
                    else:
                        raise
            else:
                raise ConnectionError("No se puede conectar a Ollama")
                
        except Exception as e:
            logger.error(f"Error inicializando DSPy con Ollama: {e}")
            # Fallback to OpenAI if available
            return self._initialize_dspy_openai(model)
    
    def _initialize_dspy_openai(self, model: Optional[str] = None) -> bool:
        """Initialize DSPy with OpenAI LLM"""
        try:
            # Check if DSPy is already configured to avoid thread conflicts
            try:
                if hasattr(dspy.settings, 'lm') and dspy.settings.lm is not None:
                    logger.info("DSPy ya está configurado, reutilizando configuración existente")
                    self.llm_provider = "openai"
                    self.llm_model = "existing_configuration"
                    return True
            except Exception:
                pass  # Settings not configured yet
                
            if not os.getenv("OPENAI_API_KEY"):
                raise ValueError("OPENAI_API_KEY no configurado")
            
            try:
                from dspy import LM
                model_name = model or "gpt-3.5-turbo"
                lm = LM(model=f"openai/{model_name}", max_tokens=3000)
                dspy.settings.configure(lm=lm)
                self.llm_provider = "openai"
                self.llm_model = model_name
                logger.info(f"DSPy inicializado con OpenAI: {model_name}")
                return True
            except RuntimeError as e:
                if "can only be changed by the thread that initially configured it" in str(e):
                    logger.warning("DSPy ya configurado en otro hilo, continuando con configuración existente")
                    self.llm_provider = "openai"
                    self.llm_model = "existing_configuration"
                    return True
                else:
                    raise
                    
        except Exception as e:
            logger.error(f"Error inicializando DSPy con OpenAI: {e}")
            return False
    
    def get_embeddings_provider(self):
        """Get the initialized embeddings provider"""
        return DSPyService._embeddings_provider
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the configured providers"""
        return DSPyService._provider_info.copy()
    
    def is_initialized(self) -> bool:
        """Check if the service has been initialized"""
        return self.dspy_configured and DSPyService._embeddings_provider is not None
    
    def reset(self):
        """Reset the service (mainly for testing)"""
        DSPyService._embeddings_provider = None
        DSPyService._provider_info = {}
        self.dspy_configured = False
        self.llm_provider = None
        self.llm_model = None
        logger.info("DSPyService reset")


# Global instance - singleton
dspy_service = DSPyService()


def initialize_dspy_and_embeddings(provider: str = "auto", 
                                 model: Optional[str] = None,
                                 llm_provider: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
    """
    Convenience function to initialize DSPy and embeddings.
    
    Args:
        provider: Embedding provider ("auto", "openai", "ollama")
        model: Specific model to use for embeddings
        llm_provider: LLM provider for DSPy ("auto", "openai", "ollama")
        
    Returns:
        Tuple of (success: bool, info: dict)
    """
    return dspy_service.initialize_dspy_and_embeddings(provider, model, llm_provider)


def get_embeddings_instance():
    """Get the initialized embeddings provider instance"""
    return dspy_service.get_embeddings_provider()


def get_provider_info() -> Dict[str, Any]:
    """Get information about the configured providers"""
    return dspy_service.get_provider_info()


def is_dspy_service_initialized() -> bool:
    """Check if the DSPy service has been initialized"""
    return dspy_service.is_initialized()
