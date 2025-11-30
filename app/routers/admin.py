from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

import app.workflow_init  # noqa: F401
from app.agents.registry_init import registry as agent_registry
from app.database import get_db
from app.logging_config import get_logger
from app.models import Task
from app.schemas import (
    AgentInfo,
    AgentListResponse,
    ToolInfo,
    ToolListResponse,
    WorkflowInfo,
    WorkflowListResponse,
    WorkflowStepInfo,
)
from app.tools.registry_init import tool_registry
from app.tracing import get_tracer
from app.workflow_registry import workflow_registry

logger = get_logger(__name__)
tracer = get_tracer(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={404: {"description": "Not found"}},
)


@router.get("/usage/{user_id_hash}")
async def get_user_usage(user_id_hash: str, db: Session = Depends(get_db)):  # noqa: B008
    """
    Get aggregated usage and cost for a specific user.
    """
    # Aggregate stats
    stats_query = select(
        func.count(Task.id).label("total_tasks"),
        func.sum(Task.total_cost).label("total_cost"),
        func.sum(Task.input_tokens).label("total_input_tokens"),
        func.sum(Task.output_tokens).label("total_output_tokens"),
    ).where(Task.user_id_hash == user_id_hash)

    result = db.execute(stats_query).first()

    if not result:
        return {
            "user_id_hash": user_id_hash,
            "total_tasks": 0,
            "total_cost": 0.0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "recent_tasks": [],
        }

    # Get recent tasks
    recent_tasks_query = (
        select(Task)
        .where(Task.user_id_hash == user_id_hash)
        .order_by(Task.created_at.desc())
        .limit(10)
    )
    recent_tasks = db.execute(recent_tasks_query).scalars().all()

    return {
        "user_id_hash": user_id_hash,
        "total_tasks": result.total_tasks or 0,
        "total_cost": float(result.total_cost or 0),
        "total_input_tokens": result.total_input_tokens or 0,
        "total_output_tokens": result.total_output_tokens or 0,
        "recent_tasks": [
            {
                "id": t.id,
                "type": t.type,
                "status": t.status,
                "created_at": t.created_at,
                "cost": float(t.total_cost or 0),
            }
            for t in recent_tasks
        ],
    }


@router.get("/agents", response_model=AgentListResponse)
async def list_agents():
    """List all registered agents."""
    with tracer.start_as_current_span(
        "admin.list_agents",
        attributes={
            "http.method": "GET",
            "http.route": "/admin/agents",
        },
    ) as span:
        agents = []
        for agent_type in agent_registry.list_all():
            metadata = agent_registry.get_metadata(agent_type)
            agents.append(
                AgentInfo(
                    name=agent_type,
                    description=metadata.description,
                    config=metadata.config,
                    tools=metadata.tools,
                )
            )

        span.set_attribute("agent.count", len(agents))
        logger.info(
            "registry.api.agents.list",
            agent_count=len(agents),
        )
        return AgentListResponse(agents=agents)


@router.get("/tools", response_model=ToolListResponse)
async def list_tools():
    """List all registered tools."""
    with tracer.start_as_current_span(
        "admin.list_tools",
        attributes={
            "http.method": "GET",
            "http.route": "/admin/tools",
        },
    ) as span:
        tools = []
        for tool_name in tool_registry.list_all():
            metadata = tool_registry.get_metadata(tool_name)
            schema = tool_registry.get_schema(tool_name)
            tools.append(
                ToolInfo(
                    name=tool_name,
                    description=metadata.description,
                    schema=schema,
                )
            )

        span.set_attribute("tool.count", len(tools))
        logger.info(
            "registry.api.tools.list",
            tool_count=len(tools),
        )
        return ToolListResponse(tools=tools)


@router.get("/workflows", response_model=WorkflowListResponse)
async def list_workflows():
    """List all registered workflows."""
    with tracer.start_as_current_span(
        "admin.list_workflows",
        attributes={
            "http.method": "GET",
            "http.route": "/admin/workflows",
        },
    ) as span:
        workflows = []
        for workflow_name in workflow_registry.list_all():
            workflow = workflow_registry.get(workflow_name)
            steps = [
                WorkflowStepInfo(
                    name=step.name or step.agent_type,
                    agent_type=step.agent_type,
                    description=None,
                    tools=None,
                )
                for step in workflow.steps
            ]
            workflows.append(
                WorkflowInfo(
                    name=workflow.name,
                    description=workflow.description,
                    strategy=workflow.coordination_type,
                    max_iterations=workflow.max_iterations,
                    steps=steps,
                )
            )
        span.set_attribute("workflow.count", len(workflows))
        logger.info(
            "registry.api.workflows.list",
            workflow_count=len(workflows),
        )
        return WorkflowListResponse(workflows=workflows)
