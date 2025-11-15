from __future__ import annotations

import os
import uuid
import traceback
from typing import Dict, Any, Optional, List

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# LLMs
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

# --- NEW: Local Storage Imports ---
from tinydb import TinyDB, Query
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document as LangChainDocument


# --------------------------- Config ---------------------------
# --- REMOVED: All ASTRA_DB_... variables ---

# Vectorize config (used for model selection)
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# LLM config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

# --- MODIFIED: Collection names ---
DOCUMENTS_COLLECTION = "documents" # This will be a Chroma collection
TEAMS_COLLECTION = "teams"       # This will be a TinyDB table
AGENTS_COLLECTION = "agents"     # This will be a TinyDB table


# --------------------------- Data Models -----------------------
# (No changes to Pydantic models)

class AgentConfig(BaseModel):
    agent_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    team_id: str
    name: str
    type: str  # triage | faq | debug
    model: Optional[str] = OPENAI_MODEL

class Team(BaseModel):
    team_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    name: str
    description: Optional[str] = None
    agents: Dict[str, AgentConfig] = {}

class DocumentInput(BaseModel):
    text: str = Field(..., description="Raw text body of the document")
    title: Optional[str] = None
    url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# -------------------------- Local DB Setup -----------------

# --- NEW: TinyDB setup for Teams and Agents ---
db = TinyDB('local_app_db.json')
teams_table = db.table(TEAMS_COLLECTION)
agents_table = db.table(AGENTS_COLLECTION)
TeamQuery = Query()
AgentQuery = Query()

# --- NEW: ChromaDB setup for Documents (Vectors) ---
def get_embedding_model():
    """Selects the embedding model based on config."""
    if OPENAI_API_KEY and EMBEDDING_PROVIDER == "openai":
        print(f"Using OpenAI embeddings: {EMBEDDING_MODEL}")
        return OpenAIEmbeddings(model=EMBEDDING_MODEL, api_key=OPENAI_API_KEY)
    
    # Fallback to a local model
    local_model = "all-MiniLM-L6-v2"
    print(f"Warning: Falling back to local embeddings: {local_model}")
    return HuggingFaceEmbeddings(
        model_name=local_model,
        model_kwargs={'device': 'cpu'} # Or 'cuda' if available
    )

# Initialize embeddings
embedding_function = get_embedding_model()

# Initialize Chroma client (persistent)
chroma_client = Chroma(
    collection_name=DOCUMENTS_COLLECTION,
    embedding_function=embedding_function,
    persist_directory="./chroma_db"
)


# -------------------------- LLM Provider -----------------------
def get_llm(model: Optional[str] = None):
    if OPENAI_API_KEY:
        return ChatOpenAI(model=model or OPENAI_MODEL, api_key=OPENAI_API_KEY, temperature=0.2)
    return ChatOllama(model=os.getenv("OLLAMA_MODEL", "llama3.1"), temperature=0.2)


# --------------------------- LangGraph -------------------------

def build_agent_graph(model_name: Optional[str], team_id: str, agent_type: str):
    llm = get_llm(model_name)

    def retrieve_node(state: Dict[str, Any]):
        query = state["query"]
        
        # --- MODIFIED: Search local ChromaDB ---
        # We use relevance score to get a 0-1 similarity, which matches
        # the original code's thresholding logic.
        results_with_scores = chroma_client.similarity_search_with_relevance_scores(
            query,
            k=5,
            filter={"team_id": team_id} # Filter by team_id in metadata
        )
        
        context = ""
        hits = []
        
        for doc, score in results_with_scores:
            # Re-format to match the expected dict structure
            hit_doc = {
                "text": doc.page_content,
                "title": doc.metadata.get("title", ""),
                "url": doc.metadata.get("url", ""),
                "metadata": doc.metadata,
                "_score": score # This is now a relevance score (0-1)
            }
            hits.append(hit_doc)

        return {"context": context, "hits": hits, "query": query}

    

    def generate_node(state: Dict[str, Any]):
        hits = state.get("hits") or []
        top_sim = hits[0]["_score"] if hits and hits[0].get("_score") is not None else 0.0
        
        # This threshold works perfectly with similarity_search_with_relevance_scores
        SIM_THRESHOLD = 0.75 

        context_text = ""
        if hits and top_sim >= SIM_THRESHOLD:
            context_text = "\n\n".join(
                f"Title: {d.get('title','')}\nURL: {d.get('url','')}\nText:\n{d.get('text','')}"
                for d in hits
            )

        system_msg = (
            "You are a helpful assistant that answers STRICTLY AND ONLY using the provided Context.\n"
            "- If the Context is empty OR insufficient to answer, reply exactly with:\n"
            "  \"I don’t know based on the team’s knowledge base.\"\n"
            "- Do not use outside knowledge.\n"
            "- Keep answers concise and quote only the relevant lines from Context."
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_msg),
                ("human", "Question: {query}\n\nContext:\n{context}\n\nAnswer:")
            ]
        )

        llm = get_llm()
        res = (prompt | llm).invoke({"query": state["query"], "context": context_text})

        return {"answer": res.content, "hits": hits}


    sg = StateGraph(dict)
    sg.add_node("retrieve", retrieve_node)
    sg.add_node("generate", generate_node)
    sg.set_entry_point("retrieve")
    sg.add_edge("retrieve", "generate")
    sg.add_edge("generate", END)
    return sg.compile()


# --------------------------- FastAPI ---------------------------
app = FastAPI(title="Local-First Agent Platform (TinyDB + ChromaDB)", version="1.0")


