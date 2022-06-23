from typing import List, Tuple
from pydantic import BaseModel


EnumChoiceType = List[Tuple[str, str]]


class EnumListResponse(BaseModel):
    council_types: EnumChoiceType
    building_types: EnumChoiceType
    permit_types: EnumChoiceType
    subscription_types: EnumChoiceType
