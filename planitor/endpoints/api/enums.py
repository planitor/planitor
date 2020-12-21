from pydantic import BaseModel
from typing import List, Tuple

from fastapi import Request

from planitor.models import enums

from . import router


EnumChoiceType = List[Tuple[str, str]]


class EnumListResponse(BaseModel):
    council_types: EnumChoiceType
    building_types: EnumChoiceType
    permit_types: EnumChoiceType


@router.get("/_enums", response_model=EnumListResponse)
def get_council_types(request: Request):
    return {
        "council_types": [
            (choice.value, choice.label) for choice in enums.CouncilTypeEnum
        ],
        "building_types": [
            (choice.value, choice.label) for choice in enums.BuildingTypeEnum
        ],
        "permit_types": [(choice.value, choice.label) for choice in enums.PermitTypeEnum],
    }
