"""Log File Monitor using inotify"""
import asyncio
import os
import time
from typing import Dict, Any, Optional
from pathlib import Path
import structlog
import aiofiles
from asyncio import Queue

try:
    import pyinotify
    HAS_INOTIFY = True
except ImportError:
    HAS_INOTIFY = False
    import threading
    from watchfiles import awatch


class LogEntry:
    def __init__(self, content: str, source_path: str, log_type: str, 
                 timestamp: float = None, metadata: Dict = None):
        self.content = content.strip()
        self.source_path = source_path
        self.log_type = log_type
        self.timestamp = timestamp or time.time()
        self.metadata = metadata or {}
        self.size = len(content)


class FileState:
    def __init__(self, path: str):
        self.path = path
        self.position = 0
        self.inode = None
        self.size = 0
        self.last_read = time.time()
        
        if os.path.exists(path):
            stat = os.stat(path)
            self.size = stat.st_size
            self.inode = stat.st_ino


class LogFileMonitor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = structlog.get_logger("file_monitor")
        self.log_queue: Queue = Queue(maxsize=self.config.get('buffer_size', 10000))
        self.file_states: Dict[str, FileState] = {}
        self.running = False
        
    async def start_monitoring(self, log_sources: Dict[str, Any]) -> None:
        """Start monitoring log files"""
        self.logger.info("Starting file monitoring", sources=len(log_sources))
        self.running = True
        
        # Initialize file states
        for path, source in log_sources.items():
            if os.path.exists(path):
                self.file_states[path] = FileState(path)
                # Read from end of file to avoid processing old logs
                self.file_states[path].position = self.file_states[path].size
        
        # Start monitoring tasks
        monitor_tasks = []
        
        if HAS_INOTIFY:
            # Use inotify for efficient monitoring
            task = asyncio.create_task(self._monitor_with_inotify(log_sources))
            monitor_tasks.append(task)
        else:
            # Fallback to watchfiles
            for path in log_sources.keys():
                task = asyncio.create_task(self._monitor_file_polling(path, log_sources[path]))
                monitor_tasks.append(task)
        
        # Background task to handle log rotation
        rotation_task = asyncio.create_task(self._handle_log_rotation())
        monitor_tasks.append(rotation_task)
        
        try:
            await asyncio.gather(*monitor_tasks)
        except Exception as e:
            self.logger.error("Monitoring error", error=str(e))
        finally:
            self.running = False
    
    async def _monitor_with_inotify(self, log_sources: Dict[str, Any]) -> None:
        """Monitor files using inotify"""
        class EventHandler(pyinotify.ProcessEvent):
            def __init__(self, monitor_instance):
                self.monitor = monitor_instance
                
            def process_IN_MODIFY(self, event):
                if not event.dir and event.pathname in log_sources:
                    asyncio.create_task(
                        self.monitor._process_file_change(event.pathname, log_sources[event.pathname])
                    )
        
        wm = pyinotify.WatchManager()
        handler = EventHandler(self)
        notifier = pyinotify.AsyncNotifier(wm, handler)
        
        # Add watches
        for path in log_sources.keys():
            if os.path.exists(path):
                wm.add_watch(path, pyinotify.IN_MODIFY)
        
        while self.running:
            if notifier.check_events():
                notifier.read_events()
                notifier.process_events()
            await asyncio.sleep(0.1)
    
    async def _monitor_file_polling(self, path: str, source: Any) -> None:
        """Monitor single file using polling (fallback)"""
        while self.running:
            try:
                if os.path.exists(path):
                    current_stat = os.stat(path)
                    file_state = self.file_states.get(path)
                    
                    if not file_state or current_stat.st_size > file_state.size:
                        await self._process_file_change(path, source)
                
                await asyncio.sleep(1)  # Poll every second
                
            except Exception as e:
                self.logger.error("Polling error", path=path, error=str(e))
                await asyncio.sleep(5)
    
    async def _process_file_change(self, path: str, source: Any) -> None:
        """Process file change event"""
        try:
            file_state = self.file_states.get(path)
            if not file_state:
                file_state = FileState(path)
                self.file_states[path] = file_state
            
            # Check if file was rotated
            current_stat = os.stat(path)
            if current_stat.st_ino != file_state.inode:
                self.logger.info("Log rotation detected", path=path)
                file_state.position = 0
                file_state.inode = current_stat.st_ino
            
            # Read new content
            async with aiofiles.open(path, 'r', encoding='utf-8', errors='ignore') as f:
                await f.seek(file_state.position)
                new_content = await f.read()
                file_state.position = await f.tell()
                file_state.size = current_stat.st_size
                file_state.last_read = time.time()
            
            if new_content:
                await self._process_new_lines(new_content, path, source)
                
        except Exception as e:
            self.logger.error("File processing error", path=path, error=str(e))
    
    async def _process_new_lines(self, content: str, path: str, source: Any) -> None:
        """Process new log lines"""
        lines = content.strip().split('\n')
        
        for line in lines:
            if line.strip():
                log_entry = LogEntry(
                    content=line,
                    source_path=path,
                    log_type=source.log_type,
                    metadata={'parser': source.parser, 'hostname': os.uname().nodename}
                )
                
                try:
                    await self.log_queue.put(log_entry)
                except asyncio.QueueFull:
                    self.logger.warning("Log queue full, dropping message", path=path)
    
    async def _handle_log_rotation(self) -> None:
        """Handle log rotation detection"""
        while self.running:
            for path, file_state in list(self.file_states.items()):
                try:
                    if os.path.exists(path):
                        current_stat = os.stat(path)
                        # Check for size decrease (rotation indicator)
                        if current_stat.st_size < file_state.size:
                            self.logger.info("Log rotation detected by size", path=path)
                            file_state.position = 0
                            file_state.size = current_stat.st_size
                            file_state.inode = current_stat.st_ino
                            
                except Exception as e:
                    self.logger.debug("Rotation check error", path=path, error=str(e))
            
            await asyncio.sleep(10)  # Check every 10 seconds
    
    def get_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        return {
            'monitored_files': len(self.file_states),
            'queue_size': self.log_queue.qsize(),
            'queue_max_size': self.log_queue.maxsize,
            'total_bytes_read': sum(fs.position for fs in self.file_states.values())
        }
