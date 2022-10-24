from typing import Optional, Sequence

from neomodel import db  # type: ignore

from clinical_mdr_api import exceptions, models
from clinical_mdr_api.domain.brand.brand import BrandAR
from clinical_mdr_api.models import BrandCreateInput
from clinical_mdr_api.services._meta_repository import MetaRepository  # type: ignore


class BrandService:
    def __init__(self, user_id: Optional[str] = None):
        self.user_id = user_id if user_id is not None else "-Unknown-"
        self.repos = MetaRepository()

    def get_all_brands(self) -> Sequence[models.Brand]:
        try:
            all_brands = self.repos.brand_repository.find_all()
            self.repos.brand_repository.close()
            return [models.Brand.from_brand_ar(brand_ar) for brand_ar in all_brands]
        finally:
            self.repos.close()

    def get_brand(self, uid: str) -> models.Brand:
        repos = MetaRepository()
        try:
            brand = models.Brand.from_uid(uid, repos.brand_repository.find_by_uid)
            if brand is None:
                raise exceptions.NotFoundException(
                    f"Brand with the specified uid '{uid}' could not be found.",
                )
            return brand
        finally:
            self.repos.close()

    @db.transaction
    def create(self, brand_create_input: BrandCreateInput) -> models.Brand:
        try:
            try:
                brand_ar = BrandAR.from_input_values(
                    name=brand_create_input.name,
                    generate_uid_callback=self.repos.brand_repository.generate_uid,
                )
            except ValueError as value_error:
                raise exceptions.ValidationException(value_error.args[0])

            # Try to retrieve brand with the same name, and return it if found
            existing_brand = self.repos.brand_repository.find_by_brand_name(
                brand_create_input.name
            )
            if existing_brand:
                return models.Brand.from_brand_ar(existing_brand)

            self.repos.brand_repository.save(brand_ar)
            return models.Brand.from_uid(
                brand_ar.uid, self.repos.brand_repository.find_by_uid
            )
        finally:
            self.repos.close()

    @db.transaction
    def delete(self, uid: str):
        self.repos.brand_repository.delete(uid)
