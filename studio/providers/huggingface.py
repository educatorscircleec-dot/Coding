"""Keyframes via Hugging Face Inference (text-to-image).

Needs `pip install huggingface_hub` and a token in HF_TOKEN (in this cloud
environment the network proxy supplies the token for huggingface.co).
"""

from __future__ import annotations

import os
from pathlib import Path

from .base import KeyframeProvider


class HFKeyframes(KeyframeProvider):
    def __init__(self, model: str = "black-forest-labs/FLUX.1-schnell", **kw):
        super().__init__(**kw)
        self.model = model

    def generate(self, prompt, negative, out_path: Path, label=""):
        from huggingface_hub import InferenceClient

        client = InferenceClient(token=os.environ.get("HF_TOKEN", "hf_proxy_injected"))
        img = client.text_to_image(
            prompt,
            negative_prompt=negative or None,
            model=self.model,
            width=self.width,
            height=self.height,
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(out_path)
        return out_path
