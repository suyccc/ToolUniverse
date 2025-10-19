Remote Tool Registration
==================================

Learn how to integrate external services, APIs, and tools running on different servers with ToolUniverse. This Tutorial covers MCP integration, REST API wrappers, and advanced remote tool patterns.

Overview
--------

Remote tools allow you to integrate external services, APIs, or tools running on different servers. This is useful for:

- Integrating with existing microservices
- Using tools that require specific environments
- Scaling computationally intensive operations
- Connecting to proprietary systems
- Leveraging cloud-based AI services

**Key Benefits:**
- ✅ **Scalability**: Offload heavy computation to dedicated servers
- ✅ **Integration**: Connect with existing systems and services
- ✅ **Flexibility**: Use tools in different programming languages
- ✅ **Isolation**: Keep sensitive operations separate
- ✅ **Performance**: Optimize for specific hardware requirements

.. note::

    Want to perform batch inference on agentic tools? See :doc:`../tools/remote/vllm_batch_inference` for the batch-inference setup.

Quick Start
-----------

Here's the fastest way to integrate a remote tool using MCP (Model Context Protocol):

.. code-block:: python

   # Configure MCP tools in your ToolUniverse setup
   from tooluniverse import ToolUniverse
   from tooluniverse.mcp_tool_registry import load_mcp_tools_to_tooluniverse

   # Initialize ToolUniverse
   tu = ToolUniverse()

   # Load MCP tools from a remote server
   load_mcp_tools_to_tooluniverse(
       tu,
       mcp_server_url="http://localhost:8000",
       tool_prefix="remote_"
   )

   # Use remote tools
   result = tu.run_one_function({
       "name": "remote_complex_analysis",
       "arguments": {"data": [1, 2, 3, 4, 5]}
   })

MCP (Model Context Protocol) Integration
----------------------------------------

MCP is the recommended way to integrate remote tools with ToolUniverse. It provides a standardized protocol for tool communication.

Setting up an MCP Server
~~~~~~~~~~~~~~~~~~~~~~~~~

Create a simple MCP server:

.. code-block:: python

   # mcp_server.py
   from fastapi import FastAPI
   from tooluniverse.mcp_server import MCPServer
   import asyncio

   app = FastAPI()
   mcp = MCPServer()

   @mcp.tool("complex_analysis")
   def complex_analysis(data: list) -> dict:
       """Perform complex analysis on data."""
       # Heavy computation here
       result = sum(data) * 2  # Simplified example
       return {"analysis_result": result, "data_points": len(data)}

   @mcp.tool("weather_forecast")
   def weather_forecast(city: str, days: int = 7) -> dict:
       """Get weather forecast for a city."""
       # Simulate API call
       return {
           "city": city,
           "forecast": [{"day": i, "temp": 20 + i, "condition": "sunny"} for i in range(days)]
       }

   # Mount MCP endpoints
   app.mount("/mcp", mcp.app)

   if __name__ == "__main__":
       import uvicorn
       uvicorn.run(app, host="0.0.0.0", port=8000)

Advanced MCP Server with Authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # secure_mcp_server.py
   from fastapi import FastAPI, HTTPException, Depends
   from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
   from tooluniverse.mcp_server import MCPServer
   import os

   app = FastAPI()
   mcp = MCPServer()
   security = HTTPBearer()

   def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
       """Verify API token."""
       if credentials.credentials != os.getenv("MCP_API_TOKEN"):
           raise HTTPException(status_code=401, detail="Invalid token")
       return credentials.credentials

   @mcp.tool("secure_data_processing")
   def secure_data_processing(data: dict, token: str = Depends(verify_token)) -> dict:
       """Process sensitive data with authentication."""
       # Process data securely
       processed_data = {k: v * 2 for k, v in data.items()}
       return {"processed_data": processed_data, "status": "success"}

   app.mount("/mcp", mcp.app)

Connecting to MCP Servers
~~~~~~~~~~~~~~~~~~~~~~~~~~

Connect to remote MCP servers from ToolUniverse:

