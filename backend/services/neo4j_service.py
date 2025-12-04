from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.graph_transformers import LLMGraphTransformer
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_community.graphs.graph_document import GraphDocument, Node, Relationship
import os
import re

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
        self.nodes_list = [ # The list of all possible node labels - across all stories
            "Person", "Character", "Creature", "Alien", "Robot", "AI", "Deity", "Spirit", "Undead", "Plant",
            "Organization", "Faction", "Family", "Kingdom", "Guild", "Cult", "Corporation", "Army", "Crew", "Race",
            "Location", "World", "City", "Building", "Room", "Region", "Universe", "Landmark", "Vehicle", "Spaceship",
            "Item", "Weapon", "Artifact", "Technology", "Book", "Clue", "Key", "Treasure", "Food", "Drug",
            "Event", "Scene", "Era", "Goal", "Obstacle", "Secret", "Prophecy", "Skill", "Law", "Disease"
        ]
        self.rels_list = [ # The list of all possible relationship types - across all stories
            "LOVES", "HATES", "FEARS", "TRUSTS", "SUSPECTS", "ENVIES", "PITIES", "RESPECTS", "DESPISES", "ADMIRES", 
            "WORSHIPS", "KNOWS", "REMEMBERS", "FORGETS", "IS_OBSESSED_WITH", "PARENT_OF", "CHILD_OF", "SIBLING_OF", 
            "MARRIED_TO", "DIVORCED_FROM", "ANCESTOR_OF", "DESCENDANT_OF", "ADOPTED", "MENTORS", "APPRENTICE_OF", 
            "FRIEND_OF", "ENEMY_OF", "RIVAL_OF", "LEADS", "MEMBER_OF", "FIGHTS", "KILLS", "WOUNDS", "CAPTURES", 
            "TORTURES", "IMPRISONS", "HUNTED_BY", "AMBUSHES", "THREATENS", "DEFEATS", "BETRAYS", "REBELS_AGAINST", 
            "DESTROYED", "SABOTAGES", "HELPS", "HEALS", "RESCUES", "PROTECTS", "ADVISES", "EMPLOYS", "SERVES", 
            "SUMMONS", "REVIVES", "TALKS_TO", "ARGUES_WITH", "LIES_TO", "PERSUADES", "COMMANDS", "INFORMS", 
            "BLACKMAILS", "INTERROGATES", "REVEALS", "HIDES", "INVESTIGATES", "DISCOVERS", "LIVES_IN", "BORN_IN", 
            "DIED_AT", "VISITS", "TRAVELS_TO", "ESCAPES_FROM", "IS_LOCATED_AT", "CONTAINS", "BORDERS", "GUARDS", 
            "OWNS", "STEALS", "FOUND", "LOST", "CREATED", "WROTE", "INVENTED", "WEARS", "USES", "CONSUMES", 
            "CAUSES", "PREVENTS", "TRIGGERS", "SOLVES", "COMPLICATES", "MOTIVATES", "FULFILLS", "FAILS", 
            "TRANSFORMS_INTO", "CASTS", "CURSES", "INFECTS", "HACKS", "PILOTS", "TELEPORTS_TO"
        ]
        self.node_props_list = [
            "name (string): The primary identifier.",
            "description (string): A short summary of visual or narrative details.",
            "status (string): E.g., 'Alive', 'Destroyed', 'Hidden'.",
            "role (string): E.g., 'King', 'Protagonist', 'Antagonist'.",
            "age (string): The age or era of the entity.",
            "traits (list): Key personality or physical traits."
        ]
        self.rel_props_list = [
            "context (string): Explains 'why' or 'how' connected.",
            "strength (integer): 1-10 scale of intensity.",
            "since (string): When this started.",
            "status (string): E.g., Active, Broken, Secret."
        ]
        self.llm_transformer = LLMGraphTransformer(
            llm=self.llm,
            allowed_nodes=self.nodes_list,
            allowed_relationships=self.rels_list,
            node_properties=["name", "description", "status", "role", "age", "traits"],
            relationship_properties=["context", "strength", "since", "status"],
        )

    async def create_new_database(self, database_name):
        """
        Creates a new, empty database and configures the LLM to use 
        your strict list of Nodes and Relationships.
        """
        # 1. Sanitize the name first
        final_db_name = self._sanitize_db_name(database_name)

        if await self.check_database_exists(final_db_name):
            raise Exception(f"[ERROR] A Neo4j database with the name {final_db_name} already exists.")
        
        print(f"[INFO] Sanitized '{database_name}' -> '{final_db_name}'")

        # 2. Create the physical database
        # We must access the driver directly to hit the 'system' database
        driver = self.db_graph._driver
        
        try:
            # Note: The standard Neo4j Python driver is synchronous. 
            # Unless you are explicitly using AsyncGraphDatabase, this block is blocking.
            with driver.session(database="system") as session:
                session.run(f"CREATE DATABASE {final_db_name} IF NOT EXISTS WAIT")
        except Exception as e:
            raise Exception(f"[ERROR] Failed to create database '{final_db_name}': {e}")

        # 3. Point the wrapper to this new database
        # (Assuming connect_to_existing_database is async based on your snippet)
        await self.connect_to_existing_database(final_db_name)
        
        print(f"[SUCCESS] Created and connected to '{final_db_name}'")
        
        # 4. Return the final name so your app knows what it ended up being
        return final_db_name

    async def connect_to_existing_database(self, database_name):
        """
        Switches the active database and injects the custom schema 
        so the LLM knows the rules.
        """

        # Switch the target database for future queries
        self.db_graph._database = database_name
        # Inject our custom schema definition
        self._inject_custom_schema()

    # We don't need to refresh the schema from the DB, we have our own definition
    def _inject_custom_schema(self):
        
        # --- 1. Universal NODE Properties ---
        node_props = self.node_props_list
        node_props_str = "\n".join([f"  - {p}" for p in node_props])

        # --- 2. Universal RELATIONSHIP Properties ---
        
        rel_props = self.rel_props_list
        rel_props_str = "\n".join([f"  - {p}" for p in rel_props])

        # --- 3. Lists ---
        nodes_formatted = ", ".join(self.nodes_list)
        rels_formatted = ", ".join(self.rels_list)

        # --- 4. Construct the Prompt ---
        custom_schema_string = f"""
        This is a storytelling database.
        
        Global Node Properties (Apply to ALL Nodes):
        {node_props_str}

        Global Relationship Properties (Apply to ALL Relationships):
        {rel_props_str}

        Allowed Node Labels:
        {nodes_formatted}

        Allowed Relationship Types:
        {rels_formatted}
        """

        self.db_graph.schema = custom_schema_string
    
    def _sanitize_db_name(self, name):
        """
        Sanitizes a string to be a valid Neo4j database name.
        Rules: 3-63 chars, start with alphanumeric, only alphanumeric/dot/dash.
        """
        # 1. Lowercase
        clean_name = name.lower()
        
        # 2. Replace invalid characters (anything not a-z, 0-9, ., -) with empty string
        clean_name = re.sub(r'[^a-z0-9.-]', '', clean_name)
        
        # 3. Ensure it starts with an alphanumeric char. If not, prepend 'DB'
        if not clean_name or not clean_name[0].isalnum():
            clean_name = f"DB{clean_name}"
            
        # 4. Truncate to 63 chars max
        clean_name = clean_name[:63]
        
        # 5. Remove trailing dots or dashes (cannot end with special char)
        clean_name = clean_name.rstrip(".-")
        
        # 6. Ensure minimum length of 3 chars
        if len(clean_name) < 3:
            clean_name = f"{clean_name}db"
            
        return clean_name
    
    async def delete_database(self, database_name):
        """
        Deletes an existing Neo4j database.
        """
        driver = self.db_graph._driver
        
        try:
            with driver.session(database="system") as session:
                session.run(f"DROP DATABASE {database_name} IF EXISTS WAIT")
            print(f"[SUCCESS] Deleted database '{database_name}'")
        except Exception as e:
            raise Exception(f"[ERROR] Failed to delete database '{database_name}': {e}")
    
    async def check_database_exists(self, database_name) -> bool:
        """
        Checks if a Neo4j database with the given name exists.
        """
        driver = self.db_graph._driver
        
        try:
            with driver.session(database="system") as session:
                result = session.run("SHOW DATABASES")
                databases = [record["name"] for record in result]
                return database_name in databases
        except Exception as e:
            raise Exception(f"[ERROR] Failed to check existence of database '{database_name}': {e}")

    async def insert_story(self, story: str):
        """
        Extracts entities and relationships from the story (in Postgres, chapter) text and inserts them into the database.

        Returns a list of tuples containing (node_label, node_name) for all nodes inserted. This should be uploaded to Postgres.
        """
        graph_documents = await self.llm_transformer.aconvert_to_graph_documents([Document(page_content=story)])
        self.db_graph.add_graph_documents(graph_documents)
        return self.parse_uploaded_graph_documents(graph_documents)
    
    async def query_with_natural_language(self, query: str, top_k: int = 10):
        # So the issue is that we have spent all this time creating a custom schema, but the schema contains
        # only the list of ALLOWED nodes and relationships. The LLM still needs to see which nodes and relationships actually ARE in the database
        # and which properties they have.
        # So, we refresh the schema from the database first. Then perform the query, then set the schema back to our custom one.
        self.db_graph.refresh_schema()  
        print("[DEBUG] Instantiating QA chain...")
        qa_chain = GraphCypherQAChain.from_llm(
            llm=self.llm,
            graph=self.db_graph,
            top_k = top_k,
            allow_dangerous_requests=True, # This NEEDS to be True to run
            return_intermediate_steps=True,
            verbose=True
        )
        print("[DEBUG] QA chain instatniated!")
        result = await qa_chain.ainvoke({"query": query})
        self._inject_custom_schema()  # Restore our custom schema
        return result['result']
    
    def parse_uploaded_graph_documents(self, uploaded_graph_documents: list[GraphDocument]) -> list[tuple[str, str]]:
        """
        Parses uploaded graph documents to extract node label and node name pairs.
        E.g. [("Person", "Alice"), ("Location", "Wonderland"), ...]
        """ 
        node_label_node_name_pairs = []
        for graph_doc in uploaded_graph_documents:
            for node in graph_doc.nodes:
                node_label_node_name_pairs.append((node.type, node.id))
        return node_label_node_name_pairs
    
    async def get_all_nodes_and_relationships(self, database_name: str) -> list[dict]:
        """
        Retrieves all nodes and relationships from the specified database.
        Returns a list of dictionaries representing nodes and relationships.
        """
        await self.connect_to_existing_database(database_name)

        query = "MATCH (n)-[r]->(m) RETURN n, labels(n), r, m, labels(m)"

        return self.db_graph.query(query)

