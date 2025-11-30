from dotenv import load_dotenv

# Load the .env file before importing registry
load_dotenv()

from app.tools.registry_init import tool_registry  # noqa: E402

# Get the tool
search = tool_registry.get("web_search")
# Execute a real search
result = search.execute(query="latest python features")
# Print results
if result["success"]:
    for item in result["result"]["results"]:
        print(f"- {item['title']}: {item['url']}")
else:
    print(f"Error: {result['error']}")