.. code-block:: python

   from tooluniverse import ToolUniverse
   from tooluniverse.mcp_tool_registry import load_mcp_tools_to_tooluniverse

   # Initialize ToolUniverse
   tu = ToolUniverse()

   # Load tools from multiple MCP servers
   load_mcp_tools_to_tooluniverse(
       tu,
       mcp_server_url="http://localhost:8000",
       tool_prefix="local_",
       auth_token="your-api-token"
   )

   load_mcp_tools_to_tooluniverse(
       tu,
       mcp_server_url="https://remote-server.com/mcp",
       tool_prefix="cloud_",
       auth_token="cloud-api-token"
   )

   # Use tools from different servers
   result1 = tu.run_one_function({
       "name": "local_complex_analysis",
       "arguments": {"data": [1, 2, 3]}
   })

   result2 = tu.run_one_function({
       "name": "cloud_weather_forecast",
       "arguments": {"city": "New York", "days": 5}
   })

REST API Integration
--------------------

For simple REST API integration, create wrapper tools:

Basic REST API Wrapper
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from tooluniverse.tool_registry import register_tool
   import requests

   @register_tool('RESTAPITool', config={
       "name": "rest_api_call",
       "type": "RESTAPITool",
       "description": "Make REST API calls to external services",
       "parameter": {
           "type": "object",
           "properties": {
               "url": {"type": "string", "description": "API endpoint URL"},
               "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"], "default": "GET"},
               "headers": {"type": "object", "description": "HTTP headers"},
               "data": {"type": "object", "description": "Request body data"},
               "params": {"type": "object", "description": "URL parameters"}
           },
           "required": ["url"]
       },
       "settings": {
           "default_timeout": 30,
           "max_retries": 3
       }
   })
   class RESTAPITool:
       def __init__(self, tool_config=None):
           self.tool_config = tool_config or {}
           self.default_timeout = self.tool_config.get("settings", {}).get("default_timeout", 30)
           self.max_retries = self.tool_config.get("settings", {}).get("max_retries", 3)

       def run(self, arguments):
           try:
               url = arguments["url"]
               method = arguments.get("method", "GET").upper()
               headers = arguments.get("headers", {})
               data = arguments.get("data", {})
               params = arguments.get("params", {})

               response = requests.request(
                   method=method,
                   url=url,
                   headers=headers,
                   json=data if method in ["POST", "PUT"] else None,
                   params=params,
                   timeout=self.default_timeout
               )

               response.raise_for_status()

               return {
                   "status_code": response.status_code,
                   "data": response.json() if response.content else None,
                   "headers": dict(response.headers),
                   "success": True
               }
           except requests.RequestException as e:
               return {"error": str(e), "success": False}

Advanced REST API Wrapper with Retry Logic
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import time
   import random
   from requests.exceptions import RequestException

   class RobustRESTAPITool(RESTAPITool):
       def run(self, arguments):
           last_exception = None

           for attempt in range(self.max_retries + 1):
               try:
                   return super().run(arguments)
               except RequestException as e:
                   last_exception = e
                   if attempt < self.max_retries:
                       # Exponential backoff with jitter
                       delay = (2 ** attempt) + random.uniform(0, 1)
                       time.sleep(delay)
                   continue

           return {"error": f"Failed after {self.max_retries} retries: {str(last_exception)}", "success": False}

Specialized API Wrappers
------------------------

