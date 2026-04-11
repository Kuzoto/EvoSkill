"""OpenCode SDK harness — option building, server management, and execution."""

from .options import build_opencode_options
from .executor import execute_query, parse_response

__all__ = ["build_opencode_options", "execute_query", "parse_response"]