if __name__ == "__main__":
    from langchain_neo4j import Neo4jGraph
    import asyncio
    db_graph = Neo4jGraph(
        url="bolt://localhost:7687",
        username="neo4j",
        password="qwertyui",
        enhanced_schema=True
    )
    neo4j_service = Neo4jService(db_graph)
    asyncio.run(neo4j_service.create_new_database("testdb2"))
    some_story = """The late afternoon sun, a benevolent golden orb, spilled over Elmwood Park, painting the ancient oaks in hues of amber and emerald. A gentle breeze, smelling of freshly cut grass and distant honeysuckle, rustled through the leaves, creating a soft, whispering symphony. This was the stage for Lisa and Emily’s perfect escape. Lisa, ever the planner, had arrived first, a wicker basket swinging from her arm, its contents a delightful mystery. She’d chosen their spot with precision: under the sprawling canopy of a particularly majestic oak, where dappled sunlight danced on the ground and a clear view of the duck pond shimmered in the distance. By the time Emily arrived, a wide-brimmed straw hat perched jauntily on her head, Lisa had already unfurled a cheerful red-and-white checkered blanket, anchoring its corners with their bags. "You're a magician, Lise," Emily declared, dropping her tote and sinking onto the soft fabric with a sigh of contentment. "This is exactly what my soul needed." Lisa grinned, already pulling out the treasures. "Only the best for my favourite picnic companion." First came the sandwiches: delicate cucumber and cream cheese on rye, cut into neat triangles, followed by plump, ruby-red strawberries that gleamed like jewels. A thermos of homemade lemonade, condensation beading on its cool surface, promised sweet refreshment. Then, a small container of Lisa's famous lemon drizzle cake, its sugary glaze sparkling. "Oh, you outdid yourself!" Emily exclaimed, plucking a strawberry and popping it into her mouth. "Pure bliss." They ate slowly, savouring each bite, the quiet hum of the park their only soundtrack. A group of children chased a brightly coloured kite across a distant field, their laughter carried on the breeze. A lone dog trotted past, its tail wagging a friendly rhythm. "Remember that time we tried to have a picnic by the river," Emily mused, a smile playing on her lips, "and a rogue gust of wind stole our entire blanket, sandwiches and all?" Lisa chuckled, a warm, melodic sound. "And we ended up chasing it halfway to the bridge, looking like two madwomen!" She shook her head, the memory still vivid. "This is much more civilized." As if on cue, a tiny, audacious squirrel, emboldened by their stillness, crept closer, its beady eyes fixed on the lemon cake. Emily, noticing its approach, tore off a tiny piece of bread and tossed it gently a few feet away. The squirrel, after a moment of cautious assessment, darted forward, snatched its prize, and vanished up the oak tree in a blur of grey fur. "Nature's little tax collector," Emily quipped, leaning back on her elbows, her gaze drifting towards the pond where a family of ducks glided serenely. Lisa watched her friend, a quiet contentment settling over her. Emily’s face, framed by the straw hat, was relaxed, her eyes sparkling with a gentle joy. It wasn't just the perfect weather or the delicious food; it was the shared silence, the easy laughter, the unspoken understanding that flowed between them. As the sun began its slow descent, casting long, dramatic shadows across the grass, they packed up, leaving no trace of their presence save for the faint imprint of their blanket. The air grew cooler, carrying the faint scent of evening dew. "Thank you, Lise," Emily said, giving her a warm hug. "This was exactly what I needed." Lisa smiled, the golden light catching in her hair. "Anytime, Em. Anytime." And as they walked away, the park slowly emptying around them, they carried with them not just the lingering taste of strawberries and lemonade, but the quiet, profound joy of a perfect afternoon spent in the company of a cherished friend."""
    result = asyncio.run(neo4j_service.insert_story(some_story))
    print("Inserted story graph documents:", result)
    result = asyncio.run(neo4j_service.query_with_natural_language("What did the two girls eat at their picnic?", top_k=5))
    print("Query result:", result)