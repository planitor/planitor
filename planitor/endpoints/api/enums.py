from fastapi import Request

from planitor.models import enums
from planitor.schemas.enums import EnumListResponse

from . import router


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
        "subscription_types": [(choice.value, choice.label) for choice in enums.SubscriptionTypeEnum],
    }
