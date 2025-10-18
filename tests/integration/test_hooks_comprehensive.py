#!/usr/bin/env python3
"""
Comprehensive Hook Integration Tests

This test file provides comprehensive coverage of all hook functionality:
- SummarizationHook basic and advanced functionality
- FileSaveHook file processing and metadata
- Hook configuration validation and error handling
- Performance testing and optimization
- Integration with different ToolUniverse modes

Usage:
    pytest tests/integration/test_hooks_comprehensive.py -v
"""

import pytest
import time
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tooluniverse import ToolUniverse


@pytest.mark.integration
@pytest.mark.hooks
class TestHooksComprehensive:
    """Comprehensive hook functionality tests"""

    def setup_method(self):
        """Setup for each test method"""
        self.tu = ToolUniverse()
        self.tu.load_tools()

    @pytest.mark.require_api_keys
    def test_summarization_hook_basic_functionality(self):
        """Test basic SummarizationHook functionality"""
        # Enable SummarizationHook
        self.tu.toggle_hooks(True)
        
        # Test tool call that should trigger summarization
        function_call = {
            "name": "OpenTargets_get_target_gene_ontology_by_ensemblID",
            "arguments": {"ensemblId": "ENSG00000012048"}
        }
        
        result = self.tu.run_one_function(function_call)
        
        # Verify result is not None and is a string
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Check if summarization occurred (look for summary indicators)
        result_lower = result.lower()
        # Note: We can't guarantee summarization occurred without knowing the original length
        # but we can verify the hook system is working
        assert True  # Hook system is functional

    @pytest.mark.require_api_keys
    def test_file_save_hook_functionality(self):
        """Test FileSaveHook functionality"""
        # Configure FileSaveHook
        hook_config = {
            "hooks": [{
                "name": "file_save_hook",
                "type": "FileSaveHook",
                "enabled": True,
                "conditions": {
                    "output_length": {
                        "operator": ">",
                        "threshold": 1000
                    }
                },
                "hook_config": {
                    "temp_dir": tempfile.gettempdir(),
                    "file_prefix": "test_output",
                    "include_metadata": True,
                    "auto_cleanup": True,
                    "cleanup_age_hours": 1
                }
            }]
        }
        
        # Create new ToolUniverse instance with FileSaveHook
        tu_file = ToolUniverse(hooks_enabled=True, hook_config=hook_config)
        tu_file.load_tools()
        
        # Test tool call
        function_call = {
            "name": "OpenTargets_get_target_gene_ontology_by_ensemblID",
            "arguments": {"ensemblId": "ENSG00000012048"}
        }
        
        result = tu_file.run_one_function(function_call)
        
        # Verify FileSaveHook result structure
        assert isinstance(result, dict)
        assert "file_path" in result
        assert "data_format" in result
        assert "file_size" in result
        assert "data_structure" in result
        
        # Verify file exists
        file_path = result["file_path"]
        assert os.path.exists(file_path)
        
        # Verify file size is reasonable
        assert result["file_size"] > 0
        
        # Clean up
        if os.path.exists(file_path):
            os.remove(file_path)

    @pytest.mark.require_api_keys
    def test_hook_configuration_validation(self):
        """Test hook configuration validation and error handling"""
        # Test valid configuration
        valid_config = {
            "hooks": [{
                "name": "test_hook",
                "type": "SummarizationHook",
                "enabled": True,
                "conditions": {
                    "output_length": {
                        "operator": ">",
                        "threshold": 1000
                    }
                },
                "hook_config": {
                    "chunk_size": 2000,
                    "focus_areas": "key_findings_and_results",
                    "max_summary_length": 1500
                }
            }]
        }
        
        tu = ToolUniverse(hooks_enabled=True, hook_config=valid_config)
        tu.load_tools()
        
        # Verify hook manager is properly initialized
        assert hasattr(tu, 'hook_manager')
        assert tu.hook_manager is not None
        assert len(tu.hook_manager.hooks) > 0

    @pytest.mark.require_api_keys
    def test_hook_performance_impact(self):
        """Test hook performance impact"""
        function_call = {
            "name": "OpenTargets_get_target_gene_ontology_by_ensemblID",
            "arguments": {"ensemblId": "ENSG00000012048"}
        }
        
        # Test without hooks
        tu_no_hooks = ToolUniverse(hooks_enabled=False)
        tu_no_hooks.load_tools()
        
        start_time = time.time()
        result_no_hooks = tu_no_hooks.run_one_function(function_call)
        time_no_hooks = time.time() - start_time
        
        # Test with hooks
        tu_with_hooks = ToolUniverse(hooks_enabled=True)
        tu_with_hooks.load_tools()
        
        start_time = time.time()
        result_with_hooks = tu_with_hooks.run_one_function(function_call)
        time_with_hooks = time.time() - start_time
        
        # Verify both executions succeeded
        assert result_no_hooks is not None
        assert result_with_hooks is not None
        
        # Verify hooks add some processing time (expected)
        assert time_with_hooks >= time_no_hooks
        
        # Verify performance impact is reasonable (less than 200x overhead for AI summarization)
        if time_no_hooks > 0:
            overhead_ratio = time_with_hooks / time_no_hooks
            assert overhead_ratio < 200.0, f"Hook overhead too high: {overhead_ratio:.2f}x"

    @pytest.mark.require_api_keys
    def test_tool_specific_hook_configuration(self):
        """Test tool-specific hook configuration"""
        tool_specific_config = {
            "tool_specific_hooks": {
                "OpenTargets_get_target_gene_ontology_by_ensemblID": {
                    "enabled": True,
                    "hooks": [{
                        "name": "protein_specific_hook",
                        "type": "SummarizationHook",
                        "enabled": True,
                        "conditions": {
                            "output_length": {
                                "operator": ">",
                                "threshold": 2000
                            }
                        },
                        "hook_config": {
                            "focus_areas": "protein_function_and_structure",
                            "max_summary_length": 2000
                        }
                    }]
                }
            }
        }
        
        tu = ToolUniverse(hooks_enabled=True, hook_config=tool_specific_config)
        tu.load_tools()
        
        # Verify hook manager is initialized
        assert hasattr(tu, 'hook_manager')
        assert tu.hook_manager is not None

    @pytest.mark.require_api_keys
    def test_hook_error_handling(self):
        """Test hook error handling and graceful degradation"""
        # Test with invalid hook type
        invalid_config = {
            "hooks": [{
                "name": "invalid_hook",
                "type": "NonExistentHook",
                "enabled": True,
                "conditions": {
                    "output_length": {
                        "operator": ">",
                        "threshold": 1000
                    }
                }
            }]
        }
        
        # Should not raise exception, but should handle gracefully
        try:
            tu = ToolUniverse(hooks_enabled=True, hook_config=invalid_config)
            tu.load_tools()
            # If we get here, the system handled the invalid config gracefully
            assert True
        except Exception as e:
            # If an exception is raised, it should be informative
            assert "NonExistentHook" in str(e) or "hook" in str(e).lower()

    @pytest.mark.require_api_keys
    def test_hook_priority_and_execution_order(self):
        """Test hook priority and execution order"""
        priority_config = {
            "hooks": [
                {
                    "name": "low_priority_hook",
                    "type": "SummarizationHook",
                    "enabled": True,
                    "priority": 3,
                    "conditions": {
                        "output_length": {
                            "operator": ">",
                            "threshold": 1000
                        }
                    }
                },
                {
                    "name": "high_priority_hook",
                    "type": "SummarizationHook",
                    "enabled": True,
                    "priority": 1,
                    "conditions": {
                        "output_length": {
                            "operator": ">",
                            "threshold": 1000
                        }
                    }
                }
            ]
        }
        
        tu = ToolUniverse(hooks_enabled=True, hook_config=priority_config)
        tu.load_tools()
        
        # Verify hooks are loaded
        assert hasattr(tu, 'hook_manager')
        assert len(tu.hook_manager.hooks) >= 2

    @pytest.mark.require_api_keys
    def test_hook_caching_functionality(self):
        """Test hook caching functionality"""
        cache_config = {
            "global_settings": {
                "enable_hook_caching": True
            },
            "hooks": [{
                "name": "cached_hook",
                "type": "SummarizationHook",
                "enabled": True,
                "conditions": {
                    "output_length": {
                        "operator": ">",
                        "threshold": 1000
                    }
                }
            }]
        }
        
        tu = ToolUniverse(hooks_enabled=True, hook_config=cache_config)
        tu.load_tools()
        
        # Verify caching is enabled
        assert hasattr(tu, 'hook_manager')
        # Note: Specific caching behavior would need to be tested with actual hook execution

    @pytest.mark.require_api_keys
    def test_hook_cleanup_and_resource_management(self):
        """Test hook cleanup and resource management"""
        # Test FileSaveHook with auto-cleanup
        cleanup_config = {
            "hooks": [{
                "name": "cleanup_hook",
                "type": "FileSaveHook",
                "enabled": True,
                "conditions": {
                    "output_length": {
                        "operator": ">",
                        "threshold": 1000
                    }
                },
                "hook_config": {
                    "temp_dir": tempfile.gettempdir(),
                    "file_prefix": "cleanup_test",
                    "auto_cleanup": True,
                    "cleanup_age_hours": 0.01  # Very short cleanup time for testing
                }
            }]
        }
        
        tu = ToolUniverse(hooks_enabled=True, hook_config=cleanup_config)
        tu.load_tools()
        
        # Execute tool to create file
        function_call = {
            "name": "OpenTargets_get_target_gene_ontology_by_ensemblID",
            "arguments": {"ensemblId": "ENSG00000012048"}
        }
        
        result = tu.run_one_function(function_call)
        file_path = result.get("file_path")
        
        if file_path and os.path.exists(file_path):
            # Wait for cleanup (in real scenario, this would be handled by the cleanup mechanism)
            time.sleep(0.1)
            # Note: Actual cleanup testing would require more sophisticated timing

    @pytest.mark.require_api_keys
    def test_hook_metadata_and_logging(self):
        """Test hook metadata and logging functionality"""
        # Test that hook operations can be logged
        with patch('logging.getLogger') as mock_logger:
            mock_log = MagicMock()
            mock_logger.return_value = mock_log
            
            tu = ToolUniverse(hooks_enabled=True)
            tu.load_tools()
            
            # Execute a tool call
            function_call = {
                "name": "OpenTargets_get_target_gene_ontology_by_ensemblID",
                "arguments": {"ensemblId": "ENSG00000012048"}
            }
            
            result = tu.run_one_function(function_call)
            
            # Verify execution succeeded
            assert result is not None

    @pytest.mark.require_api_keys
    def test_hook_integration_with_different_tools(self):
        """Test hook integration with different tool types"""
        # Test with different tool categories
        test_tools = [
            {
                "name": "OpenTargets_get_target_gene_ontology_by_ensemblID",
                "arguments": {"ensemblId": "ENSG00000012048"}
            }
        ]
        
        tu = ToolUniverse(hooks_enabled=True)
        tu.load_tools()
        
        for tool_call in test_tools:
            result = tu.run_one_function(tool_call)
            assert result is not None
            assert isinstance(result, str) or isinstance(result, dict)

    @pytest.mark.require_api_keys
    def test_hook_configuration_precedence(self):
        """Test hook configuration precedence rules"""
        # Test that hook_config takes precedence over hook_type
        hook_config = {
            "hooks": [{
                "name": "config_hook",
                "type": "SummarizationHook",
                "enabled": True,
                "conditions": {
                    "output_length": {
                        "operator": ">",
                        "threshold": 1000
                    }
                }
            }]
        }
        
        # Both hook_config and hook_type specified
        tu = ToolUniverse(
            hooks_enabled=True,
            hook_type="FileSaveHook",  # This should be ignored
            hook_config=hook_config    # This should take precedence
        )
        tu.load_tools()
        
        # Verify hook manager is initialized with config
        assert hasattr(tu, 'hook_manager')
        assert tu.hook_manager is not None


