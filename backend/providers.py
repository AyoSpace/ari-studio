"""
ARI Studio provider layer (Cloudflare Workers AI edition).

Standard library only, so it needs no extra installs.
Every result says which provider made it and whether it was a fallback.
"""
import asyncio
import base64
import json
import logging
import os
import re
import urllib.error
import urllib.parse
import urllib.request
import zlib
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger("ari")

# .strip() removes invisible line breaks that get copied along with secrets
CF_ACCOUNT_ID = (os.getenv("CF_ACCOUNT_ID") or "").strip()
CF_API_TOKEN = (os.getenv("CF_API_TOKEN") or "").strip()

IMAGE_MODEL = os.getenv("CF_IMAGE_MODEL", "@cf/black-forest-labs/flux-1-schnell")
TEXT_MODEL = os.getenv("CF_TEXT_MODEL", "@cf/meta/llama-3.1-8b-instruct")
IMAGE_TIMEOUT = float(os.getenv("IMAGE_TIMEOUT", "60"))
TEXT_TIMEOUT = float(os.getenv("TEXT_TIMEOUT", "30"))


def cf_configured() -> bool:
    return bool(CF_ACCOUNT_ID and CF_API_TOKEN)


def _cf_run(model: str, payload: dict, timeout: float) -> dict:
    """Blocking call to Cloudflare Workers AI. Never puts the token in an error."""
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{model}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": "Bearer " + CF_API_TOKEN,
            "Content-Type": "application/json",
            "User-Agent": "ari-studio/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Cloudflare HTTP {e.code}: {e.read().decode()[:200]}") from None
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Cloudflare request failed: {type(e).__name__}") from None


def extract_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}


# ----------------------------------------------------------------- images ----
@dataclass
class ImageResult:
    image_url: str
    provider: str
    degraded: bool = False
    errors: list = field(default_factory=list)


def _cf_image(prompt: str) -> str:
    d = _cf_run(IMAGE_MODEL, {"prompt": prompt}, IMAGE_TIMEOUT)
    img = (d.get("result") or {}).get("image")
    if not img:
        raise RuntimeError(f"no image returned: {d.get('errors')}")
    raw = base64.b64decode(img)
    mime = "image/png" if raw[:4] == b"\x89PNG" else "image/jpeg"
    return f"data:{mime};base64,{img}"


def _pollinations_url(prompt: str, seed_text: str) -> str:
    seed = zlib.crc32(seed_text.encode()) % 100000  # stable, unlike hash()
    return (
        f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}"
        f"?width=1024&height=768&seed={seed}&nologo=true&model=flux"
    )


async def generate_image(prompt: str, seed_text: str = "") -> ImageResult:
    errors = []
    if cf_configured():
        try:
            url = await asyncio.wait_for(asyncio.to_thread(_cf_image, prompt), IMAGE_TIMEOUT + 5)
            log.info("--> Cloudflare image success")
            return ImageResult(url, f"cloudflare:{IMAGE_MODEL}")
        except Exception as e:  # noqa: BLE001
            errors.append(str(e) or type(e).__name__)
            log.warning("!!! Cloudflare image failed -> %s", errors[-1])
    else:
        errors.append("Cloudflare is not configured (CF_ACCOUNT_ID / CF_API_TOKEN)")
    # Last resort so the UI never hangs. Flagged so the UI can say so.
    return ImageResult(_pollinations_url(prompt, seed_text), "pollinations", True, errors)


# ------------------------------------------------------------- structured spec
CATEGORIES = {"garment", "jewelry", "styling", "tryon"}
METALS = ["rose gold", "white gold", "yellow gold", "gold", "silver", "platinum", "brass", "copper"]
GEMS = ["diamond", "sapphire", "emerald", "ruby", "pearl", "coral", "amethyst", "opal", "topaz"]
JEWEL_WORDS = ("ring", "necklace", "earring", "bracelet", "pendant", "anklet", "choker", "chain")

SPEC_SYSTEM = """You are the creative director engine of ARI Studio, a design tool for fashion, \
jewelry and styling for creatives anywhere in the world. Convert the user's request into JSON ONLY, \
no prose, no markdown, with exactly these keys:
{"category": "garment|jewelry|styling|tryon",
 "subject": "the main thing to design, short and concrete",
 "must_have": ["specific details the user demanded, each a short phrase, copied faithfully"],
 "materials": ["fabrics/leathers/etc"],
 "metals_gems": ["metals and stones, e.g. rose gold, sapphire"],
 "mood": "a few words",
 "director_note": "two sentences of expert design reasoning"}
Rules: never drop or reinterpret a user-specified detail. Cultural context is inspiration, \
never a restriction. Do not invent details the user did not imply.
must_have holds ONLY details beyond the subject, as complete phrases. Example: for \
'black trousers with a grey leather patch at each ankle' use subject 'black ankle-length \
trousers' and must_have ['grey leather patch at each ankle']. Never split a phrase into words."""


