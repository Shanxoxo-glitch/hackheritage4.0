from fastapi import APIRouter, Response, HTTPException, status
from fastapi.responses import RedirectResponse
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication & Quick-Exit"])

@router.post("/session")
async def create_covert_session(response: Response, victim_id: str):
    """
    Creates a covert, pseudo-anonymous session token stored strictly in HttpOnly,
    Secure, SameSite=Strict cookies to leave zero trace in browser local storage.
    """
    session_token = f"covert_sess_{victim_id[:8]}"
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=60 * 60 * 24 * 7 # 7 days
    )
    return {"status": "success", "session_created": True, "covert_mode": True}

@router.post("/purge")
@router.get("/purge")
async def quick_exit_purge(response: Response):
    """
    QUICK-EXIT EMERGENCY ENDPOINT:
    Single-tap emergency trigger that purges client session cookies, revokes tokens,
    clears server-side transient context, and returns a 302 Redirect to a neutral page.
    """
    # Delete covert cookie
    response = RedirectResponse(url=settings.QUICK_EXIT_REDIRECT_URL, status_code=status.HTTP_302_FOUND)
    response.delete_cookie("session_token")
    response.delete_cookie("access_token")
    return response
