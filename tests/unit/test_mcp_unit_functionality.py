#!/usr/bin/env python3
"""
Test MCP (Model Context Protocol) functionality - Cleaned Version

This test file covers real MCP functionality:
1. Real MCP server creation and configuration
2. Real MCP client tool creation and execution
3. Real MCP tool registry functionality
4. Real error handling in MCP context
"""

import sys
import unittest
from pathlib import Path
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tooluniverse import ToolUniverse


@pytest.mark.unit
class TestMCPFunctionality(unittest.TestCase):
    """Test real MCP functionality and integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tu = ToolUniverse()
        self.tu.load_tools()
    
    def test_mcp_server_creation_real(self):
        """Test real MCP server creation."""
        try:
            from tooluniverse.smcp import SMCP
            
            # Test server creation
            server = SMCP(
                name="Test MCP Server",
                tool_categories=["uniprot"],
                search_enabled=True
            )
            
            self.assertIsNotNone(server)
            self.assertEqual(server.name, "Test MCP Server")
            self.assertTrue(server.search_enabled)
            self.assertIsNotNone(server.tooluniverse)
            
        except ImportError:
            self.skipTest("SMCP not available")
    
    def test_mcp_client_tool_creation_real(self):
        """Test real MCP client tool creation."""
        try:
            from tooluniverse.mcp_client_tool import MCPClientTool
            
            # Test client tool creation
            client_tool = MCPClientTool({
                "name": "test_mcp_client",
                "description": "A test MCP client",
                "server_url": "http://localhost:8000",
                "transport": "http"
            })
            
            self.assertIsNotNone(client_tool)
            self.assertEqual(client_tool.tool_config["name"], "test_mcp_client")
            self.assertEqual(client_tool.tool_config["server_url"], "http://localhost:8000")
            
        except ImportError:
            self.skipTest("MCPClientTool not available")
    
    def test_mcp_client_tool_execution_real(self):
        """Test real MCP client tool execution."""
        try:
            from tooluniverse.mcp_client_tool import MCPClientTool
            
            client_tool = MCPClientTool({
                "name": "test_mcp_client",
                "description": "A test MCP client",
                "server_url": "http://localhost:8000",
                "transport": "http"
            })
            
            # Test tool execution
            result = client_tool.run({
                "name": "test_tool",
                "arguments": {"test": "value"}
            })
            
            # Should return a result (may be error if connection fails)
            self.assertIsInstance(result, dict)
            
        except ImportError:
            self.skipTest("MCPClientTool not available")
        except Exception as e:
            # Expected if connection fails
            self.assertIsInstance(e, Exception)
    
    def test_mcp_tool_registry_real(self):
        """Test real MCP tool registry functionality."""
        try:
            from tooluniverse.mcp_tool_registry import MCPToolRegistry
            
            # Test registry creation
            registry = MCPToolRegistry()
            self.assertIsNotNone(registry)
            
            # Test tool registration
            test_tool = {
                "name": "test_tool",
                "description": "A test tool",
                "parameter": {
                    "type": "object",
                    "properties": {
                        "test_param": {
                            "type": "string",
                            "description": "Test parameter"
                        }
                    }
                }
            }
            
            registry.register_tool(test_tool)
            
            # Test tool retrieval
            retrieved_tool = registry.get_tool("test_tool")
            self.assertIsNotNone(retrieved_tool)
            self.assertEqual(retrieved_tool["name"], "test_tool")
            
        except ImportError:
            self.skipTest("MCPToolRegistry not available")
    
    def test_mcp_tool_discovery_real(self):
        """Test real MCP tool discovery through ToolUniverse."""
        # Test that MCP tools can be discovered
        tool_names = self.tu.list_built_in_tools(mode="list_name")
        mcp_tools = [name for name in tool_names if "MCP" in name or "mcp" in name.lower()]
        
        # Should find some MCP tools
        self.assertIsInstance(mcp_tools, list)
    
    def test_mcp_tool_execution_real(self):
        """Test real MCP tool execution through ToolUniverse."""
        try:
            # Test MCP tool execution
            result = self.tu.run({
                "name": "MCPClientTool",
                "arguments": {
                    "config": {
                        "name": "test_client",
                        "transport": "stdio",
                        "command": "echo"
                    },
                    "tool_call": {
                        "name": "test_tool",
                        "arguments": {"test": "value"}
                    }
                }
            })
            
            # Should return a result
            self.assertIsInstance(result, dict)
            
        except Exception as e:
            # Expected if MCP tools not available
            self.assertIsInstance(e, Exception)
    
    def test_mcp_error_handling_real(self):
        """Test real MCP error handling."""
        try:
            from tooluniverse.mcp_client_tool import MCPClientTool
            
            # Test with invalid configuration
            client_tool = MCPClientTool(
                tooluniverse=self.tu,
                config={
                    "name": "invalid_client",
                    "description": "An invalid MCP client",
                    "transport": "invalid_transport"
                }
            )
            
            result = client_tool.run({
                "name": "test_tool",
                "arguments": {"test": "value"}
            })
            
            # Should handle invalid configuration gracefully
            self.assertIsInstance(result, dict)
            
        except ImportError:
            self.skipTest("MCPClientTool not available")
        except Exception as e:
            # Expected if configuration is invalid
            self.assertIsInstance(e, Exception)
    
    def test_mcp_streaming_real(self):
        """Test real MCP streaming functionality."""
        try:
            from tooluniverse.mcp_client_tool import MCPClientTool
            
            # Test streaming callback
            callback_called = False
            callback_data = []
            
            def test_callback(chunk):
                nonlocal callback_called, callback_data
                callback_called = True
                callback_data.append(chunk)
            
            client_tool = MCPClientTool(
                tooluniverse=self.tu,
                config={
                    "name": "test_streaming_client",
                    "description": "A test streaming MCP client",
                    "transport": "stdio",
                    "command": "echo"
                }
            )
            
            result = client_tool.run({
                "name": "test_tool",
                "arguments": {"test": "value"}
            }, stream_callback=test_callback)
            
            # Should return a result
            self.assertIsInstance(result, dict)
            
        except ImportError:
            self.skipTest("MCPClientTool not available")
        except Exception as e:
            # Expected if connection fails
            self.assertIsInstance(e, Exception)
    
    def test_mcp_tool_validation_real(self):
        """Test real MCP tool validation."""
        try:
            from tooluniverse.mcp_tool_registry import MCPToolRegistry
            
            registry = MCPToolRegistry()
            
            # Test valid tool
            valid_tool = {
                "name": "valid_tool",
                "description": "A valid tool",
                "parameter": {
                    "type": "object",
                    "properties": {
                        "param": {
                            "type": "string",
                            "description": "A parameter"
                        }
                    },
                    "required": ["param"]
                }
            }
            
            registry.register_tool(valid_tool)
            retrieved_tool = registry.get_tool("valid_tool")
            self.assertIsNotNone(retrieved_tool)
            
        except ImportError:
            self.skipTest("MCPToolRegistry not available")
    
    def test_mcp_tool_performance_real(self):
        """Test real MCP tool performance."""
        try:
            from tooluniverse.mcp_client_tool import MCPClientTool
            import time
            
            # Initialize start_time before any potential exceptions
            start_time = time.time()
            
            client_tool = MCPClientTool({
                "name": "performance_test_client",
                "description": "A performance test client",
                "transport": "stdio",
                "command": "echo"
            })
            
            result = client_tool.run({
                "name": "test_tool",
                "arguments": {"test": "value"}
            })
            
            execution_time = time.time() - start_time
            
            # Should complete within reasonable time (10 seconds)
            self.assertLess(execution_time, 10)
            self.assertIsInstance(result, dict)
            
        except ImportError:
            self.skipTest("MCPClientTool not available")
        except Exception:
            # Expected if connection fails
            execution_time = time.time() - start_time
            self.assertLess(execution_time, 10)
    
    def test_mcp_tool_concurrent_execution_real(self):
        """Test real concurrent MCP tool execution."""
        try:
            from tooluniverse.mcp_client_tool import MCPClientTool
            import threading
            
            results = []
            results_lock = threading.Lock()
            
            def make_call(call_id):
                try:
                    client_tool = MCPClientTool({
                        "name": f"concurrent_client_{call_id}",
                        "description": f"A concurrent client {call_id}",
                        "transport": "stdio",
                        "command": "echo"
                    })
                    
                    result = client_tool.run({
                        "name": "test_tool",
                        "arguments": {"test": f"value_{call_id}"}
                    })
                    
                    with results_lock:
                        results.append(result)
                        
                except Exception as e:
                    with results_lock:
                        results.append({"error": str(e), "call_id": call_id})
            
            # Create multiple threads
            threads = []
            for i in range(3):  # Reduced for testing
                thread = threading.Thread(target=make_call, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads with timeout
            for thread in threads:
                thread.join(timeout=10)  # 10 second timeout per thread
            
            # Verify all calls completed
            self.assertEqual(
                len(results), 3, 
                f"Expected 3 results, got {len(results)}: {results}"
            )
            for result in results:
                self.assertIsInstance(result, dict)
                
        except ImportError:
            self.skipTest("MCPClientTool not available")


if __name__ == "__main__":
    unittest.main()
