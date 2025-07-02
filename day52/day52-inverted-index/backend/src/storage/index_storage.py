import json
import aiofiles
import os
from typing import Dict, Any, Optional

class IndexStorage:
    def __init__(self, file_path: str):
        self.file_path = file_path
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    async def save(self, data: Dict[str, Any]) -> bool:
        try:
            async with aiofiles.open(self.file_path, 'w') as f:
                await f.write(json.dumps(data, indent=2))
            return True
        except Exception as e:
            print(f"Error saving to storage: {e}")
            return False
    
    async def load(self) -> Optional[Dict[str, Any]]:
        try:
            if not os.path.exists(self.file_path):
                return None
            
            async with aiofiles.open(self.file_path, 'r') as f:
                content = await f.read()
                return json.loads(content)
        except Exception as e:
            print(f"Error loading from storage: {e}")
            return None
