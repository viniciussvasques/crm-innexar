from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.goal import Goal, GoalType, GoalPeriod, GoalStatus, GoalCategory
from app.api.dependencies import get_current_user, get_user_role_str
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta

router = APIRouter(prefix="/goals", tags=["goals"])

class GoalCreate(BaseModel):
    title: str
    description: Optional[str] = None
    goal_type: GoalType = GoalType.INDIVIDUAL
    category: GoalCategory = GoalCategory.REVENUE
    period: GoalPeriod = GoalPeriod.MONTHLY
    target_value: float
    unit: str = "BRL"
    assignee_id: Optional[int] = None
    start_date: datetime
    end_date: datetime
    reward_description: Optional[str] = None
    penalty_description: Optional[str] = None

class GoalResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    goal_type: GoalType
    category: GoalCategory
    period: GoalPeriod
    target_value: float
    current_value: float
    unit: str
    assignee_id: Optional[int]
    assignee_name: Optional[str]
    creator_name: str
    start_date: datetime
    end_date: datetime
    completed_at: Optional[datetime]
    status: GoalStatus
    progress_percentage: float
    reward_description: Optional[str]
    penalty_description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    target_value: Optional[float] = None
    status: Optional[GoalStatus] = None
    reward_description: Optional[str] = None
    penalty_description: Optional[str] = None

@router.post("/", response_model=GoalResponse, status_code=201)
async def create_goal(
    goal_data: GoalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cria nova meta - apenas admin pode criar metas para outros"""
    if get_user_role_str(current_user) != "admin":
        # Usuários não-admin só podem criar metas para si mesmos
        if goal_data.assignee_id and goal_data.assignee_id != current_user.id:
            raise HTTPException(status_code=403, detail="Não autorizado a criar metas para outros usuários")
        goal_data.assignee_id = current_user.id

    # Valida se o assignee existe
    if goal_data.assignee_id:
        result = await db.execute(select(User).where(User.id == goal_data.assignee_id))
        assignee = result.scalar_one_or_none()
        if not assignee:
            raise HTTPException(status_code=404, detail="Usuário destinatário não encontrado")

    goal = Goal(
        title=goal_data.title,
        description=goal_data.description,
        goal_type=goal_data.goal_type,
        category=goal_data.category,
        period=goal_data.period,
        target_value=goal_data.target_value,
        unit=goal_data.unit,
        assignee_id=goal_data.assignee_id,
        creator_id=current_user.id,
        start_date=goal_data.start_date,
        end_date=goal_data.end_date,
        reward_description=goal_data.reward_description,
        penalty_description=goal_data.penalty_description
    )

    db.add(goal)
    await db.commit()
    await db.refresh(goal)

    return await _format_goal_response(goal, db)

@router.get("/", response_model=List[GoalResponse])
async def list_goals(
    goal_type: Optional[GoalType] = None,
    status: Optional[GoalStatus] = None,
    assignee_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista metas com filtros"""
    query = select(Goal)

    # Filtros
    if goal_type:
        query = query.where(Goal.goal_type == goal_type)

    if status:
        query = query.where(Goal.status == status)

    # Usuários não-admin só veem suas próprias metas ou metas públicas da equipe
    if get_user_role_str(current_user) != "admin":
        query = query.where(
            or_(
                Goal.assignee_id == current_user.id,
                and_(
                    Goal.goal_type.in_([GoalType.TEAM, GoalType.DEPARTMENT]),
                    Goal.creator_id == current_user.id
                )
            )
        )
    elif assignee_id:
        query = query.where(Goal.assignee_id == assignee_id)

    query = query.order_by(desc(Goal.created_at))

    result = await db.execute(query)
    goals = result.scalars().all()

    return [await _format_goal_response(goal, db) for goal in goals]

@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(
    goal_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Busca meta específica"""
    result = await db.execute(select(Goal).where(Goal.id == goal_id))
    goal = result.scalar_one_or_none()

    if not goal:
        raise HTTPException(status_code=404, detail="Meta não encontrada")

    # Verifica permissões
    user_role = get_user_role_str(current_user)
    if user_role != "admin" and goal.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso negado")

    return await _format_goal_response(goal, db)

@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: int,
    goal_data: GoalUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Atualiza meta"""
    result = await db.execute(select(Goal).where(Goal.id == goal_id))
    goal = result.scalar_one_or_none()

    if not goal:
        raise HTTPException(status_code=404, detail="Meta não encontrada")

    # Verifica permissões
    user_role = get_user_role_str(current_user)
    if user_role != "admin" and goal.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso negado")

    # Atualiza campos
    for field, value in goal_data.dict(exclude_unset=True).items():
        if value is not None:
            setattr(goal, field, value)

    # Atualiza progresso se necessário
    if goal.status == GoalStatus.COMPLETED and not goal.completed_at:
        goal.completed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(goal)

    return await _format_goal_response(goal, db)

@router.delete("/{goal_id}")
async def delete_goal(
    goal_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Exclui meta"""
    result = await db.execute(select(Goal).where(Goal.id == goal_id))
    goal = result.scalar_one_or_none()

    if not goal:
        raise HTTPException(status_code=404, detail="Meta não encontrada")

    # Verifica permissões
    user_role = get_user_role_str(current_user)
    if user_role != "admin" and goal.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso negado")

    await db.delete(goal)
    await db.commit()

    return {"message": "Meta excluída com sucesso"}

@router.post("/{goal_id}/progress")
async def update_progress(
    goal_id: int,
    current_value: float,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Atualiza progresso da meta"""
    result = await db.execute(select(Goal).where(Goal.id == goal_id))
    goal = result.scalar_one_or_none()

    if not goal:
        raise HTTPException(status_code=404, detail="Meta não encontrada")

    # Verifica permissões
    user_role = get_user_role_str(current_user)
    if user_role != "admin" and goal.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso negado")

    goal.current_value = current_value
    goal.progress_percentage = min(100.0, (current_value / goal.target_value) * 100)

    # Verifica se a meta foi completada
    if goal.progress_percentage >= 100 and goal.status == GoalStatus.ACTIVE:
        goal.status = GoalStatus.COMPLETED
        goal.completed_at = datetime.utcnow()

    await db.commit()

    return await _format_goal_response(goal, db)

async def _format_goal_response(goal: Goal, db: AsyncSession) -> GoalResponse:
    """Formata resposta da meta com nomes dos usuários"""
    assignee_name = None
    if goal.assignee_id:
        result = await db.execute(select(User.name).where(User.id == goal.assignee_id))
        assignee_name = result.scalar_one_or_none()

    creator_name = ""
    result = await db.execute(select(User.name).where(User.id == goal.creator_id))
    creator_name_result = result.scalar_one_or_none()
    if creator_name_result:
        creator_name = creator_name_result

    return GoalResponse(
        id=goal.id,
        title=goal.title,
        description=goal.description,
        goal_type=goal.goal_type,
        category=goal.category,
        period=goal.period,
        target_value=goal.target_value,
        current_value=goal.current_value,
        unit=goal.unit,
        assignee_id=goal.assignee_id,
        assignee_name=assignee_name,
        creator_name=creator_name,
        start_date=goal.start_date,
        end_date=goal.end_date,
        completed_at=goal.completed_at,
        status=goal.status,
        progress_percentage=goal.progress_percentage,
        reward_description=goal.reward_description,
        penalty_description=goal.penalty_description,
        created_at=goal.created_at
    )
