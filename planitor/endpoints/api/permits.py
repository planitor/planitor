from typing import List

from fastapi import Depends, Request, Response
from fastapi.exceptions import HTTPException
from sqlakeyset.paging import select_page
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from planitor import models
from planitor.database import get_async_db
from planitor.models.enums import BuildingTypeEnum, PermitTypeEnum
from planitor.schemas.permits import (
    Permit,
    PermitForm,
    ApiResponsePermit,
    ApiLoadPermit,
)
from planitor.permits import PermitMinute
from planitor.security import get_current_active_superuser

from . import router


PERMIT_LOAD_OPTIONS = (
    selectinload(models.Permit.minute).selectinload(models.Minute.meeting),
    selectinload(models.Permit.minute)
    .selectinload(models.Minute.case)
    .selectinload(models.Case.municipality),
    selectinload(models.Permit.minute)
    .selectinload(models.Minute.case)
    .selectinload(models.Case.iceaddr),
)

MINUTE_PERMIT_LOAD_OPTIONS = (
    selectinload(models.Minute.permit),
    selectinload(models.Minute.meeting),
    selectinload(models.Minute.case).selectinload(models.Case.municipality),
    selectinload(models.Minute.case).selectinload(models.Case.iceaddr),
)


@router.get("/permits", response_model=List[ApiResponsePermit])
async def get_permits(
    request: Request,
    response: Response,
    cursor: str = None,
    db: AsyncSession = Depends(get_async_db),
):
    query = (
        select(models.Permit)
        .options(*PERMIT_LOAD_OPTIONS)
        .join(models.Minute)
        .join(models.Meeting)
        .join(models.Case)
        .join(models.Municipality)
        .order_by(models.Meeting.start.desc(), models.Minute.id)
    )
    page = await db.run_sync(
        lambda sync_db: select_page(sync_db, query, per_page=100, page=cursor)
    )
    url = request.url_for("get_permits")
    response.headers["Link"] = (
        f'<{url}?cursor={page.paging.bookmark_next}>; rel: "next"'
    )
    permits = [ApiLoadPermit(request, row[0]) for row in page]
    return permits


@router.get("/minutes/{minute_id}/permit", response_model=Permit)
async def get_permit(
    request: Request,
    minute_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_superuser),
):
    minute = await db.scalar(
        select(models.Minute)
        .options(*MINUTE_PERMIT_LOAD_OPTIONS)
        .where(models.Minute.id == minute_id)
    )
    if minute is None:
        raise HTTPException(404)
    permit = minute.permit
    if permit is None:
        permit = PermitMinute(minute)
    return permit


@router.put("/minutes/{minute_id}/permit", response_model=Permit)
async def update_permit(
    request: Request,
    minute_id: int,
    form: PermitForm,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_superuser),
):
    minute = await db.scalar(
        select(models.Minute)
        .options(*MINUTE_PERMIT_LOAD_OPTIONS)
        .where(models.Minute.id == minute_id)
    )
    if minute is None:
        raise HTTPException(404)
    permit = minute.permit
    if permit is None:
        permit = models.Permit(minute=minute)

    permit.units = form.units
    permit.area_added = form.area_added
    permit.area_subtracted = form.area_subtracted

    permit.building_type = None
    permit.permit_type = None
    if form.building_type:
        permit.building_type = getattr(BuildingTypeEnum, form.building_type)
    if form.permit_type:
        permit.permit_type = getattr(PermitTypeEnum, form.permit_type)

    db.add(permit)
    await db.commit()
    await db.refresh(permit)
    return permit