OpenAI API Wrapper
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   @register_tool('OpenAITool', config={
       "name": "openai_completion",
       "type": "OpenAITool",
       "description": "Generate text completions using OpenAI API",
       "parameter": {
           "type": "object",
           "properties": {
               "prompt": {"type": "string", "description": "Text prompt"},
               "model": {"type": "string", "enum": ["gpt-3.5-turbo", "gpt-4"], "default": "gpt-3.5-turbo"},
               "max_tokens": {"type": "integer", "minimum": 1, "maximum": 4000, "default": 100},
               "temperature": {"type": "number", "minimum": 0, "maximum": 2, "default": 0.7}
           },
           "required": ["prompt"]
       },
       "settings": {
           "api_key": "env:OPENAI_API_KEY",
           "base_url": "https://api.openweathermap.org/v1"
       }
   })
   class OpenAITool:
       def __init__(self, tool_config=None):
           self.tool_config = tool_config or {}
           self.api_key = self.tool_config.get("settings", {}).get("api_key")
           self.base_url = self.tool_config.get("settings", {}).get("base_url")

       def run(self, arguments):
           try:
               import openai

               openai.api_key = self.api_key

               response = openai.ChatCompletion.create(
                   model=arguments.get("model", "gpt-3.5-turbo"),
                   messages=[{"role": "user", "content": arguments["prompt"]}],
                   max_tokens=arguments.get("max_tokens", 100),
                   temperature=arguments.get("temperature", 0.7)
               )

               return {
                   "completion": response.choices[0].message.content,
                   "usage": response.usage,
                   "model": response.model,
                   "success": True
               }
           except Exception as e:
               return {"error": str(e), "success": False}

Weather API Wrapper
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   @register_tool('WeatherAPITool', config={
       "name": "weather_api",
       "type": "WeatherAPITool",
       "description": "Get weather data from OpenWeatherMap API",
       "parameter": {
           "type": "object",
           "properties": {
               "city": {"type": "string", "description": "City name"},
               "country_code": {"type": "string", "description": "Country code (e.g., 'US')"},
               "units": {"type": "string", "enum": ["metric", "imperial", "kelvin"], "default": "metric"}
           },
           "required": ["city"]
       },
       "settings": {
           "api_key": "env:OPENWEATHER_API_KEY",
           "base_url": "https://api.openweathermap.org/data/2.5/weather"
       }
   })
   class WeatherAPITool:
       def __init__(self, tool_config=None):
           self.tool_config = tool_config or {}
           self.api_key = self.tool_config.get("settings", {}).get("api_key")
           self.base_url = self.tool_config.get("settings", {}).get("base_url")

       def run(self, arguments):
           try:
               city = arguments["city"]
               country_code = arguments.get("country_code")
               units = arguments.get("units", "metric")

               params = {
                   "q": f"{city},{country_code}" if country_code else city,
                   "appid": self.api_key,
                   "units": units
               }

               response = requests.get(self.base_url, params=params)
               response.raise_for_status()

               data = response.json()

               return {
                   "city": data["name"],
                   "country": data["sys"]["country"],
                   "temperature": data["main"]["temp"],
                   "feels_like": data["main"]["feels_like"],
                   "humidity": data["main"]["humidity"],
                   "pressure": data["main"]["pressure"],
                   "description": data["weather"][0]["description"],
                   "wind_speed": data["wind"]["speed"],
                   "success": True
               }
           except Exception as e:
               return {"error": str(e), "success": False}

Database Connection Wrapper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   @register_tool('DatabaseTool', config={
       "name": "database_query",
       "type": "DatabaseTool",
       "description": "Execute queries on remote database",
       "parameter": {
           "type": "object",
           "properties": {
               "query": {"type": "string", "description": "SQL query"},
               "limit": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 100},
               "params": {"type": "array", "description": "Query parameters"}
           },
           "required": ["query"]
       },
       "settings": {
           "database_url": "env:DATABASE_URL",
           "connection_timeout": 30
       }
   })
   class DatabaseTool:
       def __init__(self, tool_config=None):
           self.tool_config = tool_config or {}
           self.db_url = self.tool_config.get("settings", {}).get("database_url")
           self.timeout = self.tool_config.get("settings", {}).get("connection_timeout", 30)

       def run(self, arguments):
           try:
               import psycopg2
               from psycopg2.extras import RealDictCursor

               query = arguments["query"]
               limit = arguments.get("limit", 100)
               params = arguments.get("params", [])

               conn = psycopg2.connect(self.db_url, connect_timeout=self.timeout)
               cursor = conn.cursor(cursor_factory=RealDictCursor)

               # Add LIMIT if not present
               if "LIMIT" not in query.upper():
                   query = f"{query} LIMIT {limit}"

               cursor.execute(query, params)
               results = cursor.fetchall()

               # Convert to list of dictionaries
               data = [dict(row) for row in results]

               cursor.close()
               conn.close()

               return {
                   "data": data,
                   "count": len(data),
                   "query": query,
                   "success": True
               }
           except Exception as e:
               return {"error": str(e), "success": False}

