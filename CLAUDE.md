# Project rules

## Never use paid services
The owner has said: **never use paid things.** This applies to every task in this project.

- Do not call paid APIs or paid tools, even cheap ones, and do not offer them as an option.
  This includes Composio instant/paid tools (fal.ai, ElevenLabs, Gemini image, GetAnyAPI
  searches), Runway credits, and any other per-call billing.
- Use only free options:
  - Animation: the free Wan 2.2 Hugging Face Space (`scripts/wan_batch.py`; it has a small daily
    ZeroGPU allowance, so if it runs out, wait for the reset) and the free CPU live-motion step
    (`python -m studio livemotion`, cut-outs via BiRefNet-lite, MIT licence).
  - Voice: Kokoro on the CPU (`python -m studio voice`).
  - Pictures: the free placeholder or compositing steps, the owner's own art in `brand/`, or
    existing backgrounds.
- If something truly can't be done for free, say so plainly and stop. Don't propose a paid
  workaround.
- Use only commercially licensed models (EduCrew is a business), e.g. no non-commercial
  licences such as RMBG-1.4.
