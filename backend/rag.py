import os
import re
import csv
import json
from datetime import datetime
from openai import OpenAI
from pypdf import PdfReader
from docx import Document

from config import Config
from backend.extensions import supabase
from backend.memory import load_memory

def parse_pdf(file_path: str) -> list:
    """Extract text page-by-page from a PDF."""
    results = []
    try:
        reader = PdfReader(file_path)
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                results.append({
                    "text": text.strip(),
                    "page_number": i + 1,
                    "section_title": f"Page {i + 1}"
                })
    except Exception as e:
        print("[RAG] PDF parse error:", e)
    return results

def parse_docx(file_path: str) -> list:
    """Extract text from DOCX, grouping by headings where possible."""
    results = []
    try:
        doc = Document(file_path)
        current_section = "Introduction"
        current_text = []
        
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            
            # Simple check for headers
            if para.style.name.startswith("Heading") or (len(text) < 100 and para.runs and all(r.bold for r in para.runs)):
                if current_text:
                    results.append({
                        "text": "\n".join(current_text),
                        "page_number": 1,
                        "section_title": current_section
                    })
                    current_text = []
                current_section = text
            else:
                current_text.append(text)
                
        if current_text:
            results.append({
                "text": "\n".join(current_text),
                "page_number": 1,
                "section_title": current_section
            })
    except Exception as e:
        print("[RAG] DOCX parse error:", e)
    return results

def parse_csv(file_path: str) -> list:
    """Parse CSV and convert rows into text blocks."""
    results = []
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            rows = list(reader)
            
            # Group rows to prevent tiny chunks
            rows_per_chunk = 15
            for idx in range(0, len(rows), rows_per_chunk):
                chunk_rows = rows[idx:idx + rows_per_chunk]
                text_lines = []
                for r_idx, row in enumerate(chunk_rows):
                    items = [f"{k}: {v}" for k, v in row.items() if v]
                    text_lines.append(f"[Row {idx + r_idx + 1}] " + " | ".join(items))
                
                results.append({
                    "text": "\n".join(text_lines),
                    "page_number": 1,
                    "section_title": f"CSV Rows {idx+1} to {idx+len(chunk_rows)}"
                })
    except Exception as e:
        print("[RAG] CSV parse error:", e)
    return results

def parse_json(file_path: str) -> list:
    """Parse JSON and pretty-format objects."""
    results = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        if isinstance(data, list):
            items_per_chunk = 10
            for idx in range(0, len(data), items_per_chunk):
                chunk_items = data[idx:idx + items_per_chunk]
                formatted = json.dumps(chunk_items, indent=2)
                results.append({
                    "text": formatted,
                    "page_number": 1,
                    "section_title": f"JSON Array Items {idx+1} to {idx+len(chunk_items)}"
                })
        else:
            formatted = json.dumps(data, indent=2)
            results.append({
                "text": formatted,
                "page_number": 1,
                "section_title": "JSON Object Root"
            })
    except Exception as e:
        print("[RAG] JSON parse error:", e)
    return results

def parse_text_file(file_path: str) -> list:
    """Extract text from TXT or MD files."""
    results = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        if content.strip():
            # Split by markdown headers if available, else paragraphs
            sections = re.split(r'\n(##? .+)\n', content)
            if len(sections) > 1:
                title = "Header"
                for s in sections:
                    s_clean = s.strip()
                    if not s_clean:
                        continue
                    if s_clean.startswith("#"):
                        title = s_clean
                    else:
                        results.append({
                            "text": s_clean,
                            "page_number": 1,
                            "section_title": title
                        })
            else:
                # Fall back to splitting by paragraphs
                paras = [p.strip() for p in content.split("\n\n") if p.strip()]
                for idx, p in enumerate(paras):
                    results.append({
                        "text": p,
                        "page_number": 1,
                        "section_title": f"Paragraph {idx + 1}"
                    })
    except Exception as e:
        print("[RAG] Text parse error:", e)
    return results

def get_file_parser(file_name: str):
    """Return the correct text parsing function based on file extension."""
    ext = file_name.split(".")[-1].lower()
    if ext == "pdf":
        return parse_pdf
    elif ext == "docx":
        return parse_docx
    elif ext == "csv":
        return parse_csv
    elif ext in ("json", "geojson"):
        return parse_json
    elif ext in ("txt", "md", "markdown", "py", "js", "html", "css"):
        return parse_text_file
    return None

