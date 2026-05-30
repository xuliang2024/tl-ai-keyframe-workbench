from typing import Any

import httpx


class VolcengineImageError(RuntimeError):
    pass


class VolcengineImageClient:
    def __init__(self, *, api_key: str, base_url: str, model: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def generate(
        self,
        *,
        prompt: str,
        image: str | list[str] | None = None,
        size: str = "4K",
        output_format: str | None = None,
        response_format: str = "url",
        watermark: bool = False,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise VolcengineImageError("ARK_API_KEY is not configured")

        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "size": size,
            "response_format": response_format,
            "watermark": watermark,
            "sequential_image_generation": "disabled",
        }
        if output_format:
            payload["output_format"] = output_format
        if image:
            payload["image"] = image

        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                f"{self.base_url}/images/generations",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

        if response.status_code >= 400:
            raise VolcengineImageError(
                f"Volcengine image request failed: {response.status_code} {response.text}"
            )

        data = response.json()
        if data.get("error"):
            message = data["error"].get("message", "Volcengine image request failed")
            raise VolcengineImageError(message)

        return data
