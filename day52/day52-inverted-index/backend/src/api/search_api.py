from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from fastapi.responses import JSONResponse
from typing import Optional
import logging
import io

logger = logging.getLogger(__name__)
router = APIRouter()

query_engine = None
inverted_index = None

class SearchAPI:
    def __init__(self, query_engine_instance, index_instance):
        global query_engine, inverted_index
        query_engine = query_engine_instance
        inverted_index = index_instance

@router.get("/search")
async def search_logs(q: str = Query(..., description="Search query"), limit: int = Query(50, ge=1, le=1000, description="Maximum results"), offset: int = Query(0, ge=0, description="Results offset")):
    try:
        if not query_engine:
            raise HTTPException(status_code=500, detail="Search engine not initialized")
        
        result = await query_engine.execute_search(q, limit=limit, offset=offset)
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error(f"Search API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/index")
async def add_log_entry(log_data: dict):
    try:
        if not inverted_index:
            raise HTTPException(status_code=500, detail="Index not initialized")
        
        success = await inverted_index.add_document(log_data)
        if success:
            return {"status": "success", "message": "Log entry indexed"}
        else:
            raise HTTPException(status_code=400, detail="Failed to index log entry")
    
    except Exception as e:
        logger.error(f"Index API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_log_file(file: UploadFile = File(...)):
    try:
        if not inverted_index:
            raise HTTPException(status_code=500, detail="Index not initialized")
        
        # Validate file type
        if not file.filename.endswith(('.log', '.txt')):
            raise HTTPException(status_code=400, detail="Only .log and .txt files are allowed")
        
        # Read file content
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File size must be less than 10MB")
        
        # Decode content
        try:
            text_content = content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                text_content = content.decode('latin-1')
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="Unable to decode file content")
        
        # Split into lines and index each line
        lines = text_content.split('\n')
        indexed_count = 0
        
        for i, line in enumerate(lines):
            if line.strip():  # Skip empty lines
                log_entry = {
                    "id": f"{file.filename}_{i+1}",
                    "content": line.strip(),
                    "timestamp": None,  # Could be extracted from log line
                    "metadata": {
                        "source": file.filename,
                        "line_number": i + 1,
                        "file_size": len(content)
                    }
                }
                
                success = await inverted_index.add_document(log_entry)
                if success:
                    indexed_count += 1
        
        # Save index after processing
        await inverted_index.save_to_storage()
        
        return {
            "status": "success",
            "message": f"Successfully indexed {indexed_count} log entries from {file.filename}",
            "file_info": {
                "filename": file.filename,
                "size": len(content),
                "lines_processed": len(lines),
                "lines_indexed": indexed_count
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_index_stats():
    try:
        if not inverted_index:
            raise HTTPException(status_code=500, detail="Index not initialized")
        
        stats = await inverted_index.get_stats()
        return JSONResponse(content=stats)
    
    except Exception as e:
        logger.error(f"Stats API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/suggest")
async def get_suggestions(q: str = Query("", description="Partial query for suggestions"), limit: int = Query(10, ge=1, le=50, description="Maximum suggestions")):
    try:
        if not inverted_index or not q:
            return {"suggestions": []}
        
        suggestions = []
        query_lower = q.lower()
        
        for term in inverted_index.index.keys():
            if term.lower().startswith(query_lower):
                suggestions.append({"term": term, "frequency": inverted_index.term_frequencies.get(term, 0)})
        
        suggestions.sort(key=lambda x: x["frequency"], reverse=True)
        return {"suggestions": suggestions[:limit]}
    
    except Exception as e:
        logger.error(f"Suggestions API error: {e}")
        return {"suggestions": []}
