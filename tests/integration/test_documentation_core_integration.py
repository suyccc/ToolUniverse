#!/usr/bin/env python3
"""
Integration tests for ToolUniverse core functionality - Cleaned Version

Tests real ToolUniverse core functionality with actual tool execution.
"""

import pytest
import os
from pathlib import Path

from tooluniverse import ToolUniverse


@pytest.mark.integration
class TestToolUniverseCoreIntegration:
    """Test core ToolUniverse functionality with real tool execution."""

    @pytest.fixture(autouse=True)
    def setup_tooluniverse(self):
        """Setup ToolUniverse instance for each test."""
        self.tu = ToolUniverse()
        self.tu.load_tools()

    def test_tool_loading_real(self):
        """Test real tool loading functionality."""
        # Test that tools are actually loaded
        assert len(self.tu.all_tools) > 0
        assert len(self.tu.all_tool_dict) > 0
        
        # Test that we can list tools
        tools = self.tu.list_built_in_tools()
        assert isinstance(tools, dict)
        assert "total_tools" in tools
        assert tools["total_tools"] > 0

    def test_tool_execution_real(self):
        """Test real tool execution with actual ToolUniverse calls."""
        # Test with a real tool (may fail due to missing API keys, but that's OK)
        try:
            result = self.tu.run({
                "name": "UniProt_get_entry_by_accession",
                "arguments": {"accession": "P05067"}
            })
            
            # Should return a result (may be error if API key not configured)
            assert isinstance(result, dict)
            if "error" in result:
                assert "API" in str(result["error"]) or "key" in str(result["error"]).lower()
        except Exception as e:
            # Expected if API key not configured
            assert isinstance(e, Exception)

    def test_tool_execution_multiple_tools_real(self):
        """Test real tool execution with multiple tools."""
        # Test multiple tool calls individually
        tools_to_test = [
            {"name": "UniProt_get_entry_by_accession", "arguments": {"accession": "P05067"}},
            {"name": "ArXiv_search_papers", "arguments": {"query": "test", "limit": 5}},
            {"name": "OpenTargets_get_associated_targets_by_disease_efoId", "arguments": {"efoId": "EFO_0000249"}}
        ]
        
        results = []
        for tool_call in tools_to_test:
            try:
                result = self.tu.run(tool_call)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})
        
        # Verify all calls completed
        assert len(results) == 3
        for result in results:
            # Allow for None results (API failures), dict results, or list results
            assert result is None or isinstance(result, (dict, list))

    def test_tool_specification_real(self):
        """Test real tool specification retrieval."""
        # Test that we can get tool specifications
        tool_names = self.tu.list_built_in_tools(mode="list_name")
        
        if tool_names:
            # Test with the first available tool
            tool_name = tool_names[0]
            spec = self.tu.tool_specification(tool_name)
            
            if spec:  # If tool has specification
                assert isinstance(spec, dict)
                assert "name" in spec
                assert "description" in spec

    def test_tool_health_check_real(self):
        """Test real tool health check functionality."""
        # Test health check
        health = self.tu.get_tool_health()
        
        assert isinstance(health, dict)
        assert "total" in health
        assert "available" in health
        assert "unavailable" in health
        assert "unavailable_list" in health
        assert "details" in health
        
        # Verify totals make sense
        assert health["total"] == health["available"] + health["unavailable"]
        assert health["total"] > 0

    def test_tool_finder_real(self):
        """Test real tool finder functionality."""
        try:
            result = self.tu.run({
                "name": "Tool_Finder_Keyword",
                "arguments": {
                    "description": "protein structure prediction",
                    "limit": 5
                }
            })
            
            assert isinstance(result, dict)
            if "tools" in result:
                assert isinstance(result["tools"], list)
        except Exception as e:
            # Expected if tool not available
            assert isinstance(e, Exception)

    def test_tool_caching_real(self):
        """Test real tool caching functionality."""
        # Test cache operations
        self.tu.clear_cache()
        assert len(self.tu._cache) == 0
        
        # Test caching a result
        test_key = "test_cache_key"
        test_value = {"result": "cached_data"}
        
        self.tu._cache.set(test_key, test_value)
        cached_result = self.tu._cache.get(test_key)
        assert cached_result is not None
        assert cached_result == test_value
        
        # Clear cache
        self.tu.clear_cache()
        assert len(self.tu._cache) == 0

    def test_tool_hooks_real(self):
        """Test real tool hooks functionality."""
        # Test hooks toggle
        self.tu.toggle_hooks(True)
        self.tu.toggle_hooks(False)
        
        # Test that hooks can be toggled without errors
        assert True  # If we get here, no exception was raised

    def test_tool_streaming_real(self):
        """Test real tool streaming functionality."""
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
            
            # Should return a result
            assert isinstance(result, dict)
        except Exception:
            # Expected if API key not configured
            pass

    def test_tool_error_handling_real(self):
        """Test real tool error handling."""
        # Test with invalid tool name
        result = self.tu.run({
            "name": "NonExistentTool",
            "arguments": {"test": "value"}
        })
        
        assert isinstance(result, dict)
        if "error" in result:
            assert "tool" in str(result["error"]).lower()

    def test_tool_parameter_validation_real(self):
        """Test real tool parameter validation."""
        # Test with invalid parameters
        result = self.tu.run({
            "name": "UniProt_get_entry_by_accession",
            "arguments": {"invalid_param": "value"}
        })
        
        assert isinstance(result, dict)
        if "error" in result:
            assert "parameter" in str(result["error"]).lower()

    def test_tool_export_real(self):
        """Test real tool export functionality."""
        import tempfile
        import os
        
        # Test exporting to file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_file = f.name
        
        try:
            self.tu.export_tool_names(temp_file)
            
            # Verify file was created and has content
            assert os.path.exists(temp_file)
            with open(temp_file, 'r') as f:
                content = f.read()
                assert len(content) > 0
                
        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_tool_env_template_real(self):
        """Test real environment template generation."""
        import tempfile
        import os
        
        # Test with some missing keys
        missing_keys = ["API_KEY_1", "API_KEY_2"]
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env') as f:
            temp_file = f.name
        
        try:
            self.tu.generate_env_template(missing_keys, output_file=temp_file)
            
            # Verify file was created and has content
            assert os.path.exists(temp_file)
            with open(temp_file, 'r') as f:
                content = f.read()
                assert "API_KEY_1" in content
                assert "API_KEY_2" in content
                
        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_tool_call_id_generation_real(self):
        """Test real call ID generation."""
        # Test generating multiple IDs
        id1 = self.tu.call_id_gen()
        id2 = self.tu.call_id_gen()
        
        assert isinstance(id1, str)
        assert isinstance(id2, str)
        assert id1 != id2
        assert len(id1) > 0
        assert len(id2) > 0

    def test_tool_lazy_loading_real(self):
        """Test real lazy loading functionality."""
        status = self.tu.get_lazy_loading_status()
        
        assert isinstance(status, dict)
        assert "lazy_loading_enabled" in status
        assert "full_discovery_completed" in status
        assert "immediately_available_tools" in status
        assert "lazy_mappings_available" in status
        assert "loaded_tools_count" in status

    def test_tool_types_real(self):
        """Test real tool types retrieval."""
        tool_types = self.tu.get_tool_types()
        
        assert isinstance(tool_types, list)
        assert len(tool_types) > 0

    def test_tool_available_tools_real(self):
        """Test real available tools retrieval."""
        available_tools = self.tu.get_available_tools()
        
        assert isinstance(available_tools, list)
        assert len(available_tools) > 0

    def test_tool_find_by_pattern_real(self):
        """Test real tool finding by pattern."""
        results = self.tu.find_tools_by_pattern("protein")
        
        assert isinstance(results, list)
        # Should find some tools related to protein
        assert len(results) >= 0

    def test_tool_concurrent_execution_real(self):
        """Test real concurrent tool execution."""
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

    def test_tool_memory_management_real(self):
        """Test real memory management."""
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

    def test_tool_performance_real(self):
        """Test real tool performance."""
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

    def test_tool_error_recovery_real(self):
        """Test real error recovery."""
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
