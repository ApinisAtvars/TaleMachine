from langchain_neo4j import Neo4jVector
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

class Neo4jService:
    def __init__(self, uri: str, user: str, password: str):
        load_dotenv()
        self.db_uri = uri
        self.db_user = user
        self.db_password = password
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            google_api_key=os.getenv("GEMINI_API_KEY"),
        )
    
    def connect(self, database_name) -> Neo4jGraph:
        """
        Connect to the Neo4j database with this given name.
        If it doesn't exist, it will be created.
        The database name should be the """
        neo4j_graph = Neo4jGraph(
            uri=self.db_uri,
            user=self.db_user,
            password=self.db_password,
            database=database_name
        )
        return neo4j_graph