def _list(v):
    return [str(x).strip() for x in v if str(x).strip()] if isinstance(v, list) else []


def _clean_details(items: list, subject: str) -> list:
    """Drop repeats of the subject and fragments of longer phrases (keeps prompts short)."""
    subj = subject.lower()
    out = []
    for it in items:
        low = it.lower()
        if low in subj:
            continue
        if any(low != o.lower() and low in o.lower() for o in items):
            continue
        if low not in [x.lower() for x in out]:
            out.append(it)
    return out


def normalize_spec(raw: dict, prompt: str, display_mode: str, root_lens: str) -> dict:
    cat = raw.get("category")
    subject = str(raw.get("subject") or prompt).strip()
    return {
        "category": cat if cat in CATEGORIES else "garment",
        "subject": subject,
        "must_have": _clean_details(_list(raw.get("must_have")), subject),
        "materials": _list(raw.get("materials")),
        "metals_gems": _list(raw.get("metals_gems")),
        "root_lens": (root_lens or "").strip(),  # user's choice only; never imposed
        "mood": str(raw.get("mood") or "").strip(),
        "display": display_mode,  # the UI toggle always wins
        "director_note": str(raw.get("director_note") or "").strip(),
        "verbatim": prompt,  # the user's own words, kept for the fallback prompt
        "from_llm": bool(raw),
    }


def heuristic_spec(prompt: str, display_mode: str, root_lens: str) -> dict:
    """Used only when the language model is unavailable."""
    low = prompt.lower()
    metals = []
    for m in METALS:  # longest first, so "gold" is skipped when "rose gold" matched
        if m in low and not any(m in other for other in metals):
            metals.append(m)
    gems = [g for g in GEMS if g in low]
    is_jewel = any(w in low for w in JEWEL_WORDS)
    spec = normalize_spec({}, prompt, display_mode, root_lens)
    spec["category"] = "jewelry" if is_jewel else "garment"
    spec["metals_gems"] = metals + gems
    return spec


def _cf_text(system: str, user: str) -> str:
    d = _cf_run(
        TEXT_MODEL,
        {
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "max_tokens": 500,
        },
        TEXT_TIMEOUT,
    )
    out = (d.get("result") or {}).get("response") or ""
    if isinstance(out, (dict, list)):  # Cloudflare sometimes returns JSON already parsed
        out = json.dumps(out)
    return out


async def build_spec(prompt, display_mode, root_lens, refs, kg) -> dict:
    ref_lines = "\n".join(f"- {r['role']}: {r['description']}" for r in refs if r.get("description")) or "none"
    user = (
        f"User request: {prompt}\n"
        f"Reference images:\n{ref_lines}\n"
        f"Optional heritage lens: {root_lens or 'none'}"
    )
    if cf_configured():
        try:
            text = await asyncio.wait_for(asyncio.to_thread(_cf_text, SPEC_SYSTEM, user), TEXT_TIMEOUT + 5)
            raw = extract_json(text)
            if raw:
                return normalize_spec(raw, prompt, display_mode, root_lens)
        except Exception as e:  # noqa: BLE001
            log.warning("spec model failed, using heuristic: %s", e)
    return heuristic_spec(prompt, display_mode, root_lens)


def build_image_prompt(spec: dict) -> str:
    """Short and concrete. The user's own details come first: FLUX weights early words."""
    if spec.get("from_llm"):
        lead = spec["subject"]
        if spec["must_have"]:
            lead += ", with " + " and ".join(spec["must_have"])
    else:
        lead = spec["verbatim"]  # no model available: trust the user's own wording
    parts = [lead]
    if spec["materials"]:
        parts.append("made of " + ", ".join(spec["materials"]))
    if spec["metals_gems"]:
        parts.append("featuring " + ", ".join(spec["metals_gems"]))
    if spec["root_lens"]:
        parts.append(f"rooted in {spec['root_lens']} craft heritage")
    if spec["mood"]:
        parts.append(spec["mood"])
    body = ", ".join(parts)

    if spec["category"] == "jewelry":
        style = "macro jewelry product photograph, soft studio light, true metal reflections, sharp gem facets"
    elif spec["display"] == "human_model":
        style = "editorial fashion photograph of a model wearing it, full outfit visible, studio backdrop, photorealistic fabric"
    else:
        style = "studio product photograph, ghost mannequin, dark studio background, crisp fabric detail"
    return f"{body}. {style}"

