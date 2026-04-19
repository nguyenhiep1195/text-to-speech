from fastapi import APIRouter, HTTPException, status

from ..auth import create_access_token
from ..config import settings
from ..models import LoginRequest, TokenResponse

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    if body.username != settings.TTS_USERNAME or body.password != settings.TTS_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không đúng",
        )
    token = create_access_token(data={"sub": body.username})
    return TokenResponse(access_token=token, username=body.username)
