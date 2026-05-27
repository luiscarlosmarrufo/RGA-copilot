"""Deterministic analytics layer (Phase 2).

Pure functions only: ``(DataFrame, params) -> result``. No I/O, no DB, no
external API calls. Every module enforces the ADR-0012 dataset scope guard
before computing.
"""
