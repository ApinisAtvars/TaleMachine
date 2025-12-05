from fastapi import APIRouter, HTTPException, Request

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.Neo4jNaturalLanguageQuery import MessageRequest
from models.Neo4jGetNodeChapter import Neo4jGetChapterNodeMapping

neo4j_router = APIRouter(prefix="/neo4j", tags=["neo4j"])

@neo4j_router.get("/get_all_nodes_relationships/{database_name}")
async def get_all_nodes_and_relationships(database_name: str, request: Request):
    """Get all nodes and relationships from a Neo4j database"""
    try:
        data = await request.app.state.db.get_all_nodes_and_relationships(database_name)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@neo4j_router.post("/natural_language_query")
async def natural_language_query(request: Request, message: MessageRequest):
    """Perform a natural language query on the Neo4j database"""
    try:
        data = await request.app.state.db.natural_language_query(message.query)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@neo4j_router.post("/get_chapter_node_mapping")
async def get_chapter_node_mapping(request: Request, node: Neo4jGetChapterNodeMapping):
    """Get the chapter node mapping for a given Neo4j node"""
    try:
        data = await request.app.state.db.get_mapping_by_node_label_and_name(node.node_label, node.node_name)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))