Microservice Integration
------------------------

Service Discovery
~~~~~~~~~~~~~~~~~

Integrate with microservices using service discovery:

.. code-block:: python

   @register_tool('MicroserviceTool', config={
       "name": "microservice_call",
       "type": "MicroserviceTool",
       "description": "Call microservices with service discovery",
       "parameter": {
           "type": "object",
           "properties": {
               "service_name": {"type": "string", "description": "Name of the microservice"},
               "endpoint": {"type": "string", "description": "API endpoint"},
               "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"], "default": "GET"},
               "data": {"type": "object", "description": "Request data"}
           },
           "required": ["service_name", "endpoint"]
       },
       "settings": {
           "service_registry_url": "env:SERVICE_REGISTRY_URL",
           "default_timeout": 30
       }
   })
   class MicroserviceTool:
       def __init__(self, tool_config=None):
           self.tool_config = tool_config or {}
           self.registry_url = self.tool_config.get("settings", {}).get("service_registry_url")
           self.timeout = self.tool_config.get("settings", {}).get("default_timeout", 30)

       def run(self, arguments):
           try:
               service_name = arguments["service_name"]
               endpoint = arguments["endpoint"]
               method = arguments.get("method", "GET")
               data = arguments.get("data", {})

               # Discover service URL
               service_url = self._discover_service(service_name)

               # Make request
               url = f"{service_url}/{endpoint.lstrip('/')}"

               response = requests.request(
                   method=method,
                   url=url,
                   json=data if method in ["POST", "PUT"] else None,
                   timeout=self.timeout
               )

               response.raise_for_status()

               return {
                   "service_name": service_name,
                   "endpoint": endpoint,
                   "status_code": response.status_code,
                   "data": response.json() if response.content else None,
                   "success": True
               }
           except Exception as e:
               return {"error": str(e), "success": False}

       def _discover_service(self, service_name):
           """Discover service URL from registry."""
           response = requests.get(f"{self.registry_url}/services/{service_name}")
           response.raise_for_status()
           service_info = response.json()
           return service_info["url"]

Circuit Breaker Pattern
~~~~~~~~~~~~~~~~~~~~~~~~

Implement circuit breaker for resilient remote calls:

.. code-block:: python

   import time
   from enum import Enum

   class CircuitState(Enum):
       CLOSED = "closed"
       OPEN = "open"
       HALF_OPEN = "half_open"

   class CircuitBreakerTool:
       def __init__(self, tool_config=None):
           self.tool_config = tool_config or {}
           self.failure_threshold = self.tool_config.get("settings", {}).get("failure_threshold", 5)
           self.recovery_timeout = self.tool_config.get("settings", {}).get("recovery_timeout", 60)
           self.failure_count = 0
           self.last_failure_time = None
           self.state = CircuitState.CLOSED

       def run(self, arguments):
           if self.state == CircuitState.OPEN:
               if time.time() - self.last_failure_time > self.recovery_timeout:
                   self.state = CircuitState.HALF_OPEN
               else:
                   return {"error": "Circuit breaker is OPEN", "success": False}

           try:
               result = self._make_request(arguments)
               self._on_success()
               return result
           except Exception as e:
               self._on_failure()
               return {"error": str(e), "success": False}

       def _make_request(self, arguments):
           """Make the actual request."""
           # Implementation depends on your specific tool
           pass

       def _on_success(self):
           self.failure_count = 0
           self.state = CircuitState.CLOSED

       def _on_failure(self):
           self.failure_count += 1
           self.last_failure_time = time.time()

           if self.failure_count >= self.failure_threshold:
               self.state = CircuitState.OPEN

Load Balancing
~~~~~~~~~~~~~~~

Implement load balancing for multiple service instances:

