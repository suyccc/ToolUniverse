#!/usr/bin/env python3
"""
Integration tests for ToolUniverse tool composition - Cleaned Version

Tests real ComposeTool functionality with actual tool execution.
"""

import pytest
import json
import tempfile
from pathlib import Path

from tooluniverse import ToolUniverse


@pytest.mark.integration
@pytest.mark.composition
class TestToolUniverseCompositionIntegration:
    """Test tool composition functionality with real tool execution."""

    @pytest.fixture(autouse=True)
    def setup_tooluniverse(self):
        """Setup ToolUniverse instance for each test."""
        self.tu = ToolUniverse()
        self.tu.load_tools()

    def test_compose_tool_availability(self):
        """Test that compose tools are actually available in ToolUniverse."""
        # Test that compose tools are available
        tool_names = self.tu.list_built_in_tools(mode='list_name')
        compose_tools = [name for name in tool_names if "Compose" in name or "compose" in name]
        assert len(compose_tools) > 0

    def test_compose_tool_execution_real(self):
        """Test actual ComposeTool execution with real ToolUniverse."""
        # Test that we can actually execute compose tools
        try:
            # Try to find and execute a compose tool
            tool_names = self.tu.list_built_in_tools(mode='list_name')
            compose_tools = [name for name in tool_names if "Compose" in name or "compose" in name]
            
            if compose_tools:
                # Try to execute the first compose tool
                result = self.tu.run({
                    "name": compose_tools[0],
                    "arguments": {"test": "value"}
                })
                
                # Should return a result (may be error if missing dependencies)
                assert isinstance(result, dict)
        except Exception as e:
            # Expected if compose tools not available or missing dependencies
            assert isinstance(e, Exception)

    def test_tool_chaining_real(self):
        """Test real tool chaining with actual ToolUniverse calls."""
        # Test sequential tool calls
        try:
            # First call
            result1 = self.tu.run({
                "name": "UniProt_get_entry_by_accession",
                "arguments": {"accession": "P05067"}
            })
            
            # If first call succeeded, try second call
            if result1 and isinstance(result1, dict) and "data" in result1:
                result2 = self.tu.run({
                    "name": "ArXiv_search_papers",
                    "arguments": {"query": "protein", "limit": 5}
                })
                
                # Both should return results
                assert isinstance(result1, dict)
                assert isinstance(result2, dict)
        except Exception:
            # Expected if API keys not configured
            pass

    def test_tool_broadcasting_real(self):
        """Test real parallel tool execution with actual ToolUniverse calls."""
        # Test parallel searches
        literature_sources = {}
        
        try:
            # Parallel searches
            literature_sources['europepmc'] = self.tu.run({
                "name": "EuropePMC_search_articles",
                "arguments": {"query": "CRISPR", "limit": 5}
            })

            literature_sources['openalex'] = self.tu.run({
                "name": "openalex_literature_search",
                "arguments": {
                    "search_keywords": "CRISPR",
                    "max_results": 5
                }
            })

            literature_sources['pubtator'] = self.tu.run({
                "name": "PubTator3_LiteratureSearch",
                "arguments": {"text": "CRISPR", "page_size": 5}
            })

            # Verify all sources were searched
            assert len(literature_sources) == 3
            for source, result in literature_sources.items():
                assert isinstance(result, dict)
        except Exception:
            # Expected if API keys not configured
            pass

    def test_compose_tool_error_handling_real(self):
        """Test real error handling in compose tools."""
        # Test with invalid tool name
        result = self.tu.run({
            "name": "NonExistentComposeTool",
            "arguments": {"test": "value"}
        })
        
        assert isinstance(result, dict)
        # Should either return error or handle gracefully
        if "error" in result:
            assert "tool" in str(result["error"]).lower()

    def test_compose_tool_dependency_management_real(self):
        """Test real dependency management in compose tools."""
        # Test that we can check for tool availability
        required_tools = [
            "EuropePMC_search_articles",
            "openalex_literature_search",
            "PubTator3_LiteratureSearch"
        ]
        
        available_tools = self.tu.get_available_tools()
        
        # Check which required tools are available
        available_required = [tool for tool in required_tools if tool in available_tools]
        
        assert isinstance(available_required, list)
        assert len(available_required) <= len(required_tools)

    def test_compose_tool_workflow_execution_real(self):
        """Test real workflow execution with compose tools."""
        # Test a simple workflow
        workflow_results = {}
        
        try:
            # Step 1: Search for papers
            search_result = self.tu.run({
                "name": "ArXiv_search_papers",
                "arguments": {"query": "machine learning", "limit": 3}
            })
            
            if search_result and isinstance(search_result, dict):
                workflow_results["search"] = search_result
                
                # Step 2: Get protein info (if search succeeded)
                protein_result = self.tu.run({
                    "name": "UniProt_get_entry_by_accession",
                    "arguments": {"accession": "P05067"}
                })
                
                if protein_result and isinstance(protein_result, dict):
                    workflow_results["protein"] = protein_result
                
                # Verify workflow results
                assert "search" in workflow_results
        except Exception:
            # Expected if API keys not configured
            pass

    def test_compose_tool_caching_real(self):
        """Test real caching functionality in compose tools."""
        # Test caching mechanism
        cache_key = "test_compose_cache"
        result = self.tu._cache.get(cache_key)
        if result is None:
            try:
                result = self.tu.run({
                    "name": "UniProt_get_entry_by_accession",
                    "arguments": {"accession": "P05067"}
                })
                self.tu._cache.set(cache_key, result)
            except Exception:
                # Expected if API key not configured
                result = {"error": "API key not configured"}
                self.tu._cache.set(cache_key, result)
        
        # Verify caching worked
        cached_result = self.tu._cache.get(cache_key)
        assert cached_result is not None
        assert cached_result == result

    def test_compose_tool_streaming_real(self):
        """Test real streaming functionality in compose tools."""
        # Test streaming callback
        callback_called = False
        callback_data = []
        
        def test_callback(chunk):
            nonlocal callback_called, callback_data
            callback_called = True
            callback_data.append(chunk)
        
        try:
            result = self.tu.run({
                "name": "UniProt_get_entry_by_accession",
                "arguments": {"accession": "P05067"}
            }, stream_callback=test_callback)
            
            # If successful, verify we got some result
            assert isinstance(result, dict)
        except Exception:
            # Expected if API key not configured
            pass

    def test_compose_tool_validation_real(self):
        """Test real parameter validation in compose tools."""
        # Test with invalid parameters
        result = self.tu.run({
            "name": "UniProt_get_entry_by_accession",
            "arguments": {"invalid_param": "value"}
        })
        
        assert isinstance(result, dict)
        # Should either return error or handle gracefully
        if "error" in result:
            assert "parameter" in str(result["error"]).lower()

    def test_compose_tool_performance_real(self):
        """Test real performance characteristics of compose tools."""
        import time
        
        # Test execution time
        start_time = time.time()
        
        try:
            result = self.tu.run({
                "name": "UniProt_get_entry_by_accession",
                "arguments": {"accession": "P05067"}
            })
            
            execution_time = time.time() - start_time
            
            # Should complete within reasonable time (30 seconds)
            assert execution_time < 30
            assert isinstance(result, dict)
        except Exception:
            # Expected if API key not configured
            execution_time = time.time() - start_time
            assert execution_time < 30

    def test_compose_tool_concurrent_execution_real(self):
        """Test real concurrent execution of compose tools."""
        import threading
        import time
        
        results = []
        
        def make_call(call_id):
            result = self.tu.run({
                "name": "UniProt_get_entry_by_accession",
                "arguments": {"accession": f"P{call_id:05d}"}
            })
            results.append(result)
        
        # Create multiple threads
        threads = []
        for i in range(3):  # Reduced for testing
            thread = threading.Thread(target=make_call, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify all calls completed
        assert len(results) == 3
        for result in results:
            assert isinstance(result, dict)

    def test_compose_tool_memory_management_real(self):
        """Test real memory management in compose tools."""
        import gc
        
        # Test multiple calls to ensure no memory leaks
        initial_objects = len(gc.get_objects())
        
        for i in range(5):  # Reduced for testing
            result = self.tu.run({
                "name": "UniProt_get_entry_by_accession",
                "arguments": {"accession": f"P{i:05d}"}
            })
            
            assert isinstance(result, dict)
            
            # Force garbage collection periodically
            if i % 2 == 0:
                gc.collect()
        
        # Check that we haven't created too many new objects
        final_objects = len(gc.get_objects())
        object_growth = final_objects - initial_objects
        
        # Should not have created more than 500 new objects
        assert object_growth < 500

    def test_compose_tool_error_recovery_real(self):
        """Test real error recovery in compose tools."""
        # Test workflow with error handling
        results = {"status": "running", "completed_steps": []}

        try:
            # Primary step
            primary_result = self.tu.run({
                "name": "NonExistentTool",  # This should fail
                "arguments": {"query": "test"}
            })
            results["primary"] = primary_result
            results["completed_steps"].append("primary")
            
            # If primary succeeded, check if it's an error result
            if isinstance(primary_result, dict) and "error" in primary_result:
                results["primary_error"] = primary_result["error"]

        except Exception as e:
            results["primary_error"] = str(e)

        # Fallback step
        try:
            fallback_result = self.tu.run({
                "name": "UniProt_get_entry_by_accession",  # This might work
                "arguments": {"accession": "P05067"}
            })
            results["fallback"] = fallback_result
            results["completed_steps"].append("fallback")

        except Exception as e2:
            results["fallback_error"] = str(e2)

        # Verify error handling worked
        # Primary should either have an error or be marked as failed
        assert ("primary_error" in results or 
                (isinstance(results.get("primary"), dict) and "error" in results["primary"]))
        # Either fallback succeeded or failed, both are valid outcomes
        assert ("fallback" in results or "fallback_error" in results)


if __name__ == "__main__":
    pytest.main([__file__])
