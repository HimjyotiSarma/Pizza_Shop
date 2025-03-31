from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from fastapi import status, HTTPException


from src.db.models import Item, Item_Category, Category
from .schema import ItemSchema, CategorySchema, ItemUpdateSchema
from src.auth.utils import convert_str


class ItemService:
    async def get_all_items(self, session: AsyncSession):
        try:
            statement = select(Item)
            result = (await session.exec(statement)).all()
            converted_result = [convert_str(item.model_dump()) for item in result]
            return converted_result
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error finding Items -> {str(e)}",
            )

    async def create_new_item(
        self, item_details: ItemSchema, item_image: str, session: AsyncSession
    ):
        try:
            item_details_dict = item_details.model_dump()
            category_name = item_details_dict.pop("category")
            if not item_image:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Item Image not provided. Or Error while processing image path",
                )
            category_info = await self.get_category_details(category_name, session)
            if category_info is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"The Category {str(category_name)} doesnot exist in the database. You need to add the Category first before proceeding",
                )
            # Add the New Category and the Item Category Entry
            new_item = Item(**item_details_dict, image=item_image)
            session.add(new_item)
            await session.flush()
            # Create Item Category Link
            new_item_category = Item_Category(
                item_id=new_item.uid, category_id=category_info.uid
            )
            session.add(new_item_category)
            await session.commit()
            await session.refresh(new_item)
            return new_item

        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating New Item: {str(e)}",
            )

    async def get_item(self, item_id: str, session: AsyncSession):
        try:
            statement = select(Item).where(Item.uid == item_id)
            result = await session.exec(statement)
            item_info = result.first()
            return item_info
        except Exception as e:
            raise Exception(f"Error getting Item Info -> {str(e)}")

    async def is_category_exist(self, category_name: str, session: AsyncSession):
        category_info = await self.get_category_details(category_name, session)
        print("Category Info: ", category_info)
        return category_info is not None

    async def get_category_details(self, category_name: str, session: AsyncSession):
        try:
            statement = select(Category).where(Category.name == category_name)
            result = await session.exec(statement)
            category_info = result.first()
            return category_info
        except Exception as e:
            raise Exception(f"Error getting category details: {str(e)}")

    async def create_new_category(
        self,
        category_info: CategorySchema,
        category_image_url: str,
        session: AsyncSession,
    ):
        try:
            category_info_dict = category_info.model_dump()
            is_Category_available = await self.is_category_exist(
                category_info.name, session
            )
            print("Category Availability: ", is_Category_available)
            if is_Category_available:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Category {str(category_info.name)} already exist in the database.",
                )

            new_category = Category(**category_info_dict, image=category_image_url)
            session.add(new_category)
            await session.commit()
            await session.refresh(new_category)
            return new_category
        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error Creating New Category : {str(e)}",
            )

    async def update_Item(self, item: Item, updated_item: dict, session: AsyncSession):
        try:
            for key, value in updated_item.items():
                if hasattr(item, key):
                    setattr(item, key, value)
                else:
                    ValueError(f"Invalid Key Attribute : {str(key)}")

            await session.commit()
            await session.refresh(item)
            return item

        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error Updating Item: {str(e)}",
            )

    async def update_Category(
        self, category: Category, updated_category: dict, session: AsyncSession
    ):
        try:
            for key, value in updated_category.items():
                if hasattr(category, key):
                    setattr(category, key, value)
                else:
                    ValueError(f"Invalid Key Attribute : {str(key)}")

            await session.commit()
            await session.refresh(category)
            return category

        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error Updating Category: {str(e)}",
            )

    async def delete_Item(self, item_id: str, session: AsyncSession):
        try:
            statement = select(Item).where(Item.uid == item_id)
            result = await session.exec(statement)
            item = result.one()
            await session.delete(item)
            await session.commit()
            return True
        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error on deleting Item: {str(e)}",
            )

    async def delete_Category(self, category_name: str, session: AsyncSession):
        try:
            statement = select(Category).where(Category.name == category_name)
            result = await session.exec(statement)
            category = result.one()
            await session.delete(category)
            await session.commit()
            return True
        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error on deleting Category: {str(e)}",
            )