.. code-block:: python

   import random
   import time

   class LoadBalancedTool:
       def __init__(self, tool_config=None):
           self.tool_config = tool_config or {}
           self.service_instances = self.tool_config.get("settings", {}).get("service_instances", [])
           self.load_balancing_strategy = self.tool_config.get("settings", {}).get("strategy", "round_robin")
           self.current_index = 0
           self.instance_weights = {}

       def run(self, arguments):
           if not self.service_instances:
               return {"error": "No service instances available", "success": False}

           instance = self._select_instance()

           try:
               return self._make_request_to_instance(instance, arguments)
           except Exception as e:
               # Try next instance on failure
               return self._try_next_instance(arguments)

       def _select_instance(self):
           if self.load_balancing_strategy == "round_robin":
               instance = self.service_instances[self.current_index]
               self.current_index = (self.current_index + 1) % len(self.service_instances)
               return instance
           elif self.load_balancing_strategy == "random":
               return random.choice(self.service_instances)
           elif self.load_balancing_strategy == "weighted":
               return self._weighted_selection()
           else:
               return self.service_instances[0]

       def _weighted_selection(self):
           total_weight = sum(self.instance_weights.values())
           random_weight = random.uniform(0, total_weight)

           current_weight = 0
           for instance, weight in self.instance_weights.items():
               current_weight += weight
               if random_weight <= current_weight:
                   return instance

           return self.service_instances[0]

Authentication and Security
---------------------------

API Key Authentication
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class AuthenticatedAPITool:
       def __init__(self, tool_config=None):
           self.tool_config = tool_config or {}
           self.api_key = self.tool_config.get("settings", {}).get("api_key")
           self.auth_header = self.tool_config.get("settings", {}).get("auth_header", "Authorization")
           self.auth_type = self.tool_config.get("settings", {}).get("auth_type", "Bearer")

       def _get_headers(self, additional_headers=None):
           headers = additional_headers or {}
           if self.api_key:
               headers[self.auth_header] = f"{self.auth_type} {self.api_key}"
           return headers

OAuth 2.0 Integration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class OAuthAPITool:
       def __init__(self, tool_config=None):
           self.tool_config = tool_config or {}
           self.client_id = self.tool_config.get("settings", {}).get("client_id")
           self.client_secret = self.tool_config.get("settings", {}).get("client_secret")
           self.token_url = self.tool_config.get("settings", {}).get("token_url")
           self.access_token = None
           self.token_expires_at = None

       def _get_access_token(self):
           if self.access_token and self.token_expires_at and time.time() < self.token_expires_at:
               return self.access_token

           # Request new token
           response = requests.post(self.token_url, data={
               "grant_type": "client_credentials",
               "client_id": self.client_id,
               "client_secret": self.client_secret
           })

           response.raise_for_status()
           token_data = response.json()

           self.access_token = token_data["access_token"]
           self.token_expires_at = time.time() + token_data.get("expires_in", 3600)

           return self.access_token

Testing Remote Tools
--------------------

Unit Testing
~~~~~~~~~~~~

Test remote tools with mocked responses:

.. code-block:: python

   import pytest
   from unittest.mock import patch, Mock

   class TestRemoteAPITool:
       @patch('requests.get')
       def test_successful_request(self, mock_get):
           mock_response = Mock()
           mock_response.json.return_value = {"result": "success"}
           mock_response.raise_for_status.return_value = None
           mock_get.return_value = mock_response

           tool = RESTAPITool()
           result = tool.run({"url": "https://api.example.com/test"})

           assert result["success"] is True
           assert result["data"]["result"] == "success"

       @patch('requests.get')
       def test_request_failure(self, mock_get):
           mock_get.side_effect = requests.RequestException("Connection error")

           tool = RESTAPITool()
           result = tool.run({"url": "https://api.example.com/test"})

           assert result["success"] is False
           assert "error" in result

Integration Testing
~~~~~~~~~~~~~~~~~~~

Test with actual remote services:

.. code-block:: python

   def test_weather_api_integration():
       tool = WeatherAPITool()
       result = tool.run({"city": "London"})

       assert result["success"] is True
       assert "temperature" in result
       assert "city" in result

Performance Testing
~~~~~~~~~~~~~~~~~~~

