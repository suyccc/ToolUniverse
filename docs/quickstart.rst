Quick Start
=================

**Build your first AI scientist in 5 minutes with ToolUniverse's 600+ scientific tools**

This Tutorial gets you from zero to your first successful query in 5 minutes. For detailed tutorials, see :doc:`getting_started`.

🚀 Quick Start
--------------

**Get your first ToolUniverse running in 2 minutes:**

.. code-block:: python

   # 1. Install ToolUniverse
   pip install tooluniverse

   # 2. Create AI scientist environment
   from tooluniverse import ToolUniverse

   tu = ToolUniverse()
   tu.load_tools()  # Load all 600+ tools

   # 3. Query scientific databases
   result = tu.run({
       "name": "OpenTargets_get_associated_targets_by_disease_efoId",
       "arguments": {"efoId": "EFO_0000537"}  # hypertension
   })

**Success!** You now have access to 600+ scientific tools.

Building AI Scientists
-----------------------------------------------------------

**ToolUniverse + LLMs/Reasoning Models/Agents = AI Scientists**

How you want to use ToolUniverse:

.. grid:: 1 2 2 3
   :gutter: 3

   .. grid-item-card:: Python Integration
      :link: #python-integration
      :link-type: ref

      Use ToolUniverse directly in Python for custom applications

      **Best for**: Custom workflows, Jupyter notebooks

      **Tutorials**:

      - :doc:`guide/tool_caller`
      - :doc:`tutorials/finding_tools`
      - :doc:`guide/scientific_workflows`

   .. grid-item-card:: LLM Integration
      :link: #ai-assistant-integration
      :link-type: ref

      Connect ToolUniverse to Claude Desktop, ChatGPT, or other AI assistants

      **Best for**: General research, quick experiments

      **Tutorials**:

      - :doc:`guide/building_ai_scientists/claude_desktop`
      - :doc:`guide/building_ai_scientists/chatgpt_api`

   .. grid-item-card:: Agent Integration
      :link: #agent-integration
      :link-type: ref

      Connect ToolUniverse to sophisticated AI agents with tool access

      **Best for**: Complex workflows, autonomous systems

      **Tutorials**:

      - :doc:`guide/building_ai_scientists/codex_cli`
      - :doc:`guide/building_ai_scientists/gemini_cli`
      - :doc:`guide/building_ai_scientists/claude_code`
      - :doc:`guide/building_ai_scientists/qwen_code`

📖 **Complete Tutorial**: :doc:`guide/building_ai_scientists/index`


Next Steps
----------

**You're ready!** Now explore:

- :doc:`installation` - Complete installation options
- :doc:`getting_started` - Complete step-by-step tutorial
- :doc:`guide/index` - Comprehensive user tutorial

**🎉 Welcome to ToolUniverse!**
