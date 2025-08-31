import re
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class SearchQuery:
    terms: List[str]
    filters: Dict[str, str]
    limit: int
    offset: int

class QueryEngine:
    def __init__(self, inverted_index):
        self.index = inverted_index
    
    async def execute_search(self, query_string: str, **kwargs) -> Dict[str, Any]:
        start_time = asyncio.get_event_loop().time()
        
        try:
            query = self._parse_query(query_string, **kwargs)
            results = await self.index.search(' '.join(query.terms), query.limit)
            filtered_results = self._apply_filters(results, query.filters)
            paginated_results = filtered_results[query.offset:query.offset + query.limit]
            
            end_time = asyncio.get_event_loop().time()
            response = {
                'results': paginated_results,
                'metadata': {
                    'total_results': len(filtered_results),
                    'page_size': query.limit,
                    'page_offset': query.offset,
                    'search_time_ms': round((end_time - start_time) * 1000, 2),
                    'query': query_string
                }
            }
            
            return response
            
        except Exception as e:
            return {'results': [], 'metadata': {'total_results': 0, 'error': str(e), 'query': query_string}}
    
    def _parse_query(self, query_string: str, **kwargs) -> SearchQuery:
        filters = {}
        terms = []
        
        filter_pattern = r'(\w+):(\w+)'
        for match in re.finditer(filter_pattern, query_string):
            field, value = match.groups()
            filters[field] = value
            query_string = query_string.replace(match.group(0), '')
        
        terms = [term.strip() for term in query_string.split() if term.strip()]
        
        return SearchQuery(terms=terms, filters=filters, limit=kwargs.get('limit', 50), offset=kwargs.get('offset', 0))
    
    def _apply_filters(self, results: List[Dict], filters: Dict[str, str]) -> List[Dict]:
        if not filters:
            return results
        
        filtered = []
        for result in results:
            match = True
            for field, value in filters.items():
                if field in result.get('metadata', {}):
                    if result['metadata'][field].lower() != value.lower():
                        match = False
                        break
            
            if match:
                filtered.append(result)
        
        return filtered
