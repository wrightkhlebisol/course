import asyncio
import gzip
import lz4.frame
import zstandard as zstd
from typing import AsyncIterator, BinaryIO
from pathlib import Path
import logging

from restoration.models import CompressionType

logger = logging.getLogger(__name__)

class StreamingDecompressor:
    def __init__(self, chunk_size: int = 8192):
        self.chunk_size = chunk_size
        
    async def decompress_stream(self, file_path: Path, 
                              compression: CompressionType) -> AsyncIterator[bytes]:
        """Stream decompress archive file in chunks"""
        
        if compression == CompressionType.RAW:
            async for chunk in self._stream_raw_file(file_path):
                yield chunk
        elif compression == CompressionType.GZIP:
            async for chunk in self._stream_gzip_file(file_path):
                yield chunk
        elif compression == CompressionType.LZ4:
            async for chunk in self._stream_lz4_file(file_path):
                yield chunk
        elif compression == CompressionType.ZSTD:
            async for chunk in self._stream_zstd_file(file_path):
                yield chunk
        else:
            raise ValueError(f"Unsupported compression type: {compression}")
    
    async def _stream_raw_file(self, file_path: Path) -> AsyncIterator[bytes]:
        """Stream raw uncompressed file"""
        try:
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(self.chunk_size)
                    if not chunk:
                        break
                    yield chunk
                    # Yield control to event loop
                    await asyncio.sleep(0)
        except Exception as e:
            logger.error(f"Error streaming raw file {file_path}: {e}")
            raise
    
    async def _stream_gzip_file(self, file_path: Path) -> AsyncIterator[bytes]:
        """Stream decompress gzip file"""
        try:
            with gzip.open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(self.chunk_size)
                    if not chunk:
                        break
                    yield chunk
                    await asyncio.sleep(0)
        except Exception as e:
            logger.error(f"Error streaming gzip file {file_path}: {e}")
            raise
    
    async def _stream_lz4_file(self, file_path: Path) -> AsyncIterator[bytes]:
        """Stream decompress LZ4 file"""
        try:
            with lz4.frame.open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(self.chunk_size)
                    if not chunk:
                        break
                    yield chunk
                    await asyncio.sleep(0)
        except Exception as e:
            logger.error(f"Error streaming LZ4 file {file_path}: {e}")
            raise
    
    async def _stream_zstd_file(self, file_path: Path) -> AsyncIterator[bytes]:
        """Stream decompress Zstandard file"""
        try:
            dctx = zstd.ZstdDecompressor()
            with open(file_path, 'rb') as ifh:
                with dctx.stream_reader(ifh) as reader:
                    while True:
                        chunk = reader.read(self.chunk_size)
                        if not chunk:
                            break
                        yield chunk
                        await asyncio.sleep(0)
        except Exception as e:
            logger.error(f"Error streaming Zstd file {file_path}: {e}")
            raise
    
    async def get_decompressed_size_estimate(self, file_path: Path, 
                                           compression: CompressionType) -> int:
        """Estimate decompressed size without full decompression"""
        
        if compression == CompressionType.RAW:
            return file_path.stat().st_size
        
        # For compressed files, read first chunk to estimate compression ratio
        try:
            compressed_size = file_path.stat().st_size
            
            # Sample first chunk to estimate compression ratio
            sample_compressed = 0
            sample_decompressed = 0
            
            async for chunk in self.decompress_stream(file_path, compression):
                sample_decompressed += len(chunk)
                sample_compressed += min(self.chunk_size, compressed_size)
                
                # Use first 10KB for estimation
                if sample_decompressed >= 10240:
                    break
            
            if sample_compressed > 0:
                ratio = sample_decompressed / sample_compressed
                return int(compressed_size * ratio)
            
        except Exception as e:
            logger.warning(f"Could not estimate size for {file_path}: {e}")
        
        # Fallback to 3x compression ratio estimate
        return file_path.stat().st_size * 3
