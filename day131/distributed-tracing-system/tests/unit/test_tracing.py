import pytest
import asyncio
from unittest.mock import Mock, patch
from src.tracing.context import TraceContextManager, TraceContext
from src.tracing.collector import TraceCollector

class TestTraceContext:
    def test_generate_trace_id(self):
        """Test trace ID generation"""
        trace_id = TraceContextManager.generate_trace_id()
        assert trace_id is not None
        assert len(trace_id) > 0
        assert isinstance(trace_id, str)
    
    def test_generate_span_id(self):
        """Test span ID generation"""
        span_id = TraceContextManager.generate_span_id()
        assert span_id is not None
        assert len(span_id) == 8
        assert isinstance(span_id, str)
    
    def test_create_trace_context(self):
        """Test trace context creation"""
        context = TraceContextManager.create_trace_context(
            service_name="test-service",
            operation_name="test-operation"
        )
        
        assert context.trace_id is not None
        assert context.span_id is not None
        assert context.service_name == "test-service"
        assert context.operation_name == "test-operation"
    
    def test_context_propagation(self):
        """Test context setting and getting"""
        context = TraceContextManager.create_trace_context()
        TraceContextManager.set_context(context)
        
        retrieved_context = TraceContextManager.get_current_context()
        assert retrieved_context is not None
        assert retrieved_context.trace_id == context.trace_id
        assert retrieved_context.span_id == context.span_id

class TestTraceCollector:
    @pytest.fixture
    async def collector(self):
        """Create trace collector for testing"""
        collector = TraceCollector("redis://localhost:6379")
        await collector.initialize()
        return collector
    
    @pytest.mark.asyncio
    async def test_record_span(self, collector):
        """Test span recording"""
        context = TraceContextManager.create_trace_context(
            service_name="test-service",
            operation_name="test-op"
        )
        
        await collector.record_span(
            context=context,
            operation="test-operation",
            duration_ms=100.0,
            status="success"
        )
        
        # Verify span was recorded
        trace = await collector.get_trace(context.trace_id)
        assert len(trace) >= 1
        assert any(span["operation"] == "test-operation" for span in trace)
    
    @pytest.mark.asyncio
    async def test_get_recent_traces(self, collector):
        """Test getting recent traces"""
        # Record some test spans
        for i in range(3):
            context = TraceContextManager.create_trace_context()
            await collector.record_span(
                context=context,
                operation=f"test-op-{i}",
                duration_ms=50.0 + i * 10
            )
        
        traces = await collector.get_recent_traces(limit=5)
        assert len(traces) >= 3
        assert all("trace_id" in trace for trace in traces)