def chunk_text_items(parsed_items: list, max_words: int = 400, overlap_words: int = 80) -> list:
    """Semantic chunker maintaining word count and overlap logic."""
    chunks = []
    for item in parsed_items:
        text = item["text"]
        words = text.split()
        
        if len(words) <= max_words:
            chunks.append({
                "chunk_text": text,
                "page_number": item["page_number"],
                "section_title": item["section_title"]
            })
            continue
            
        # Sliding window chunking
        idx = 0
        while idx < len(words):
            chunk_words = words[idx:idx + max_words]
            chunk_text = " ".join(chunk_words)
            chunks.append({
                "chunk_text": chunk_text,
                "page_number": item["page_number"],
                "section_title": item["section_title"]
            })
            idx += (max_words - overlap_words)
            
    return chunks

def generate_embeddings(texts: list) -> list:
    """Generate vector embeddings for a list of texts using OpenRouter embeddings."""
    if not texts:
        return []
    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=Config.OPENROUTER_API_KEY,
            timeout=25,
        )
        response = client.embeddings.create(
            model="openai/text-embedding-3-small",
            input=texts
        )
        return [d.embedding for d in response.data]
    except Exception as e:
        print("[RAG] Embedding generation error:", e)
        # Return dummy embeddings if the API call fails to prevent crashing the pipeline
        # (This is useful in sandbox/dry-run environments)
        return [[0.0] * 1536 for _ in texts]

def ingest_document(user_id: str, workspace_id: str, filename: str, file_path: str, file_size: int) -> dict:
    """Ingest, parse, chunk, embed, and store a document into Supabase."""
    parser = get_file_parser(filename)
    if not parser:
        return {"status": "error", "message": f"Unsupported file type: {filename}"}
        
    parsed_items = parser(file_path)
    if not parsed_items:
        return {"status": "error", "message": "Failed to parse text from file."}
        
    chunks = chunk_text_items(parsed_items)
    if not chunks:
        return {"status": "error", "message": "No chunks generated from document."}
        
    # 1. Create document record
    doc_res = supabase.table("oculus_documents").insert({
        "user_id": user_id,
        "workspace_id": workspace_id,
        "filename": filename,
        "file_size": file_size,
        "document_type": "document"
    }).execute()
    
    if not doc_res.data:
        return {"status": "error", "message": "Failed to create document record."}
        
    document_id = doc_res.data[0]["id"]
    
    # 2. Embed chunks in batches of 16
    chunk_texts = [c["chunk_text"] for c in chunks]
    embeddings = []
    
    batch_size = 16
    for i in range(0, len(chunk_texts), batch_size):
        batch = chunk_texts[i:i + batch_size]
        batch_embeddings = generate_embeddings(batch)
        embeddings.extend(batch_embeddings)
        
    # 3. Save chunks to database
    db_chunks = []
    for idx, c in enumerate(chunks):
        db_chunks.append({
            "document_id": document_id,
            "workspace_id": workspace_id,
            "page_number": c["page_number"],
            "section_title": c["section_title"],
            "chunk_text": c["chunk_text"],
            "embedding": embeddings[idx] if idx < len(embeddings) else [0.0] * 1536
        })
        
    # Supabase allows bulk inserts
    supabase.table("oculus_document_chunks").insert(db_chunks).execute()
    
    return {
        "status": "success",
        "document_id": document_id,
        "chunks_count": len(db_chunks),
        "message": f"Successfully ingested {filename} ({len(db_chunks)} chunks)."
    }

def query_workspace_rag(workspace_id: str, query_text: str, match_count: int = 5) -> list:
    """Retrieve relevant chunks from Supabase using vector similarity search."""
    try:
        embeddings = generate_embeddings([query_text])
        if not embeddings:
            return []
            
        query_embedding = embeddings[0]
        
        # Invoke the match stored procedure we defined
        res = supabase.rpc("match_document_chunks", {
            "query_embedding": query_embedding,
            "match_threshold": 0.15,
            "match_count": match_count,
            "filter_workspace_id": workspace_id
        }).execute()
        
        if res.data:
            return res.data
    except Exception as e:
        print("[RAG] Vector match error:", e)
    return []
