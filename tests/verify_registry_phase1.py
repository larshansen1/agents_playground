"""Test script to verify Agent Registry Phase 1 implementation.

This script runs the "Definition of Done" code from the requirements
to verify that the registry works as expected.
"""

from app.agents.assessment_agent import AssessmentAgent
from app.agents.registry import AgentRegistry
from app.agents.research_agent import ResearchAgent

# Create registry
registry = AgentRegistry()

# Register agents
registry.register(
    "research",
    ResearchAgent,
    config={"model": "gpt-4-turbo", "temperature": 0.7},
    tools=["web_search"],
    description="Gathers information from web sources",
)

registry.register(
    "assessment",
    AssessmentAgent,
    config={"model": "gpt-4-turbo", "temperature": 0.3},
    tools=["fact_checker"],
    description="Assesses research quality",
)

# List all
print("Registered agents:", registry.list_all())  # ['research', 'assessment']
assert len(registry.list_all()) == 2

# Get singleton
agent1 = registry.get("research")
agent2 = registry.get("research")
assert agent1 is agent2  # Same instance
print("✓ Singleton pattern verified")

# Create new
agent3 = registry.create_new("research", temperature=0.9)
assert agent3 is not agent1  # Different instance
print("✓ Fresh instance creation verified")

# Get metadata
metadata = registry.get_metadata("research")
assert "web_search" in metadata.tools
assert metadata.description == "Gathers information from web sources"
print("✓ Metadata retrieval verified")

print("\n✅ Phase 1 Complete!")
print(f"   - {len(registry.list_all())} agents registered")
print("   - Singleton pattern working")
print("   - Fresh instance creation working")
print("   - Metadata retrieval working")
