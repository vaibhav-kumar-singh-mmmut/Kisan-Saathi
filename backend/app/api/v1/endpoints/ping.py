"""Simple ping endpoint — used for gateway verification."""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def ping():
    return {"pong": True}
