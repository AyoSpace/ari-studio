import asyncio
import logging
import os
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
logging.basicConfig(level=logging.INFO)

import providers  # noqa: E402  (after load_dotenv)

log = logging.getLogger("ari")

app = FastAPI(title="ARI Studio Multi-Modal ACIE Engine")

# In production set ALLOWED_ORIGINS="https://your-app.vercel.app,http://localhost:3000"
_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------ Neo4j ----
neo4j_driver = None
_uri, _user, _pw = (os.getenv(k, "").strip() for k in ("NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"))
if _uri and _user and _pw:
    try:
        from neo4j import GraphDatabase

        neo4j_driver = GraphDatabase.driver(_uri, auth=(_user, _pw))
        log.info("Neo4j driver created.")
    except Exception as e:  # noqa: BLE001
        log.warning("Neo4j connection note: %s", e)

DEFAULT_PALETTE = ["#1A1714", "#4A4E69", "#7A2E22", "#D4AF37"]


def query_knowledge_graph(prompt_text: str, root_lens: str = "") -> dict:
    """Blocking; call via asyncio.to_thread. Enrichment only. (Graph schema fix comes in a later step.)"""
    keywords = [w.strip(".,!?").lower() for w in prompt_text.split() if len(w) > 3]
    if root_lens:
        keywords.append(root_lens.lower())

    if neo4j_driver and keywords:
        try:
            with neo4j_driver.session() as session:
                row = session.run(
                    """
                    MATCH (t:Textile)-[:PAIRS_WITH]->(j:Jewelry)
                    WHERE any(k IN $keywords WHERE toLower(t.name) CONTAINS k
                                               OR toLower(j.name) CONTAINS k)
                    RETURN t.name AS textile, j.name AS jewelry, t.palette AS palette
                    LIMIT 1
                    """,
                    keywords=keywords,
                ).single()
                if row:
                    return {
                        "textile_node": row["textile"],
                        "jewelry_pairing": row["jewelry"],
                        "color_palette": row["palette"] or DEFAULT_PALETTE,
                    }
        except Exception as e:  # noqa: BLE001
            log.warning("Neo4j query note: %s", e)

    low = prompt_text.lower()
    if any(k in low for k in ("aso-oke", "lagos", "streetwear")):
        return {
            "textile_node": "Structured Metallic Aso-Oke & Heavy Calfskin Leather",
            "jewelry_pairing": "Layered Brushed Brass Ankle Cuffs",
            "color_palette": ["#10121A", "#D4AF37", "#6B2D25", "#3A405A"],
        }
    if any(k in low for k in ("silk", "chiffon", "luxe")):
        return {
            "textile_node": "Hand-Dyed Indigo Adire Silk Satin",
            "jewelry_pairing": "Sculptural Raw Coral & Gold Collar",
            "color_palette": ["#0A1128", "#1C2541", "#475569", "#D4AF37"],
        }
    return {
        "textile_node": "Calfskin Leather & Wool Panel Hybrid",
        "jewelry_pairing": "Brushed Brass Hardware Accents",
        "color_palette": DEFAULT_PALETTE,
    }


# ------------------------------------------------------------------ routes ---
@app.get("/")
async def root():
    return {
        "status": "online",
        "engine": "ARI Studio ACIE Engine",
        "cloudflare_configured": providers.cf_configured(),
        "neo4j_configured": neo4j_driver is not None,
        "image_model": providers.IMAGE_MODEL,
    }


@app.post("/api/synthesize-multimodal")
async def synthesize_multimodal(
    prompt: str = Form(...),
    display_mode: str = Form("ghost_mannequin"),
    root_lens: str = Form(""),  # optional heritage lens, e.g. "Yoruba"
    fabric_image: Optional[UploadFile] = File(None),  # accepted; analysed in a later step
    images: List[UploadFile] = File(default=[]),
):
    prompt = prompt.strip()
    if not prompt:
        raise HTTPException(400, "Prompt is empty")

    kg = await asyncio.to_thread(query_knowledge_graph, prompt, root_lens)
    spec = await providers.build_spec(prompt, display_mode, root_lens, [], kg)

    visual_prompt = providers.build_image_prompt(spec)
    log.info("visual_prompt: %s", visual_prompt)
    img = await providers.generate_image(visual_prompt, seed_text=prompt + display_mode)

    return {
        "concept_title": f"Synthesized Concept: {prompt.title()}"[:120],
        "prompt_received": prompt,
        "ai_reasoning": spec["director_note"] or f"Design breakdown for '{prompt}'.",
        "matched_vector_asset": f"Cut: {spec['subject']}"[:80],
        "image_url": img.image_url,
        "glb_model_url": None,
        "textile_node": kg["textile_node"],
        "color_palette": kg["color_palette"],
        "jewelry_pairing": ", ".join(spec["metals_gems"]) or kg["jewelry_pairing"],
        "spec": spec,
        "provider": img.provider,
        "degraded": img.degraded,  # the UI can show a "fallback used / retry" badge
        "provider_errors": img.errors,
        "references_analyzed": False,
        "status": "success",
    }
