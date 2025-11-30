from langchain_neo4j import Neo4jVector
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

class Neo4jService:
    def __init__(self, db_graph: Neo4jGraph):
        load_dotenv()
        self.db_graph = db_graph
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            google_api_key=os.getenv("GEMINI_API_KEY"),
        )
    
    def connect_to_database(self, database_name):
        # First, check if database exists by querying for it
        res = self.db_graph.query(f"SHOW DATABASES YIELD name WHERE name = '{database_name}' RETURN count(*) > 0")
        print(res)
        # self.db_graph._database = database_name
        # self.db_graph.refresh_schema()

if __name__ == "__main__":
    from langchain_neo4j import Neo4jGraph
    db_graph = Neo4jGraph(
        url="bolt://localhost:7687",
        username=os.getenv("NEO4J_USERNAME"),
        password=os.getenv("NEO4J_PASSWORD"),
        database="neo4j"  # Default database to connect to
    )
    neo4j_service = Neo4jService(db_graph)
    neo4j_service.connect_to_database("test_story_db")