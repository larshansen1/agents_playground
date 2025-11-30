from app.tools.registry_init import tool_registry

# 1. Get the calculator tool
calc = tool_registry.get("calculator")
# 2. Execute a calculation
# Try different expressions: "2 + 2", "10 * 5", "2 ** 3"
result = calc.execute(expression="2 + 2 * 3")
print(f"Success: {result['success']}")
print(f"Result: {result['result']}")  # Should be 8
print(f"Error: {result['error']}")
