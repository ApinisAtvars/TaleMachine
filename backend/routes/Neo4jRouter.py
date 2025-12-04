from fastapi import APIRouter, HTTPException, Request

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

neo4j_router = APIRouter(prefix="/neo4j", tags=["neo4j"])

@neo4j_router.get("/get_all_nodes_relationships/{database_name}")
async def get_all_nodes_and_relationships(database_name: str, request: Request):
    """Get all nodes and relationships from a Neo4j database"""
    try:
        data = await request.app.state.db.get_all_nodes_and_relationships(database_name)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
