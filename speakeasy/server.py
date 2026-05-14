from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .console import log
from .permission import PermissionRequest, handle_permission
from .speaker import speak


class NotifyRequest(BaseModel):
    message: str


def create_app() -> FastAPI:
    app = FastAPI(title="speakeasy")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/notify")
    async def notify(req: NotifyRequest) -> dict[str, str]:
        message = req.message.strip()
        if not message:
            raise HTTPException(status_code=400, detail="Empty message")
        log("notify", message)
        speak(message)
        return {"status": "ok"}

    @app.post("/permission")
    async def permission(req: PermissionRequest) -> dict[str, object]:
        if not req.tool_name or not req.tool_input:
            raise HTTPException(status_code=400, detail="Missing required fields: tool_name, tool_input")
        decision = handle_permission(req)
        return {
            "hookSpecificOutput": {
                "hookEventName": "PermissionRequest",
                "decision": decision,
            }
        }

    return app
