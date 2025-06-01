#!/usr/bin/env python
"""
Script para testar a configuração de chaves de API no AutoMeetAI.

Este script verifica se as chaves de API podem ser carregadas corretamente,
seja do Streamlit Secrets ou do arquivo user_preferences.json.
"""

import os
import sys
from typing import Dict, Any, Optional

# Adiciona o diretório raiz ao PYTHONPATH para importar módulos do projeto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config.user_preferences_provider import UserPreferencesProvider
from src.utils.logging import get_logger, configure_logger

# Configura o logger
configure_logger()
logger = get_logger(__name__)

def test_streamlit_secrets():
    """
    Tenta carregar as chaves de API do Streamlit Secrets.

    Returns:
        Dict[str, str]: Um dicionário com as chaves de API ou None se não encontradas
    """
    try:
        import streamlit as st
        aai_api_key = st.secrets['assemblyai']['api_key']
        openai_api_key = st.secrets['openai']['api_key']

        logger.info("API keys obtidas do Streamlit Secrets")
        return {
            'assemblyai_api_key': aai_api_key,
            'openai_api_key': openai_api_key
        }
    except Exception as e:
        # Log at info level instead of warning since this is expected behavior in many environments
        logger.info(f"Não foi possível obter API keys do Streamlit Secrets: {e}")
        return None

def test_user_preferences():
    """
    Tenta carregar as chaves de API do arquivo user_preferences.json.

    Returns:
        Dict[str, str]: Um dicionário com as chaves de API ou None se não encontradas
    """
    try:
        user_prefs = UserPreferencesProvider()
        aai_api_key = user_prefs.get('assemblyai_api_key')
        openai_api_key = user_prefs.get('openai_api_key')

        if not aai_api_key or not openai_api_key:
            logger.warning("API keys não encontradas em user_preferences.json")
            return None

        logger.info("API keys obtidas de user_preferences.json")
        return {
            'assemblyai_api_key': aai_api_key,
            'openai_api_key': openai_api_key
        }
    except Exception as e:
        logger.error(f"Erro ao carregar user_preferences.json: {e}")
        return None

def main():
    """
    Função principal que testa as diferentes fontes de chaves de API.
    """
    print("Testando configuração de chaves de API para o AutoMeetAI...")

    # Tenta obter as chaves do Streamlit Secrets
    secrets_keys = test_streamlit_secrets()

    # Tenta obter as chaves do user_preferences.json
    prefs_keys = test_user_preferences()

    # Verifica os resultados
    if secrets_keys:
        print("\n✅ Streamlit Secrets: Chaves de API encontradas")
        print(f"  AssemblyAI API Key: {secrets_keys['assemblyai_api_key'][:5]}...{secrets_keys['assemblyai_api_key'][-5:]}")
        print(f"  OpenAI API Key: {secrets_keys['openai_api_key'][:5]}...{secrets_keys['openai_api_key'][-5:]}")
    else:
        print("\n❌ Streamlit Secrets: Chaves de API não encontradas")

    if prefs_keys:
        print("\n✅ user_preferences.json: Chaves de API encontradas")
        print(f"  AssemblyAI API Key: {prefs_keys['assemblyai_api_key'][:5]}...{prefs_keys['assemblyai_api_key'][-5:]}")
        print(f"  OpenAI API Key: {prefs_keys['openai_api_key'][:5]}...{prefs_keys['openai_api_key'][-5:]}")
    else:
        print("\n❌ user_preferences.json: Chaves de API não encontradas")

    # Verifica se pelo menos uma fonte de chaves está disponível
    if not secrets_keys and not prefs_keys:
        print("\n❌ ERRO: Nenhuma chave de API encontrada!")
        print("Por favor, configure suas chaves de API usando um dos métodos descritos no README.")
        return False

    print("\n✅ Configuração de chaves de API concluída com sucesso!")
    print("A aplicação deve iniciar corretamente.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
