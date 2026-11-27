"""Image-to-video via the Wan 2.2 Hugging Face Space (fast fp8 build on ZeroGPU).

Space: zerogpu-aoti/wan2-2-fp8da-aoti-faster, endpoint /generate_video
Needs `pip install gradio_client`. ZeroGPU Spaces have a per-account daily GPU quota.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from .base import AnimateProvider

SPACE = "zerogpu-aoti/wan2-2-fp8da-aoti-faster"


class WanAnimate(AnimateProvider):
    def __init__(self, steps: int = 6, seed: int | None = 42, space: str = SPACE, **kw):
        super().__init__(**kw)
        self.steps, self.seed, self.space = steps, seed, space
        self._client = None

    def _get_client(self):
        if self._client is None:
            from gradio_client import Client
            self._client = Client(self.space, hf_token=os.environ.get("HF_TOKEN"))
        return self._client

    def animate(self, image: Path, prompt, negative, duration, out_path: Path, label=""):
        from gradio_client import handle_file

        video, _seed = self._get_client().predict(
            input_image=handle_file(str(image)),
            prompt=prompt,
            steps=self.steps,
            negative_prompt=negative,
            duration_seconds=duration,
            guidance_scale=1,
            guidance_scale_2=1,
            seed=self.seed if self.seed is not None else 42,
            randomize_seed=self.seed is None,
            api_name="/generate_video",
        )
        src = video["video"] if isinstance(video, dict) else video
        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, out_path)
        return out_path
