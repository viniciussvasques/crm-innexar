"""Customer Authentication Module - Package Init"""
from fastapi import APIRouter
from .routes import router

__all__ = ["router"]
