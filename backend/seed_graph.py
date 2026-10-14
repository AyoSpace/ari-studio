import os
import certifi
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()
os.environ["SSL_CERT_FILE"] = certifi.where()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

def seed_database():
    try:
        driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    except Exception:
        fallback_uri = URI.replace("neo4j+s://", "neo4j+ssc://")
        driver = GraphDatabase.driver(fallback_uri, auth=(USER, PASSWORD))

    with driver.session(database="neo4j") as session:
        # Simple atomic writes to comply with Aura Free access rules
        session.run("MERGE (t:Textile {name: 'Aso-Oke'}) SET t.origin = 'Yoruba', t.texture = 'Handwoven Structured'")
        session.run("MERGE (s:Silhouette {name: 'Sculptural Overcoat'}) SET s.drape = 'Architectural'")
        session.run("MERGE (a:Accessory {name: 'Layered Coral Brass Cuffs'}) SET a.material = 'Brushed Brass'")
        
        session.run("""
            MATCH (t:Textile {name: 'Aso-Oke'}), (s:Silhouette {name: 'Sculptural Overcoat'})
            MERGE (t)-[:PAIRS_WITH]->(s)
        """)
        session.run("""
            MATCH (s:Silhouette {name: 'Sculptural Overcoat'}), (a:Accessory {name: 'Layered Coral Brass Cuffs'})
            MERGE (s)-[:ACCENTED_BY]->(a)
        """)
        print("ACIE Knowledge Graph seeded successfully!")
    driver.close()

if __name__ == "__main__":
    seed_database()
    
