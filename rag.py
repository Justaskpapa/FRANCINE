import os
from pathlib import Path
from typing import List, Tuple, Union
import faiss
import numpy as np
import glob
import json
import asyncio

import llm
# FIX: Dynamically determine BASE_DIR based on the new BASE_DIR from memory.py
# Assuming memory.py is imported and its BASE_DIR is the source of truth
import memory
BASE_DIR = memory.BASE_DIR
IDX_DIR = BASE_DIR / "faiss_idx"
IDX_DIR.mkdir(parents=True, exist_ok=True)
INDEX_PATH = IDX_DIR / "docs.index"
DOC_MAP_PATH = IDX_DIR / "doc_map.json" # To store mapping of index ID to original text

CONSTITUTION_PATH = BASE_DIR / "constitution.txt"
CORE_MEMORY_PATH = BASE_DIR / "core_memory.json"
MEM_LOG_PATH = BASE_DIR / "memlog.txt" # For reflecting on recent memory

async def build_rag_index(docs_path: str = "documents_to_index"): # FIX: docs_path is now relative to BASE_DIR
    """
    Builds a FAISS index from text documents, constitution, and core memory insights
    using embeddings from llm.ollama_embed.
    This function should be run ONCE to create or rebuild your RAG index.
    """
    print(f"--- Starting RAG Index Building from {docs_path} and internal memory ---")
    
    all_texts_to_index = []
    
    # 1. Add user-provided documents
    # FIX: docs_to_index_path is now relative to BASE_DIR
    docs_to_index_path = BASE_DIR / docs_path
    if docs_to_index_path.exists():
        for file_path in glob.glob(str(docs_to_index_path / "*.txt")):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    all_texts_to_index.append(f"--- User Document: {Path(file_path).name} ---\n{content}")
                print(f"Loaded document: {Path(file_path).name}")
            except Exception as e:
                print(f"Error loading document {file_path}: {e}")
    else:
        print(f"Document indexing path '{docs_to_index_path}' does not exist. Skipping user documents.")

    # 2. Add Constitution content
    if CONSTITUTION_PATH.exists():
        try:
            with open(CONSTITUTION_PATH, 'r', encoding='utf-8') as f:
                constitution_content = f.read()
                all_texts_to_index.append(f"--- Francine's Constitution ---\n{constitution_content}")
            print(f"Loaded constitution: {CONSTITUTION_PATH.name}")
        except Exception as e:
            print(f"Error loading constitution: {e}")

    # 3. Add Core Memory insights
    if CORE_MEMORY_PATH.exists():
        try:
            with open(CORE_MEMORY_PATH, 'r', encoding='utf-8') as f:
                core_memory_data = json.load(f)
                insights = core_memory_data.get("core_insights", [])
                if insights:
                    for insight in insights:
                        all_texts_to_index.append(f"--- Core Memory Insight ---\n{insight}")
                    print(f"Loaded {len(insights)} core memory insights.")
        except json.JSONDecodeError:
            print("Warning: core_memory.json is corrupted. Skipping core memory insights for RAG.")
        except Exception as e:
            print(f"Error loading core memory: {e}")

    # 4. Add recent interactions from memlog.txt (as a general memory context)
    if MEM_LOG_PATH.exists():
        try:
            with open(MEM_LOG_PATH, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                recent_interactions_content = "\n".join(lines[-50:])
                if recent_interactions_content.strip():
                    all_texts_to_index.append(f"--- Recent Conversation Log ---\n{recent_interactions_content}")
                    print(f"Loaded recent memlog interactions.")
        except Exception as e:
            print(f"Error loading recent memlog for RAG: {e}")


    if not all_texts_to_index:
        print("No text content found to index. FAISS index not built.")
        return

    print(f"Generating embeddings for {len(all_texts_to_index)} text chunks using Ollama (minilm:latest) concurrently...")
    
    # FIX: Removed asyncio.to_thread as llm.ollama_embed is already async
    embedding_tasks = [llm.ollama_embed(text_chunk) for text_chunk in all_texts_to_index]
    embeddings_list_of_lists = await asyncio.gather(*embedding_tasks, return_exceptions=True)
    
    embeddings = []
    doc_map = {} 

    for i, embed_result in enumerate(embeddings_list_of_lists):
        if isinstance(embed_result, list) and embed_result: # Check if it's a valid embedding list
            embeddings.append(embed_result)
            doc_map[i] = all_texts_to_index[i] # Store the text chunk itself
        else:
            print(f"Warning: Failed to get embedding for chunk {i} (Error: {embed_result}). Skipping.")

    if not embeddings:
        print("No embeddings could be generated. FAISS index not built.")
        return

    embeddings_np = np.array(embeddings, dtype=np.float32)
    d = embeddings_np.shape[1]

    index = faiss.IndexFlatL2(d)
    index.add(embeddings_np)

    faiss.write_index(index, str(INDEX_PATH))
    
    # Save the document map
    with open(DOC_MAP_PATH, 'w', encoding='utf-8') as f:
        json.dump(doc_map, f, indent=2)

    print(f"FAISS index built and saved to {INDEX_PATH}")
    print(f"Document map saved to {DOC_MAP_PATH}")
    print(f"Indexed {len(embeddings)} text chunks.")

async def get_relevant_context(query: str, k: int = 3) -> str:
    """
    Queries the FAISS index for relevant contextual information (documents, constitution, core memory).
    Returns a concatenated string of relevant text chunks.
    """
    if not INDEX_PATH.exists() or not DOC_MAP_PATH.exists():
        print("RAG index or document map not found. Cannot retrieve context.")
        return ""

    try:
        index = faiss.read_index(str(INDEX_PATH))
        with open(DOC_MAP_PATH, 'r', encoding='utf-8') as f:
            doc_map = json.load(f)
    except Exception as e:
        print(f"Error loading RAG index or document map: {e}")
        return ""

    embedding_list = await llm.ollama_embed(query)
    if not embedding_list:
        print("Failed to get embedding from Ollama for context query.")
        return ""

    embedding = np.array([embedding_list], dtype=np.float32)

    D, I = index.search(embedding, k)
    
    relevant_chunks = []
    for idx, score in zip(I[0], D[0]):
        if idx in doc_map:
            # Only add if score is above a certain threshold (optional, for relevance)
            # For now, we'll just add the top K
            relevant_chunks.append(doc_map[str(idx)]) # doc_map keys are strings from JSON dump
            
    if relevant_chunks:
        print(f"Retrieved {len(relevant_chunks)} relevant context chunks.")
        return "\n\n--- Retrieved Context ---\n" + "\n\n".join(relevant_chunks) + "\n--- End Retrieved Context ---"
    else:
        return ""
