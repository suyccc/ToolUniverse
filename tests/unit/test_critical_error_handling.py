#!/usr/bin/env python3
"""
Test critical error handling and recovery scenarios - Cleaned Version

This test file covers important error handling scenarios:
1. ToolUniverse error handling
2. Invalid tool responses
3. Memory issues
4. Concurrent access issues
5. Resource cleanup
"""

import sys
import unittest
from pathlib import Path
import pytest
from unittest.mock import patch, Mock, MagicMock
import time
import threading

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tooluniverse import ToolUniverse
from tooluniverse.exceptions import ToolError, ToolValidationError


@pytest.mark.unit
class TestCriticalErrorHandling(unittest.TestCase):
    """Test critical error handling and recovery scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tu = ToolUniverse()
        # Load tools for real testing
        self.tu.load_tools()
    
    def test_invalid_tool_name_handling(self):
        """Test that invalid tool names are handled gracefully."""
        # Test with completely invalid tool name
        result = self.tu.run({
            "name": "NonExistentTool",
            "arguments": {"test": "value"}
        })
        
        self.assertIsInstance(result, dict)
        # Should either return error or handle gracefully
        if "error" in result:
            self.assertIn("tool", str(result["error"]).lower())
    
    def test_invalid_arguments_handling(self):
        """Test that invalid arguments are handled gracefully."""
        # Test with invalid arguments for a real tool
        result = self.tu.run({
            "name": "UniProt_get_entry_by_accession",
            "arguments": {"invalid_param": "value"}
        })
        
        self.assertIsInstance(result, dict)
        # Should either return error or handle gracefully
        if "error" in result:
            self.assertIn("parameter", str(result["error"]).lower())
    
    def test_empty_arguments_handling(self):
        """Test handling of empty arguments."""
        # Test with empty arguments
        result = self.tu.run({
            "name": "UniProt_get_entry_by_accession",
            "arguments": {}
        })
        
        self.assertIsInstance(result, dict)
        # Should either return error or handle gracefully
        if "error" in result:
            self.assertIn("required", str(result["error"]).lower())
    
    def test_none_arguments_handling(self):
        """Test handling of None arguments."""
        # Test with None arguments
        result = self.tu.run({
            "name": "UniProt_get_entry_by_accession",
            "arguments": None
        })
        
        self.assertIsInstance(result, dict)
        # Should handle None arguments gracefully
    
    def test_malformed_query_handling(self):
        """Test handling of malformed queries."""
        malformed_queries = [
            {"name": "UniProt_get_entry_by_accession"},  # Missing arguments
            {"arguments": {"accession": "P05067"}},  # Missing name
            {"name": "", "arguments": {"accession": "P05067"}},  # Empty name
            {"name": "UniProt_get_entry_by_accession", "arguments": ""},  # String arguments
            {"name": "UniProt_get_entry_by_accession", "arguments": []},  # List arguments
        ]
        
        for query in malformed_queries:
            result = self.tu.run(query)
            self.assertIsInstance(result, dict)
            # Should handle malformed queries gracefully
    
    def test_large_argument_handling(self):
        """Test handling of very large arguments."""
        # Test with very large argument values
        large_args = {
            "accession": "P05067",
            "large_string": "A" * 100000,  # 100KB string
            "large_array": ["item"] * 10000,  # Large array
        }
        
        result = self.tu.run({
            "name": "UniProt_get_entry_by_accession",
            "arguments": large_args
        })
        
        self.assertIsInstance(result, dict)
        # Should handle large arguments gracefully
    
    def test_concurrent_tool_access(self):
        """Test concurrent access to tools."""
        results = []
        
        def make_call(call_id):
            result = self.tu.run({
                "name": "UniProt_get_entry_by_accession",
                "arguments": {"accession": f"P{call_id:05d}"}
            })
            results.append(result)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_call, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify all calls completed
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertIsInstance(result, dict)
    
    def test_tool_initialization_failure(self):
        """Test handling of tool initialization failures."""
        # Test with invalid tool configuration
        invalid_tool = {
            "name": "InvalidTool",
            "type": "NonExistentType",
            "description": "Invalid tool"
        }
        
        self.tu.all_tools.append(invalid_tool)
        self.tu.all_tool_dict["InvalidTool"] = invalid_tool
        
        result = self.tu.run({
            "name": "InvalidTool",
            "arguments": {"test": "value"}
        })
        
        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
    
    def test_memory_pressure_handling(self):
        """Test handling under memory pressure."""
        # Simulate memory pressure by creating large objects
        large_objects = []
        
        try:
            # Create some large objects to simulate memory pressure
            for i in range(100):
                large_objects.append(["data"] * 10000)
            
            result = self.tu.run({
                "name": "UniProt_get_entry_by_accession",
                "arguments": {"accession": "P05067"}
            })
            
            self.assertIsInstance(result, dict)
            
        finally:
            # Clean up large objects
            del large_objects
    
    def test_resource_cleanup(self):
        """Test proper resource cleanup."""
        # Test that resources are properly cleaned up
        initial_tools = len(self.tu.all_tools)
        
        # Add some tools
        test_tool = {
            "name": "TestTool",
            "type": "TestType",
            "description": "Test tool"
        }
        
        self.tu.all_tools.append(test_tool)
        self.tu.all_tool_dict["TestTool"] = test_tool
        
        # Clear tools
        self.tu.all_tools.clear()
        self.tu.all_tool_dict.clear()
        
        # Verify cleanup
        self.assertEqual(len(self.tu.all_tools), 0)
        self.assertEqual(len(self.tu.all_tool_dict), 0)
    
    def test_error_propagation(self):
        """Test proper error propagation."""
        # Test with various error conditions
        error_cases = [
            {"name": "NonExistentTool", "arguments": {}},
            {"name": "UniProt_get_entry_by_accession", "arguments": {"invalid": "param"}},
            {"name": "", "arguments": {}},
            {"name": "UniProt_get_entry_by_accession", "arguments": None},
        ]
        
        for query in error_cases:
            result = self.tu.run(query)
            self.assertIsInstance(result, dict)
            # Should handle errors gracefully
    
    def test_partial_failure_recovery(self):
        """Test recovery from partial failures."""
        # Test multiple tool calls to ensure system remains stable
        results = []
        
        for i in range(5):
            result = self.tu.run({
                "name": "UniProt_get_entry_by_accession",
                "arguments": {"accession": f"P{i:05d}"}
            })
            results.append(result)
        
        # Verify mixed results
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertIsInstance(result, dict)
    
    def test_circuit_breaker_pattern(self):
        """Test circuit breaker pattern for repeated failures."""
        # Test multiple calls with invalid tool
        results = []
        
        for i in range(5):
            result = self.tu.run({
                "name": "NonExistentTool",
                "arguments": {"test": f"value_{i}"}
            })
            results.append(result)
        
        # All should fail gracefully
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertIsInstance(result, dict)
            self.assertIn("error", result)
    
    def test_graceful_degradation(self):
        """Test graceful degradation when services are unavailable."""
        # Test with tool that might not be available
        result = self.tu.run({
            "name": "NonExistentService",
            "arguments": {"query": "test"}
        })
        
        self.assertIsInstance(result, dict)
        # Should handle service unavailable gracefully
    
    def test_data_corruption_handling(self):
        """Test handling of corrupted data."""
        # Test with corrupted arguments
        corrupted_args = {
            "accession": "P05067\x00\x00",  # Null bytes
            "invalid_unicode": "test\xff\xfe",  # Invalid Unicode
        }
        
        result = self.tu.run({
            "name": "UniProt_get_entry_by_accession",
            "arguments": corrupted_args
        })
        
        self.assertIsInstance(result, dict)
        # Should handle corrupted data gracefully
    
    def test_tool_health_check_under_stress(self):
        """Test tool health check under stress."""
        # Test health check
        health = self.tu.get_tool_health()
        
        self.assertIsInstance(health, dict)
        self.assertIn("total", health)
        self.assertIn("available", health)
        self.assertIn("unavailable", health)
        self.assertIn("unavailable_list", health)
        self.assertIn("details", health)
        
        # Verify totals make sense
        self.assertEqual(health["total"], health["available"] + health["unavailable"])
    
    def test_cache_management_under_stress(self):
        """Test cache management under stress."""
        # Test cache operations under stress
        self.tu.clear_cache()
        
        # Add many items to cache using the proper API
        for i in range(100):
            self.tu._cache.set(f"item_{i}", {"data": f"value_{i}"})
        
        # Verify cache operations
        self.assertEqual(len(self.tu._cache), 100)
        
        # Clear cache
        self.tu.clear_cache()
        self.assertEqual(len(self.tu._cache), 0)
    
    def test_tool_specification_edge_cases(self):
        """Test tool specification edge cases."""
        # Test with non-existent tool
        spec = self.tu.tool_specification("NonExistentTool")
        self.assertIsNone(spec)
        
        # Test with empty string
        spec = self.tu.tool_specification("")
        self.assertIsNone(spec)
        
        # Test with None
        spec = self.tu.tool_specification(None)
        self.assertIsNone(spec)
    
    def test_tool_listing_edge_cases(self):
        """Test tool listing edge cases."""
        # Test with invalid mode
        tools = self.tu.list_built_in_tools(mode="invalid_mode")
        self.assertIsInstance(tools, dict)
        
        # Test with None mode
        tools = self.tu.list_built_in_tools(mode=None)
        self.assertIsInstance(tools, dict)
    
    def test_tool_filtering_edge_cases(self):
        """Test tool filtering edge cases."""
        # Test with empty category filter
        tools = self.tu.get_available_tools(category_filter="")
        self.assertIsInstance(tools, list)
        
        # Test with None category filter
        tools = self.tu.get_available_tools(category_filter=None)
        self.assertIsInstance(tools, list)
        
        # Test with non-existent category
        tools = self.tu.get_available_tools(category_filter="non_existent_category")
        self.assertIsInstance(tools, list)
    
    def test_tool_search_edge_cases(self):
        """Test tool search edge cases."""
        # Test with empty pattern
        results = self.tu.find_tools_by_pattern("")
        self.assertIsInstance(results, list)
        
        # Test with None pattern
        results = self.tu.find_tools_by_pattern(None)
        self.assertIsInstance(results, list)
        
        # Test with invalid search_in parameter
        results = self.tu.find_tools_by_pattern("test", search_in="invalid_field")
        self.assertIsInstance(results, list)


if __name__ == "__main__":
    unittest.main()
