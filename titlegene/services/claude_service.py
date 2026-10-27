"""Backward-compatible names for integrations using the old Claude-only module."""

from titlegene.services.llm_service import LLMAPIError, LLMService

ClaudeService = LLMService
ClaudeAPIError = LLMAPIError

__all__ = ["ClaudeAPIError", "ClaudeService"]
