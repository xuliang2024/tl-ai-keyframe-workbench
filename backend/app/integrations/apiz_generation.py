from typing import Any

import httpx


class ApizGenerationError(RuntimeError):
    pass


class ApizGenerationClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        poll_interval_seconds: float = 2,
        max_poll_attempts: int = 90,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.poll_interval_seconds = poll_interval_seconds
        self.max_poll_attempts = max_poll_attempts

    async def generate_image(
        self,
        *,
        model: str,
        prompt: str,
        image: str | list[str] | None = None,
        image_size: str = "16:9",
        resolution: str = "1K",
        quality: str = "high",
        num_images: int = 1,
        output_format: str = "png",
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "prompt": prompt,
            "image_size": "auto" if image else image_size,
            "resolution": resolution,
            "quality": quality,
            "num_images": num_images,
            "output_format": output_format,
        }
        if image:
            params["image_urls"] = image if isinstance(image, list) else [image]

        task = await self._create_task(model=model, params=params)
        result = await self._wait_for_task(task["task_id"])
        images = self._extract_urls(result, key="images")
        return {
            "model": model,
            "provider": "apiz",
            "apiz_task": task,
            "data": [{"url": url, "size": image_size} for url in images],
            "usage": {"price": task.get("price"), "task_id": task["task_id"]},
            "raw_response": result,
        }

    async def generate_video(
        self,
        *,
        model: str,
        prompt: str,
        image: str | list[str] | None = None,
        ratio: str = "16:9",
        duration: int = 4,
        resolution: str = "720p",
        engine_model: str = "seedance2.0_fast_direct",
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "model": engine_model,
            "prompt": prompt,
            "ratio": ratio,
            "duration": duration,
            "resolution": resolution,
        }
        if image:
            params["image_files"] = image if isinstance(image, list) else [image]

        task = await self._create_task(model=model, params=params)
        result = await self._wait_for_task(task["task_id"])
        videos = self._extract_urls(result, key="videos") or self._extract_urls(result, key="video")
        return {
            "model": model,
            "provider": "apiz",
            "apiz_task": task,
            "data": [{"url": url} for url in videos],
            "usage": {"price": task.get("price"), "task_id": task["task_id"]},
            "raw_response": result,
        }

    async def _create_task(self, *, model: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise ApizGenerationError("APIZ_API_KEY is not configured")

        response = await self._post("/tasks/create", {"model": model, "params": params})
        data = self._unwrap_response(response, "APIZ create task failed")
        task_id = data.get("task_id")
        if not task_id:
            raise ApizGenerationError("APIZ create task response is missing task_id")
        return data

    async def _wait_for_task(self, task_id: str) -> dict[str, Any]:
        for _ in range(self.max_poll_attempts):
            response = await self._post("/tasks/query", {"task_id": task_id})
            data = self._unwrap_response(response, "APIZ query task failed")
            status = str(data.get("status", "")).lower()
            if status in {"completed", "success", "succeeded"}:
                return data
            if status in {"failed", "error", "canceled", "cancelled"}:
                error = data.get("error") or data.get("message") or "APIZ task failed"
                raise ApizGenerationError(str(error))

            await self._sleep()

        raise ApizGenerationError(f"APIZ task timed out: {task_id}")

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                f"{self.base_url}{path}",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

        if response.status_code >= 400:
            raise ApizGenerationError(f"APIZ request failed: {response.status_code} {response.text}")
        return response.json()

    async def _sleep(self) -> None:
        import asyncio

        await asyncio.sleep(self.poll_interval_seconds)

    @staticmethod
    def _unwrap_response(response: dict[str, Any], default_message: str) -> dict[str, Any]:
        code = response.get("code")
        if code not in (None, 0, 200, "0", "200"):
            message = response.get("message") or response.get("msg") or default_message
            raise ApizGenerationError(str(message))

        data = response.get("data")
        if not isinstance(data, dict):
            raise ApizGenerationError(default_message)
        return data

    @staticmethod
    def _extract_urls(task: dict[str, Any], *, key: str) -> list[str]:
        candidates = [task.get("result"), task.get("output"), task]
        urls: list[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            value = candidate.get(key)
            if isinstance(value, str):
                if value not in seen:
                    urls.append(value)
                    seen.add(value)
            elif isinstance(value, list):
                for item in value:
                    url = None
                    if isinstance(item, str):
                        url = item
                    elif isinstance(item, dict) and isinstance(item.get("url"), str):
                        url = item["url"]
                    if url and url not in seen:
                        urls.append(url)
                        seen.add(url)
        return urls
