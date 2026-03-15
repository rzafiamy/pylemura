"""Final response formatter — mirrors lemura/src/agent/execution/FinalResponseFormatter.ts"""
from __future__ import annotations


class FinalResponseFormatter:
    @staticmethod
    def format(content: str) -> str:
        return content.strip()