@app.get("/health")
def health():
    try:
        # Check TinyDB
        teams_count = len(teams_table)
        # Check Chroma
        chroma_count = chroma_client._collection.count()
        return {
            "status": "ok", 
            "tinydb_teams": teams_count, 
            "chroma_docs": chroma_count
        }
    except Exception as e:
        return {"status": "degraded", "error": str(e)}

# --- MODIFIED: `create_team` endpoint (uses TinyDB) ---
@app.post("/teams")
def create_team(data: Dict[str, str]):
    name = (data or {}).get("name") or "Untitled Team"
    team = Team(name=name, description=(data or {}).get("description"))
    
    doc_to_insert = team.model_dump(exclude={"agents"})
    
    try:
        # We store the Pydantic-generated team_id as a field
        teams_table.insert(doc_to_insert)
        return {"team_id": team.team_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create team: {e}")

# --- MODIFIED: `list_teams` endpoint (uses TinyDB) ---
@app.get("/teams")
def list_teams():
    try:
        team_docs = teams_table.all()
        return [Team.model_validate(doc) for doc in team_docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list teams: {e}")

# --- MODIFIED: `create_agent` endpoint (uses TinyDB) ---
@app.post("/teams/{team_id}/agents")
def create_agent(team_id: str, data: Dict[str, str]):
    # 1. Check if team exists
    if not teams_table.search(TeamQuery.team_id == team_id):
        raise HTTPException(status_code=404, detail="team not found")
    
    cfg = AgentConfig(
        team_id=team_id,
        name=(data or {}).get("name") or "agent",
        type=(data or {}).get("type", "faq"),
        model=(data or {}).get("model", OPENAI_MODEL),
    )
    
    doc_to_insert = cfg.model_dump()
    
    try:
        agents_table.insert(doc_to_insert)
        return {"agent_id": cfg.agent_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create agent: {e}")

# --- MODIFIED: `ingest_document` endpoint (uses ChromaDB) ---
@app.post("/teams/{team_id}/documents")
def ingest_document(team_id: str, doc: DocumentInput):
    if not teams_table.search(TeamQuery.team_id == team_id):
        raise HTTPException(status_code=44, detail="team not found")
        
    if not doc.text or not doc.text.strip():
        raise HTTPException(status_code=400, detail="missing text")
    try:
        doc_id = uuid.uuid4().hex
        
        # Prepare metadata for Chroma
        metadata = doc.metadata or {}
        metadata["team_id"] = team_id
        metadata["title"] = doc.title or ""
        metadata["url"] = doc.url or ""

        # Add to Chroma. This automatically embeds and inserts.
        chroma_client.add_texts(
            texts=[doc.text],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        # Make sure it's persisted to disk
        chroma_client.persist() 
        
        return {"status": "ok", "team_id": team_id, "doc_id": doc_id}
    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"ChromaDB insert failed: {e}\n{tb}")

@app.get("/debug/vector/{team_id}")
def debug_vector(team_id: str):
    try:
        results = chroma_client.get(
            where={"team_id": team_id},
            include=["metadatas", "embeddings"]
        )
        # Add embedding length for quick check
        if results.get("embeddings"):
            results["embedding_dim"] = len(results["embeddings"][0])
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- MODIFIED: `query_team` endpoint (uses TinyDB) ---
@app.post("/teams/{team_id}/query")
def query_team(team_id: str, payload: Dict[str, Any]):
    # 1. Fetch team from TinyDB
    team_doc = teams_table.get(TeamQuery.team_id == team_id)
    if not team_doc:
        raise HTTPException(status_code=404, detail="team not found")
        
    # 2. Fetch agents for this team from TinyDB
    agent_docs = agents_table.search(AgentQuery.team_id == team_id)
    
    # 3. Populate the Pydantic model
    team = Team.model_validate(team_doc)
    team.agents = {
        agent["agent_id"]: AgentConfig.model_validate(agent) 
        for agent in agent_docs
    }

    query = (payload or {}).get("query")
    if not query:
        raise HTTPException(status_code=400, detail="missing query")
    agent_type = (payload or {}).get("agent_type", "faq")

    agent_cfg = next(iter(team.agents.values()), None)
    model_name = agent_cfg.model if agent_cfg and agent_cfg.model else OPENAI_MODEL

    # The graph builder now uses team_id to filter Chroma search
    graph = build_agent_graph(model_name, team_id, agent_type)
    try:
        result = graph.invoke({"query": query})
        return {"answer": result.get("answer"), "hits": result.get("hits")}
    except Exception:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=tb)


# -------------------------- Example Usage ----------------------
"""
(Your curl commands will work exactly the same as before)

1) Create a team
curl -X POST http://localhost:8000/teams -H 'Content-Type: application/json' \
  -d '{"name":"Infra Team"}'

2) Add an agent (use the team_id from step 1)
curl -X POST http://localhost:8000/teams/TEAM_ID/agents -H 'Content-Type: application/json' \
  -d '{"name":"faq","type":"faq"}'

3) Ingest a document (Chroma does the vectorization locally)
curl -X POST http://localhost:8000/teams/TEAM_ID/documents -H 'Content-Type: application/json' \
  -d '{"title":"API Restart Runbook","text":"To restart the API, run systemctl restart api.service","metadata":{"source":"runbook"}}'

4) Query (Local semantic search + LLM answer)
curl -X POST http://localhost:8000/teams/TEAM_ID/query -H 'Content-Type: application/json' \
  -d '{"query":"How do I restart the API?"}'
"""
