#!/usr/bin/env python3
"""Verification script for Tool Registry implementation."""

import sys

print("=" * 60)
print("Tool Registry Verification")
print("=" * 60)

# Test 1: Import tool registry
print("\n1. Testing tool registry import...")
try:
    from app.tools.registry_init import tool_registry

    print("   ✅ Tool registry imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import: {e}")
    sys.exit(1)

# Test 2: List available tools
print("\n2. Listing available tools...")
try:
    tools = tool_registry.list_all()
    print(f"   ✅ Available tools: {tools}")
except Exception as e:
    print(f"   ❌ Failed to list tools: {e}")
    sys.exit(1)

# Test 3: Get calculator tool
print("\n3. Getting calculator tool...")
try:
    calc_tool = tool_registry.get("calculator")
    print(f"   ✅ Got calculator: {calc_tool.tool_name}")
except Exception as e:
    print(f"   ❌ Failed to get calculator: {e}")
    sys.exit(1)

# Test 4: Execute calculator
print("\n4. Executing calculator (2 + 2 * 3)...")
try:
    result = calc_tool.execute(expression="2 + 2 * 3")
    if result["success"] and result["result"] == 8:
        print(f"   ✅ Calculation successful: {result['result']}")
    else:
        print(f"   ❌ Unexpected result: {result}")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ Failed to execute: {e}")
    sys.exit(1)

# Test 5: Get web search tool
print("\n5. Getting web search tool...")
try:
    search_tool = tool_registry.get("web_search")
    print(f"   ✅ Got web search: {search_tool.tool_name}")
except Exception as e:
    print(f"   ❌ Failed to get web search: {e}")
    sys.exit(1)

# Test 6: Test web search (without API key)
print("\n6. Testing web search error handling...")
try:
    result = search_tool.execute(query="Python tutorials")
    # Expected to fail without API key
    if not result["success"] and "BRAVE_API_KEY" in result["error"]:
        print("   ✅ Web search error handling works correctly")
    else:
        print(f"   ⚠️  Unexpected result (API key may be set): {result}")
except Exception as e:
    print(f"   ❌ Failed unexpectedly: {e}")
    sys.exit(1)

# Test 7: Test agent integration
print("\n7. Testing agent-tool integration...")
try:
    from app.agents.base import Agent

    class TestAgent(Agent):
        def __init__(self):
            super().__init__(agent_type="test", tools=["calculator"])

        def execute(self, _input_data, _user_id_hash=None):
            # Use calculator tool
            result = self._execute_tool("calculator", expression="5 * 5")
            return {
                "output": {"calculation": result},
                "usage": {
                    "model_used": "none",
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_cost": 0.0,
                    "generation_id": "test",
                },
            }

    agent = TestAgent()
    output = agent.execute({})
    calc_result = output["output"]["calculation"]

    if calc_result["success"] and calc_result["result"] == 25:
        print("   ✅ Agent can use tools successfully")
    else:
        print(f"   ❌ Unexpected agent result: {output}")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ Failed agent integration: {e}")
    sys.exit(1)

# Test 8: Get tool schema
print("\n8. Testing tool schema retrieval...")
try:
    schema = tool_registry.get_schema("calculator")
    if "properties" in schema and "expression" in schema["properties"]:
        print("   ✅ Tool schema retrieved successfully")
    else:
        print(f"   ❌ Invalid schema: {schema}")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ Failed to get schema: {e}")
    sys.exit(1)

# Test 9: Create fresh instance
print("\n9. Testing fresh instance creation...")
try:
    new_calc = tool_registry.create_new("calculator")
    old_calc = tool_registry.get("calculator")

    if new_calc is not old_calc:
        print("   ✅ Fresh instances work correctly")
    else:
        print("   ❌ Fresh instances are the same as singleton")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ Failed to create fresh instance: {e}")
    sys.exit(1)

# Test 10: Test parameter validation
print("\n10. Testing parameter validation...")
try:
    calc = tool_registry.get("calculator")
    try:
        # This should fail - missing required parameter
        calc.execute()
        print("   ❌ Validation should have failed")
        sys.exit(1)
    except ValueError as ve:
        if "expression" in str(ve).lower():
            print("   ✅ Parameter validation works correctly")
        else:
            print(f"   ❌ Unexpected validation error: {ve}")
            sys.exit(1)
except Exception as e:
    print(f"   ❌  Failed validation test: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ ALL VERIFICATION TESTS PASSED!")
print("=" * 60)
print("\n Tool Registry Implementation Complete! 🎉\n")
