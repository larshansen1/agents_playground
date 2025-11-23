from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Task

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
