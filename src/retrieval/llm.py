from __future__ import annotations

from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from core.config import (
    Settings,
    normalized_judge_provider,
    normalized_provider,
    require_judge_llm_credentials,
    require_llm_credentials,
)


def build_llm(settings: Settings, temperature: float = 0.0):
    provider = normalized_provider(settings)
    require_llm_credentials(settings)

    if provider == "gemini":
        return ChatGoogleGenerativeAI(
            model=settings.model_name,
            google_api_key=settings.google_api_key,
            temperature=temperature,
        )
    if provider == "openai":
        return ChatOpenAI(
            model=settings.model_name,
            api_key=settings.openai_api_key,
            temperature=temperature,
        )
    if provider == "anthropic":
        return ChatAnthropic(
            model=settings.model_name,
            api_key=settings.anthropic_api_key,
            temperature=temperature,
        )
    if provider == "openrouter":
        return ChatOpenAI(
            model=settings.model_name,
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            temperature=temperature,
        )
    if provider == "ollama":
        return ChatOllama(
            model=settings.model_name,
            base_url=settings.ollama_base_url,
            temperature=temperature,
        )
    if provider == "custom":
        return ChatOpenAI(
            model=settings.model_name,
            api_key=settings.custom_llm_api_key or "unused",
            base_url=settings.custom_llm_base_url,
            temperature=temperature,
        )
    raise RuntimeError(f"Unsupported LLM provider: {settings.llm_provider}")


def build_judge_llm(settings: Settings, temperature: float = 0.0):
    provider = normalized_judge_provider(settings)
    require_judge_llm_credentials(settings)

    if provider == "gemini":
        return ChatGoogleGenerativeAI(
            model=settings.judge_llm_model,
            google_api_key=settings.google_api_key,
            temperature=temperature,
        )
    if provider == "openai":
        return ChatOpenAI(
            model=settings.judge_llm_model,
            api_key=settings.openai_api_key,
            temperature=temperature,
        )
    if provider == "anthropic":
        return ChatAnthropic(
            model=settings.judge_llm_model,
            api_key=settings.anthropic_api_key,
            temperature=temperature,
        )
    if provider == "openrouter":
        return ChatOpenAI(
            model=settings.judge_llm_model,
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            temperature=temperature,
        )
    if provider == "ollama":
        return ChatOllama(
            model=settings.judge_llm_model,
            base_url=settings.ollama_base_url,
            temperature=temperature,
        )
    if provider == "custom":
        return ChatOpenAI(
            model=settings.judge_llm_model,
            api_key=settings.custom_llm_api_key or "unused",
            base_url=settings.custom_llm_base_url,
            temperature=temperature,
        )
    raise RuntimeError(f"Unsupported Judge LLM provider: {settings.judge_llm_provider}")

