import asyncio
import json
import time
import re
from collections import defaultdict, Counter
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class Document:
    id: str
    content: str
    timestamp: str
    metadata: Dict[str, Any]
    indexed_at: float

@dataclass
class PostingList:
    term: str
    documents: List[str]
    term_frequency: Dict[str, int]

class InvertedIndex:
    def __init__(self, tokenizer, storage):
        self.tokenizer = tokenizer
        self.storage = storage
        self.index: Dict[str, PostingList] = {}
        self.documents: Dict[str, Document] = {}
        self.term_frequencies = Counter()
        self.stats = {'total_documents': 0, 'total_terms': 0, 'index_size_mb': 0, 'last_update': None}
        self.term_cache = {}
        self.cache_size_limit = 1000
        self._lock = asyncio.Lock()
    
    async def add_document(self, doc_data: Dict[str, Any]) -> bool:
        async with self._lock:
            try:
                doc_id = doc_data.get('id', f"doc_{len(self.documents) + 1}")
                content = doc_data.get('content', doc_data.get('message', ''))
                
                document = Document(
                    id=doc_id,
                    content=content,
                    timestamp=doc_data.get('timestamp', ''),
                    metadata={k: v for k, v in doc_data.items() if k not in ['id', 'message']},
                    indexed_at=time.time()
                )
                
                tokens = self.tokenizer.tokenize(content)
                if not tokens:
                    return False
                
                self.documents[doc_id] = document
                
                for token in tokens:
                    if token not in self.index:
                        self.index[token] = PostingList(term=token, documents=[], term_frequency={})
                    
                    posting_list = self.index[token]
                    if doc_id not in posting_list.documents:
                        posting_list.documents.append(doc_id)
                        posting_list.term_frequency[doc_id] = tokens.count(token)
                        self.term_frequencies[token] += 1
                
                self.stats.update({
                    'total_documents': len(self.documents),
                    'total_terms': len(self.index),
                    'last_update': time.time()
                })
                
                logger.debug(f"Indexed document {doc_id} with {len(tokens)} terms")
                return True
                
            except Exception as e:
                logger.error(f"Error indexing document: {e}")
                return False
    
    async def search(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            query_terms = self.tokenizer.tokenize(query)
            if not query_terms:
                return []
            
            matching_docs = set()
            for i, term in enumerate(query_terms):
                if term in self.index:
                    term_docs = set(self.index[term].documents)
                    if i == 0:
                        matching_docs = term_docs
                    else:
                        matching_docs = matching_docs.intersection(term_docs)
                else:
                    return []
            
            results = []
            for doc_id in matching_docs:
                if doc_id in self.documents:
                    doc = self.documents[doc_id]
                    score = self._calculate_score(doc, query_terms)
                    
                    result = {
                        'id': doc.id,
                        'content': doc.content,
                        'timestamp': doc.timestamp,
                        'metadata': doc.metadata,
                        'score': score,
                        'highlighted': self._highlight_terms(doc.content, query_terms)
                    }
                    results.append(result)
            
            results.sort(key=lambda x: (-x['score'], -self._parse_timestamp(x['timestamp'])))
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def _calculate_score(self, document: Document, query_terms: List[str]) -> float:
        score = 0.0
        content_lower = document.content.lower()
        
        for term in query_terms:
            tf = content_lower.count(term.lower())
            total_docs = len(self.documents)
            docs_with_term = len(self.index.get(term, PostingList("", [], {})).documents)
            idf = 1.0 if docs_with_term == 0 else total_docs / docs_with_term
            score += tf * idf
        
        return score
    
    def _highlight_terms(self, content: str, query_terms: List[str]) -> str:
        highlighted = content
        for term in query_terms:
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            highlighted = pattern.sub(f'<mark>{term}</mark>', highlighted)
        return highlighted
    
    def _parse_timestamp(self, timestamp: str) -> float:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.timestamp()
        except:
            return 0.0
    
    async def get_stats(self) -> Dict[str, Any]:
        import sys
        index_size = sum(sys.getsizeof(posting_list.documents) + sys.getsizeof(posting_list.term_frequency) for posting_list in self.index.values())
        
        self.stats.update({
            'total_documents': len(self.documents),
            'total_terms': len(self.index),
            'index_size_mb': round(index_size / (1024 * 1024), 2),
            'most_frequent_terms': self.term_frequencies.most_common(10),
            'cache_size': len(self.term_cache)
        })
        
        return self.stats
    
    async def save_to_storage(self):
        try:
            index_data = {
                'documents': {doc_id: asdict(doc) for doc_id, doc in self.documents.items()},
                'index': {term: {'documents': posting_list.documents, 'term_frequency': posting_list.term_frequency} for term, posting_list in self.index.items()},
                'stats': self.stats
            }
            await self.storage.save(index_data)
            logger.info("Index saved to storage")
        except Exception as e:
            logger.error(f"Error saving index: {e}")
    
    async def load_from_storage(self):
        try:
            index_data = await self.storage.load()
            if not index_data:
                logger.info("No existing index found, starting fresh")
                return
            
            for doc_id, doc_data in index_data.get('documents', {}).items():
                self.documents[doc_id] = Document(**doc_data)
            
            for term, posting_data in index_data.get('index', {}).items():
                self.index[term] = PostingList(term=term, documents=posting_data['documents'], term_frequency=posting_data['term_frequency'])
            
            self.stats.update(index_data.get('stats', {}))
            logger.info(f"Loaded index with {len(self.documents)} documents and {len(self.index)} terms")
            
        except Exception as e:
            logger.error(f"Error loading index: {e}")
