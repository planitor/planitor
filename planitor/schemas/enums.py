from typing import List, Tuple, TypeVar
from pydantic import BaseModel

from planitor.models.enums import BuildingTypeEnum, CouncilTypeEnum, PermitTypeEnum, SubscriptionTypeEnum

K = TypeVar('K')


EnumChoiceType = List[Tuple[K, str]]

class EnumListResponse(BaseModel):
    council_types: EnumChoiceType[CouncilTypeEnum]
    building_types: EnumChoiceType[BuildingTypeEnum]
    permit_types: EnumChoiceType[PermitTypeEnum]
    subscription_types: EnumChoiceType[SubscriptionTypeEnum]
