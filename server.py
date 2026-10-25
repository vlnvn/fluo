"""Vercel framework entrypoint; frozen inference initializes per warm instance."""
from backend.app import app

__all__ = ['app']
