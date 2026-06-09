from typing import List

from fastapi import Depends, Request, Response
from fastapi.exceptions import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from planitor import models
from planitor.crud import monitor as crud
from planitor.database import get_async_db
from planitor.models.city import CouncilTypeEnum
from planitor.schemas.monitor import (
    Subscription,
    SubscriptionForm,
)
from planitor.security import get_current_active_user

from . import router


@router.get("/subscriptions", response_model=List[Subscription])
async def get_subscriptions(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    result = await db.scalars(
        select(models.Subscription)
        .options(
            selectinload(models.Subscription.entity),
            selectinload(models.Subscription.address).selectinload(
                models.Address.municipality
            ),
            selectinload(models.Subscription.case).selectinload(
                models.Case.municipality
            ),
        )
        .where(models.Subscription.user_id == current_user.id)
        .order_by(models.Subscription.created)
    )
    subscriptions = result.all()
    return subscriptions


@router.post("/subscriptions", response_model=Subscription)
def create_subscription():
    return None


def set_subscription_council_types(
    subscription: models.Subscription,
    council_types: List[CouncilTypeEnum],
) -> None:
    """If all councils selected, whether within municipality or the available council
    types, turn field into None, which is the default state. If no councils selected,
    deactivate subscription, but let `councils` field keep the presumable last remaining
    council type, so that when reactivated, that is the selected council."""

    if council_types == []:
        subscription.active = False
        return

    # Turn form into dict with named keys, for easier access
    _types = {c.name for c in council_types}

    municipality = subscription.get_municipality()

    if municipality:
        _municipality_councils = {c.council_type.name for c in municipality.councils}
        all_selected = _municipality_councils.issubset(_types)
        if all_selected:
            subscription.council_types = None
            return

    subscription.council_types = [getattr(CouncilTypeEnum, key) for key in _types]
    if set(subscription.council_types) == set(CouncilTypeEnum):
        subscription.council_types = None


@router.post("/subscriptions/{id}", response_model=Subscription)
async def update_subscription(
    id: int,
    request: Request,
    form: SubscriptionForm,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    subscription = await db.scalar(
        select(models.Subscription)
        .options(
            selectinload(models.Subscription.address)
            .selectinload(models.Address.municipality)
            .selectinload(models.Municipality.councils),
            selectinload(models.Subscription.case)
            .selectinload(models.Case.municipality)
            .selectinload(models.Municipality.councils),
            selectinload(models.Subscription.entity),
        )
        .where(models.Subscription.id == id)
    )
    if subscription is None or subscription.user_id != current_user.id:
        raise HTTPException(404)
    if form.active is not None:
        subscription.active = form.active
    if form.immediate is not None:
        subscription.immediate = form.immediate
    if form.radius is not None:
        subscription.radius = form.radius
    if form.council_types is not None:
        set_subscription_council_types(subscription, form.council_types)
    db.add(subscription)
    await db.commit()
    return subscription


@router.delete("/subscriptions/{id}")
async def delete_subscription(
    id: int,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    subscription = await db.scalar(
        select(models.Subscription).where(models.Subscription.id == id)
    )
    if subscription is None or subscription.user_id != current_user.id:
        raise HTTPException(404)
    await crud.adelete_subscription(db, subscription)
    return Response(None, 204)
