from langchain_neo4j import Neo4jVector
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
from dotenv import load_dotenv
import os

class Neo4jService:
    def __init__(self, uri: str, user: str, password: str):
        self.graph = Neo4jGraph(
            url=uri,
            username=user,
            password=password
        )
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            google_api_key=os.getenv("GEMINI_API_KEY"),
        )
        