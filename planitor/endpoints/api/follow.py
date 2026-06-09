from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from planitor import crud
from planitor.database import get_async_db
from planitor.models import Address, Case, Entity, User
from planitor.security import get_current_active_user

from . import router


@router.post("/follow/cases/{case_id}")
async def follow_case(
    case_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    case = await db.get(Case, case_id)
    if case is None:
        raise HTTPException(404)
    await crud.acreate_case_subscription(db, current_user, case)
    return {}


@router.delete("/follow/cases/{case_id}")
async def unfollow_case(
    case_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    case = await db.get(Case, case_id)
    if case is None:
        raise HTTPException(404)
    await crud.adelete_case_subscription(db, current_user, case)
    return {}


@router.post("/follow/entities/{kennitala}")
async def follow_entity(
    kennitala: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    entity = await db.get(Entity, kennitala)
    if entity is None:
        raise HTTPException(404)
    await crud.acreate_entity_subscription(db, current_user, entity)
    return {}


@router.delete("/follow/entities/{kennitala}")
async def unfollow_entity(
    kennitala: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    entity = await db.get(Entity, kennitala)
    if entity is None:
        raise HTTPException(404)
    await crud.adelete_entity_subscription(db, current_user, entity)
    return {}


@router.post("/follow/addresses/{hnitnum}")
async def follow_address(
    hnitnum: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    address = await db.get(Address, hnitnum)
    if address is None:
        address = crud.get_and_init_address(hnitnum)
        if address is None:
            raise HTTPException(404)
        db.add(address)
        await db.commit()
        await db.refresh(address)
    await crud.acreate_address_subscription(db, current_user, address)
    return {}


@router.delete("/follow/addresses/{hnitnum}")
async def unfollow_address(
    hnitnum: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    address = await db.get(Address, hnitnum)
    if address is None:
        raise HTTPException(404)
    await crud.adelete_address_subscription(db, current_user, address)
    return {}
