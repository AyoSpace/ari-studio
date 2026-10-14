import os
import urllib.parse
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import replicate

# Load environment variables
load_dotenv()

# Initialize FastAPI App FIRST before middleware
app = FastAPI(title="ARI Studio Multi-Modal ACIE Engine")

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment credentials
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
TRIPO3D_KEY = os.getenv("TRIPO3D_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Initialize Gemini Client
gemini_client = None
if GEMINI_KEY:
    try:
        from google import genai
        gemini_client = genai.Client(api_key=GEMINI_KEY)
    except Exception as e:
        print(f"Gemini Client Init Note: {e}")

# Initialize Neo4j Driver
neo4j_driver = None
if NEO4J_URI and NEO4J_USERNAME and NEO4J_PASSWORD:
    try:
        from neo4j import GraphDatabase
        neo4j_driver = GraphDatabase.driver(
            NEO4J_URI, 
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )
        print("Connected to Neo4j Knowledge Graph database.")
    except Exception as e:
        print(f"Neo4j Connection Note: {e}")

def query_knowledge_graph(prompt_text: str):
    """
    Queries Neo4j for matching textile nodes, jewelry pairings, and color palettes.
    Provides structured fallback graph context if DB is unpopulated.
    """
    if neo4j_driver:
        try:
            with neo4j_driver.session() as session:
                query = """
                MATCH (t:Textile)-[:PAIRS_WITH]->(j:Jewelry)
                WHERE toLower(t.name) CONTAINS toLower($keyword) 
                   OR toLower(j.name) CONTAINS toLower($keyword)
                RETURN t.name AS textile, j.name AS jewelry, t.palette AS palette
                LIMIT 1
                """
                keyword = prompt_text.split()[0] if prompt_text else "leather"
                result = session.run(query, keyword=keyword).single()
                if result:
                    return {
                        "textile_node": result["textile"],
                        "jewelry_pairing": result["jewelry"],
                        "color_palette": result["palette"] or ["#1A1714", "#4A4E69", "#7A2E22", "#D4AF37"]
                    }
        except Exception as e:
            print(f"Neo4j Query Note: {e}")

    # Fallback knowledge nodes based on prompt context
    lowered = prompt_text.lower()
    if "aso-oke" in lowered or "lagos" in lowered or "streetwear" in lowered:
        return {
            "textile_node": "Structured Metallic Aso-Oke & Heavy Calfskin Leather",
            "jewelry_pairing": "Layered Brushed Brass Ankle Cuffs",
            "color_palette": ["#10121A", "#D4AF37", "#6B2D25", "#3A405A"]
        }
    elif "silk" in lowered or "chiffon" in lowered or "luxe" in lowered:
        return {
            "textile_node": "Hand-Dyed Indigo Adire Silk Satin",
            "jewelry_pairing": "Sculptural Raw Coral & Gold Collar",
            "color_palette": ["#0A1128", "#1C2541", "#475569", "#D4AF37"]
        }
    
    return {
        "textile_node": "Calfskin Leather & Wool Panel Hybrid",
        "jewelry_pairing": "Brushed Brass Hardware Accents",
        "color_palette": ["#1A1714", "#4A4E69", "#7A2E22", "#D4AF37"]
    }

class DesignRequest(BaseModel):
    prompt: str
    display_mode: str = "ghost_mannequin"

@app.get("/")
async def root():
    return {"status": "online", "engine": "ARI Studio ACIE Engine"}

@app.post("/api/synthesize-multimodal")
async def synthesize_multimodal(
    prompt: str = Form(...),
    display_mode: str = Form("ghost_mannequin"),
    fabric_image: UploadFile = File(None)
):
    # 1. Query Knowledge Graph for Cultural & Material Context
    kg_data = query_knowledge_graph(prompt)
    
    fabric_analysis = ""
    
    # 2. Analyze fabric texture upload if present via Gemini 2.5
    if fabric_image and gemini_client:
        try:
            image_bytes = await fabric_image.read()
            from google.genai import types
            res = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    "Analyze this fabric texture/material in 2 sentences.",
                    types.Part.from_bytes(data=image_bytes, mime_type=fabric_image.content_type)
                ]
            )
            if res and res.text:
                fabric_analysis = res.text.strip()
        except Exception as e:
            print(f"Multimodal Fabric Analysis Note: {e}")

    # Construct visual prompt
    enriched_directive = (
        f"{prompt}. Textile Base: {kg_data['textile_node']}. "
        f"Jewelry Match: {kg_data['jewelry_pairing']}."
    )
    if fabric_analysis:
        enriched_directive += f" Fabric Photo Texture: {fabric_analysis}"

    if display_mode == "human_model":
        visual_prompt = (
            f"Editorial high fashion studio portrait of a model wearing {enriched_directive}, "
            "vogue fashion studio backdrop, sharp focus, 8k resolution, photorealistic fabric texture"
        )
    else:
        visual_prompt = (
            f"Studio product photograph of {enriched_directive}, isolated floating garment, "
            "ghost mannequin presentation, crisp details, sharp leather texture, dark studio background, 8k"
        )

    # 3. Visual Generation via Replicate FLUX 1.1 Pro
    image_url = None
    if REPLICATE_TOKEN:
        try:
            print(f"--> Attempting Replicate FLUX call with token: {REPLICATE_TOKEN[:6]}...")
            output = replicate.run(
                "black-forest-labs/flux-1.1-pro",
                input={"prompt": visual_prompt, "aspect_ratio": "4:3"}
            )
            image_url = str(output)
            print("--> Replicate FLUX Success!")
        except Exception as e:
            print(f"!!! REPLICATE FAILURE REASON: {e}")

    # Guaranteed fallback image generator so UI never hangs on Synthesizing
    if not image_url:
        encoded = urllib.parse.quote(visual_prompt)
        seed = abs(hash(prompt + display_mode)) % 100000
        image_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=768&seed={seed}&nologo=true&model=flux"

    # 4. Generate Reasoning via Gemini 2.5
    ai_reasoning = f"Haute-couture structural breakdown for '{prompt}'."
    if gemini_client:
        try:
            res = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=(
                    f"You are the lead AI Creative Director for ARI Studio. Provide a 2-sentence haute-couture analysis for: '{enriched_directive}'."
                )
            )
            if res and res.text:
                ai_reasoning = res.text.strip()
        except Exception as e:
            print(f"Gemini Analysis Note: {e}")

    return {
        "concept_title": f"Synthesized Concept: {prompt.title()}",
        "prompt_received": prompt,
        "ai_reasoning": ai_reasoning,
        "matched_vector_asset": f"Architectural Cut: {prompt.split()[0].title()}",
        "image_url": image_url,
        "glb_model_url": None,
        "textile_node": fabric_analysis if fabric_analysis else kg_data["textile_node"],
        "color_palette": kg_data["color_palette"],
        "jewelry_pairing": kg_data["jewelry_pairing"],
        "status": "success"
    }
