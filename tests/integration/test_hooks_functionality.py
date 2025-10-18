#!/usr/bin/env python3
"""
Test hooks functionality comprehensively

This test file covers hook functionality:
1. SummarizationHook basic functionality
2. Hook tool loading and availability
3. Hook processing with different output types
4. Hook error handling and recovery
5. Hook performance and timeout handling
"""

import pytest
import json
import time
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tooluniverse import ToolUniverse
from tooluniverse.output_hook import SummarizationHook, HookManager
from tooluniverse.default_config import get_default_hook_config


@pytest.mark.integration
@pytest.mark.hooks
class TestHooksFunctionality:
    """Test comprehensive hooks functionality"""

    def setup_method(self):
        """Setup for each test method"""
        self.tu = ToolUniverse()
        self.tu.load_tools()

    def test_summarization_hook_initialization(self):
        """Test SummarizationHook can be initialized"""
        hook_config = {
            "composer_tool": "OutputSummarizationComposer",
            "chunk_size": 1000,
            "focus_areas": "key findings, results, conclusions",
            "max_summary_length": 500
        }
        
        hook = SummarizationHook(
            config={"hook_config": hook_config},
            tooluniverse=self.tu
        )
        
        assert hook is not None
        assert hook.composer_tool == "OutputSummarizationComposer"
        assert hook.chunk_size == 1000
        assert hook.focus_areas == "key findings, results, conclusions"
        assert hook.max_summary_length == 500

    def test_hook_tools_availability(self):
        """Test that hook tools are available after enabling hooks"""
        # Enable hooks
        self.tu.toggle_hooks(True)
        
        # Trigger hook tools loading by calling a tool that would use hooks
        # This ensures the hook tools are actually loaded into callable_functions
        test_function_call = {
            "name": "OpenTargets_get_target_gene_ontology_by_ensemblID",
            "arguments": {"ensemblId": "ENSG00000012048"}
        }
        
        # This will trigger hook tools loading
        try:
            self.tu.run_one_function(test_function_call)
        except Exception:
            # We don't care about the result, just that it loads the tools
            pass
        
        # Check that hook tools are in callable_functions
        assert "ToolOutputSummarizer" in self.tu.callable_functions
        assert "OutputSummarizationComposer" in self.tu.callable_functions
        
        # Check that tools can be called
        summarizer = self.tu.callable_functions["ToolOutputSummarizer"]
        composer = self.tu.callable_functions["OutputSummarizationComposer"]
        
        assert summarizer is not None
        assert composer is not None

    def test_summarization_hook_with_short_text(self):
        """Test SummarizationHook with short text (should not summarize)"""
        hook_config = {
            "composer_tool": "OutputSummarizationComposer",
            "chunk_size": 1000,
            "focus_areas": "key findings, results, conclusions",
            "max_summary_length": 500
        }
        
        hook = SummarizationHook(
            config={"hook_config": hook_config},
            tooluniverse=self.tu
        )
        
        # Short text should not be summarized
        short_text = "This is a short text that should not be summarized."
        result = hook.process(
            result=short_text,
            tool_name="test_tool",
            arguments={"test": "arg"},
            context={"query": "test query"}
        )
        
        assert result == short_text  # Should return original text

    def test_summarization_hook_with_long_text(self):
        """Test SummarizationHook with long text (should summarize)"""
        # Enable hooks
        self.tu.toggle_hooks(True)
        
        hook_config = {
            "composer_tool": "OutputSummarizationComposer",
            "chunk_size": 1000,
            "focus_areas": "key findings, results, conclusions",
            "max_summary_length": 500
        }
        
        hook = SummarizationHook(
            config={"hook_config": hook_config},
            tooluniverse=self.tu
        )
        
        # Create long text that should be summarized
        long_text = "This is a very long text. " * 100  # ~2500 characters
        
        # Mock the composer tool to avoid actual LLM calls in tests
        with patch.object(self.tu, 'run_one_function') as mock_run:
            mock_run.return_value = "This is a summarized version of the long text."
            
            result = hook.process(long_text)
            
            # Should return summarized text
            assert result != long_text
            assert len(result) < len(long_text)
            assert "summarized" in result.lower()

    def test_hook_manager_initialization(self):
        """Test HookManager can be initialized and configured"""
        hook_manager = HookManager(get_default_hook_config(), self.tu)
        
        assert hook_manager is not None
        assert hook_manager.tooluniverse == self.tu

    def test_hook_manager_enable_hooks(self):
        """Test HookManager can enable hooks"""
        hook_manager = HookManager(get_default_hook_config(), self.tu)
        
        # Enable hooks
        hook_manager.enable_hooks()
        
        # Check that hooks are enabled
        assert hook_manager.hooks_enabled
        assert len(hook_manager.hooks) > 0

    def test_hook_manager_disable_hooks(self):
        """Test HookManager can disable hooks"""
        hook_manager = HookManager(get_default_hook_config(), self.tu)
        
        # Enable then disable hooks
        hook_manager.enable_hooks()
        hook_manager.disable_hooks()
        
        # Check that hooks are disabled
        assert not hook_manager.hooks_enabled
        assert len(hook_manager.hooks) == 0

    def test_hook_processing_with_different_output_types(self):
        """Test hook processing with different output types"""
        # Enable hooks
        self.tu.toggle_hooks(True)
        
        hook_config = {
            "composer_tool": "OutputSummarizationComposer",
            "chunk_size": 1000,
            "focus_areas": "key findings, results, conclusions",
            "max_summary_length": 500
        }
        
        hook = SummarizationHook(
            config={"hook_config": hook_config},
            tooluniverse=self.tu
        )
        
        # Test with string output
        string_output = "This is a string output. " * 50
        result = hook.process(string_output)
        assert isinstance(result, str)
        
        # Test with dict output
        dict_output = {"data": "This is a dict output. " * 50, "status": "success"}
        result = hook.process(dict_output)
        assert isinstance(result, (str, dict))

    def test_hook_error_handling(self):
        """Test hook error handling and recovery"""
        # Enable hooks
        self.tu.toggle_hooks(True)
        
        hook_config = {
            "composer_tool_name": "OutputSummarizationComposer",
            "chunk_size": 1000,
            "focus_areas": "key findings, results, conclusions",
            "max_summary_length": 500
        }
        
        hook = SummarizationHook(
            config={"hook_config": hook_config},
            tooluniverse=self.tu
        )
        
        # Mock the composer tool to raise an exception
        with patch.object(self.tu, 'run_one_function') as mock_run:
            mock_run.side_effect = Exception("Test error")
            
            long_text = "This is a very long text. " * 100
            
            # Should handle error gracefully and return original text
            result = hook.process(long_text)
            assert result == long_text  # Should return original text on error

    def test_hook_timeout_handling(self):
        """Test hook timeout handling"""
        # Enable hooks
        self.tu.toggle_hooks(True)
        
        hook_config = {
            "composer_tool": "OutputSummarizationComposer",
            "chunk_size": 1000,
            "focus_areas": "key findings, results, conclusions",
            "max_summary_length": 500,
            "composer_timeout_sec": 1  # Very short timeout
        }
        
        hook = SummarizationHook(
            config={"hook_config": hook_config},
            tooluniverse=self.tu
        )
        
        # Mock the composer tool to take a long time
        def slow_run(*args, **kwargs):
            time.sleep(2)  # Longer than timeout
            return "This is a summarized version."
        
        with patch.object(self.tu, 'run_one_function', side_effect=slow_run):
            long_text = "This is a very long text. " * 100
            
            # Should handle timeout gracefully and return original text
            result = hook.process(long_text)
            assert result == long_text  # Should return original text on timeout

    def test_hook_with_real_tool_call(self):
        """Test hook with real tool call (if API keys are available)"""
        # Enable hooks
        self.tu.toggle_hooks(True)
        
        # Test with a simple tool call
        function_call = {
            "name": "get_server_info",
            "arguments": {}
        }
        
        # This should work with or without hooks
        result = self.tu.run_one_function(function_call)
        assert result is not None

    def test_hook_configuration_validation(self):
        """Test hook configuration validation"""
        # Test with invalid configuration
        invalid_config = {
            "composer_tool": "NonExistentTool",
            "chunk_size": -1,  # Invalid
            "max_summary_length": -1  # Invalid
        }
        
        # Should handle invalid config gracefully
        hook = SummarizationHook(
            config={"hook_config": invalid_config},
            tooluniverse=self.tu
        )
        
        assert hook is not None
        # Should use default values for invalid config
        assert hook.chunk_size > 0
        assert hook.max_summary_length > 0

    def test_hook_performance_metrics(self):
        """Test hook performance metrics"""
        # Enable hooks
        self.tu.toggle_hooks(True)
        
        hook_config = {
            "composer_tool": "OutputSummarizationComposer",
            "chunk_size": 1000,
            "focus_areas": "key findings, results, conclusions",
            "max_summary_length": 500
        }
        
        hook = SummarizationHook(
            config={"hook_config": hook_config},
            tooluniverse=self.tu
        )
        
        # Mock the composer tool
        with patch.object(self.tu, 'run_one_function') as mock_run:
            mock_run.return_value = "This is a summarized version."
            
            long_text = "This is a very long text. " * 100
            
            start_time = time.time()
            result = hook.process(long_text)
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            # Should complete within reasonable time
            assert processing_time < 10  # Should be much faster with mocked LLM
            assert result is not None

    def test_hook_with_empty_output(self):
        """Test hook with empty output"""
        # Enable hooks
        self.tu.toggle_hooks(True)
        
        hook_config = {
            "composer_tool": "OutputSummarizationComposer",
            "chunk_size": 1000,
            "focus_areas": "key findings, results, conclusions",
            "max_summary_length": 500
        }
        
        hook = SummarizationHook(
            config={"hook_config": hook_config},
            tooluniverse=self.tu
        )
        
        # Test with empty string
        result = hook.process(
            result="",
            tool_name="test_tool",
            arguments={"test": "arg"},
            context={"query": "test query"}
        )
        assert result == ""
        
        # Test with None
        result = hook.process(
            result=None,
            tool_name="test_tool",
            arguments={"test": "arg"},
            context={"query": "test query"}
        )
        assert result is None

    def test_hook_with_very_long_output(self):
        """Test hook with very long output"""
        # Enable hooks
        self.tu.toggle_hooks(True)
        
        hook_config = {
            "composer_tool_name": "OutputSummarizationComposer",
            "chunk_size": 1000,
            "focus_areas": "key findings, results, conclusions",
            "max_summary_length": 500
        }
        
        hook = SummarizationHook(
            config={"hook_config": hook_config},
            tooluniverse=self.tu
        )
        
        # Create very long text
        very_long_text = "This is a very long text. " * 1000  # ~25000 characters
        
        # Mock the composer tool
        with patch.object(self.tu, 'run_one_function') as mock_run:
            mock_run.return_value = "This is a summarized version of the very long text."
            
            result = hook.process(very_long_text)
            
            # Should return summarized text
            assert result != very_long_text
            assert len(result) < len(very_long_text)
            assert "summarized" in result.lower()
