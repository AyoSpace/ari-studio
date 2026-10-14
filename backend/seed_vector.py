import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_KEY = os.getenv("QDRANT_API_KEY")

# Initialize Qdrant Client (fallback to in-memory mode if URL is not provided)
if QDRANT_URL and QDRANT_KEY:
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_KEY)
else:
    client = QdrantClient(":memory:")

COLLECTION_NAME = "fashion_assets"

def init_vector_db():
    # Create collection with 384-dimensional vector space
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )

    # Sample vector representations (384 floats)
    dummy_vector = [0.1] * 384
    
    points = [
        PointStruct(
            id=1,
            vector=dummy_vector,
            payload={
                "title": "Aso-Oke Sculptural Ensemble",
                "culture": "Yoruba/Lagos",
                "texture": "Structured Handwoven",
                "image_url": "/assets/aso_oke_look.jpg"
            }
        ),
        PointStruct(
            id=2,
            vector=dummy_vector,
            payload={
                "title": "Ottoman Silk Kaftan",
                "culture": "Ottoman/Mediterranean",
                "texture": "Fluid Silk Satin",
                "image_url": "/assets/ottoman_silk.jpg"
            }
        )
    ]

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print("Qdrant Vector DB initialized and seeded successfully!")

if __name__ == "__main__":
    init_vector_db()
    