# backend/tests/test_vector_service_memory.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.vector_service import vector_service
from sentence_transformers import SentenceTransformer

@pytest.mark.asyncio
async def test_store_memory():
    with patch.object(vector_service, 'client', new_callable=AsyncMock) as mock_client:
        mock_client.upsert = AsyncMock()
        vector = [0.1] * 384
        result = await vector_service.store_memory(
            agent_id="b-test",
            text="Test memory",
            vector=vector,
            timestamp="2023-01-01T00:00:00Z"
        )
        assert result is True
        mock_client.upsert.assert_awaited_once()

@pytest.mark.asyncio
async def test_search_memory():
    with patch.object(vector_service, 'client', new_callable=AsyncMock) as mock_client:
        mock_client.search = AsyncMock(return_value=[
            MagicMock(payload={"agent_id": "b-test", "text": "memory1", "source": "memory"}),
            MagicMock(payload={"agent_id": "b-test", "text": "memory2", "source": "memory"})
        ])
        vector = [0.1] * 384
        results = await vector_service.search_memory("b-test", vector, limit=2)
        assert len(results) == 2
        assert results[0]["text"] == "memory1"
        assert results[1]["text"] == "memory2"
        # Verify filter was correct
        call_args = mock_client.search.call_args[1]
        assert call_args["query_filter"].must[0].key == "agent_id"
        assert call_args["query_filter"].must[0].match.value == "b-test"
        assert call_args["query_filter"].must[1].key == "source"
        assert call_args["query_filter"].must[1].match.value == "memory"