Test performance and reliability:

.. code-block:: python

   import time

   def test_performance():
       tool = RESTAPITool()

       start_time = time.time()
       results = []

       for i in range(10):
           result = tool.run({"url": f"https://api.example.com/test/{i}"})
           results.append(result)

       end_time = time.time()
       duration = end_time - start_time

       assert duration < 10  # Should complete within 10 seconds
       assert all(r["success"] for r in results)

Best Practices
--------------

Error Handling
~~~~~~~~~~~~~~

Implement comprehensive error handling:

.. code-block:: python

   def run(self, arguments):
       try:
           # Validate inputs
           self._validate_inputs(arguments)

           # Make request
           result = self._make_request(arguments)

           return {"data": result, "success": True}

       except ValidationError as e:
           return {"error": f"Validation error: {str(e)}", "success": False}
       except requests.Timeout as e:
           return {"error": f"Request timeout: {str(e)}", "success": False}
       except requests.ConnectionError as e:
           return {"error": f"Connection error: {str(e)}", "success": False}
       except requests.HTTPError as e:
           return {"error": f"HTTP error {e.response.status_code}: {str(e)}", "success": False}
       except Exception as e:
           return {"error": f"Unexpected error: {str(e)}", "success": False}

Monitoring and Logging
~~~~~~~~~~~~~~~~~~~~~~~

Add comprehensive logging:

.. code-block:: python

   import logging

   class MonitoredRemoteTool:
       def __init__(self, tool_config=None):
           self.logger = logging.getLogger(__name__)
           self.tool_config = tool_config

       def run(self, arguments):
           self.logger.info(f"Starting remote tool execution with args: {arguments}")

           start_time = time.time()
           try:
               result = self._execute(arguments)
               duration = time.time() - start_time

               self.logger.info(f"Tool completed successfully in {duration:.2f}s")
               return result

           except Exception as e:
               duration = time.time() - start_time
               self.logger.error(f"Tool failed after {duration:.2f}s: {str(e)}")
               raise

Configuration Management
~~~~~~~~~~~~~~~~~~~~~~~~

Use environment variables and configuration files:

.. code-block:: python

   import os
   from typing import Dict, Any

   class ConfigurableRemoteTool:
       def __init__(self, tool_config=None):
           self.tool_config = tool_config or {}
           self.settings = self._load_settings()

       def _load_settings(self) -> Dict[str, Any]:
           settings = {}

           # Load from tool config
           settings.update(self.tool_config.get("settings", {}))

           # Load from environment variables
           for key, value in settings.items():
               if isinstance(value, str) and value.startswith("env:"):
                   env_var = value[4:]  # Remove "env:" prefix
                   settings[key] = os.getenv(env_var)

           return settings

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Problem
     - Solution
   * - Connection timeout
     - Increase timeout setting, check network connectivity
   * - Authentication failed
     - Verify API keys and authentication headers
   * - Service unavailable
     - Implement retry logic and circuit breaker
   * - Rate limiting
     - Add rate limiting and exponential backoff
   * - SSL certificate errors
     - Update certificates or disable SSL verification for testing

Debugging Tools
~~~~~~~~~~~~~~~

Enable detailed logging:

.. code-block:: python

   import logging
   logging.basicConfig(level=logging.DEBUG)

   # Enable requests logging
   import urllib3
   urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

   # Test connectivity
   import requests
   response = requests.get("https://api.example.com/health", timeout=10)
   print(f"Status: {response.status_code}")

Next Steps
----------

Now that you can integrate remote tools:

* 🏠 **Local Tools**: :doc:`local_tool_registration` - Learn about local tool development
* 📤 **Contributing**: :doc:`contributing_tools` - Submit your tools to ToolUniverse
* 🔧 **Advanced Patterns**: :doc:`../advanced/custom_tools` - Advanced development patterns
* 🤖 **AI Integration**: :doc:`../guide/building_ai_scientists/mcp_integration` - Connect with AI assistants

.. tip::
   **Integration tip**: Start with simple REST API wrappers, then move to MCP for more complex integrations. Always implement proper error handling and monitoring!
