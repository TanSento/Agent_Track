from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import os
import requests


class PushNotificationInput(BaseModel):
    """A message to be sent to the user"""
    message: str = Field(..., description="The message to be sent to the user")

class PushNotificationTool(BaseTool):
    name: str = "Send a push notification"
    description: str = (
        "This tool is used to send a push notification to the user"
    )
    args_schema: Type[BaseModel] = PushNotificationInput

    def _run(self, message: str) -> str:
        pushover_user = os.environ.get("PUSHOVER_USER")
        pushover_token = os.environ.get("PUSHOVER_TOKEN")
        push_url = "https://api.pushover.net/1/messages.json"

        print(f"Push: {message}")
        payload = {
            "token": pushover_token,
            "user": pushover_user,
            "message": message
        }
        requests.post(push_url, data=payload)
        return '{"notification": "ok"}'