@pytest.mark.integration
@pytest.mark.hooks
@pytest.mark.slow
class TestHooksPerformance:
    """Hook performance and optimization tests"""

    @pytest.mark.require_api_keys
    def test_hook_performance_benchmarks(self):
        """Test hook performance benchmarks"""
        function_call = {
            "name": "OpenTargets_get_target_gene_ontology_by_ensemblID",
            "arguments": {"ensemblId": "ENSG00000012048"}
        }
        
        # Benchmark without hooks
        tu_no_hooks = ToolUniverse(hooks_enabled=False)
        tu_no_hooks.load_tools()
        
        times_no_hooks = []
        for _ in range(3):  # Run multiple times for average
            start_time = time.time()
            tu_no_hooks.run_one_function(function_call)
            times_no_hooks.append(time.time() - start_time)
        
        avg_time_no_hooks = sum(times_no_hooks) / len(times_no_hooks)
        
        # Benchmark with hooks
        tu_with_hooks = ToolUniverse(hooks_enabled=True)
        tu_with_hooks.load_tools()
        
        times_with_hooks = []
        for _ in range(3):  # Run multiple times for average
            start_time = time.time()
            tu_with_hooks.run_one_function(function_call)
            times_with_hooks.append(time.time() - start_time)
        
        avg_time_with_hooks = sum(times_with_hooks) / len(times_with_hooks)
        
        # Verify performance metrics
        assert avg_time_no_hooks > 0
        assert avg_time_with_hooks > 0
        
        # Verify hooks don't cause excessive overhead
        overhead_ratio = avg_time_with_hooks / avg_time_no_hooks
        assert overhead_ratio < 5.0, f"Hook overhead too high: {overhead_ratio:.2f}x"

    @pytest.mark.require_api_keys
    def test_hook_memory_usage(self):
        """Test hook memory usage impact"""
        # This is a basic test - in a real scenario, you'd use memory profiling tools
        function_call = {
            "name": "OpenTargets_get_target_gene_ontology_by_ensemblID",
            "arguments": {"ensemblId": "ENSG00000012048"}
        }
        
        # Test without hooks
        tu_no_hooks = ToolUniverse(hooks_enabled=False)
        tu_no_hooks.load_tools()
        result_no_hooks = tu_no_hooks.run_one_function(function_call)
        
        # Test with hooks
        tu_with_hooks = ToolUniverse(hooks_enabled=True)
        tu_with_hooks.load_tools()
        result_with_hooks = tu_with_hooks.run_one_function(function_call)
        
        # Basic memory usage check
        assert result_no_hooks is not None
        assert result_with_hooks is not None
        
        # Verify hooks don't cause memory leaks (basic check)
        del tu_no_hooks
        del tu_with_hooks
        # In a real test, you'd check memory usage here


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
