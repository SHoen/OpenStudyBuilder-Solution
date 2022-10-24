from typing import Callable, Optional

from pydantic import Field

from clinical_mdr_api.domain.brand.brand import BrandAR
from clinical_mdr_api.models.utils import BaseModel


class Brand(BaseModel):
    uid: str = Field(
        ...,
        title="uid",
        description="The unique id of the Brand.",
    )

    name: Optional[str] = Field(
        ...,
        title="name",
        description="",
    )

    @classmethod
    def from_uid(
        cls,
        uid: str,
        find_by_uid: Callable[[str], Optional[BrandAR]],
    ) -> Optional["Brand"]:
        brand = None
        brand_ar: BrandAR = find_by_uid(uid)
        if brand_ar is not None:
            brand = Brand.from_brand_ar(brand_ar)
        return brand

    @classmethod
    def from_brand_ar(
        cls,
        brand_ar: BrandAR,
    ) -> "Brand":
        return Brand(
            uid=brand_ar.uid,
            name=brand_ar.name,
        )


class BrandCreateInput(BaseModel):

    name: Optional[str] = Field(
        ...,
        title="name",
        description="",
    )
