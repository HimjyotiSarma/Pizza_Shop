from fastapi import (
    APIRouter,
    dependencies,
    HTTPException,
    status,
    Depends,
    Form,
    UploadFile,
    File,
)
from fastapi.responses import JSONResponse
from typing import Optional
import tempfile
import shutil
from .service import ItemService
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.main import get_session
from src.db.models import User
from src.auth.utils import convert_str
from src.auth.dependencies import (
    AccessTokenBearer,
    get_current_user,
    RoleChecker,
    save_temp_image,
    uploadCloudinary,
)
from .schema import ItemSchema, CategorySchema, ItemUpdateSchema, CategoryUpdateSchema

item_router = APIRouter()
item_service = ItemService()

admin_checker = Depends(RoleChecker(["admin"]))
manager_user = Depends(RoleChecker(["admin", "manager"]))
admin_manager_checker = Depends(RoleChecker(["admin", "manager"]))


def parse_category_form_data(
    name: str = Form(), type_of: str = Form(), description: str = Form()
) -> CategorySchema:
    return CategorySchema(name=name, type_of=type_of, description=description)


def parse_item_form_data(
    name: str = Form(),
    description: str = Form(),
    sku: str = Form(),
    size: str = Form(),
    price_in_paise: str = Form(),
    category: str = Form(),
) -> ItemSchema:
    return ItemSchema(
        name=name,
        description=description,
        sku=sku,
        size=size,
        price=price_in_paise,
        category=category,
    )


def parse_update_item_form_data(
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    sku: Optional[str] = Form(None),
    size: Optional[str] = Form(None),
    price_in_paise: Optional[str] = Form(None),
) -> dict:
    item_data = ItemUpdateSchema(
        name=name,
        description=description,
        sku=sku,
        size=size,
        price=price_in_paise,
    ).model_dump()
    return {key: value for key, value in item_data.items() if value is not None}


def parse_update_category_form_data(
    name: Optional[str] = Form(None),
    type_of: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
) -> dict:
    category_data = CategoryUpdateSchema(
        name=name, type_of=type_of, description=description
    ).model_dump()
    return {key: value for key, value in category_data.items() if value is not None}


@item_router.post("/create", dependencies=[admin_manager_checker])
async def create_new_Item(
    item_details: ItemSchema = Depends(parse_item_form_data),
    image_path=Depends(save_temp_image),
    session: AsyncSession = Depends(get_session),
):
    try:
        cloudinary_response = await uploadCloudinary(image_path)
        if not cloudinary_response:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error while processing image. Please check the image and try again",
            )
        cloudinary_image_url = cloudinary_response.get("url")
        new_item_details = await item_service.create_new_item(
            item_details, cloudinary_image_url, session
        )

        return JSONResponse(
            content={
                "message": "New Item Added to the Menu",
                "item": convert_str(new_item_details.model_dump()),
            },
            status_code=status.HTTP_201_CREATED,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Something went wrong while creating new Item :-> {str(e)}",
        )


@item_router.post("/category/create", dependencies=[admin_manager_checker])
async def create_new_category(
    form_data: CategorySchema = Depends(parse_category_form_data),
    image_path: str = Depends(save_temp_image),
    session: AsyncSession = Depends(get_session),
):
    #  First store the image in Temp and store it in cloudinary

    try:
        cloudinary_response = await uploadCloudinary(image_path)

        if not cloudinary_response:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error while processing image. Please check the image and try again",
            )
        cloudinary_url = cloudinary_response.get("url")
        new_category = await item_service.create_new_category(
            form_data, cloudinary_url, session
        )
        return JSONResponse(
            content={
                "message": "New Category added successfully",
                "category": convert_str(new_category.model_dump()),
            },
            status_code=status.HTTP_201_CREATED,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Something went wrong while creating new category :-> {str(e)}",
        )


@item_router.patch("/update/{item_id}", dependencies=[admin_manager_checker])
async def update_item(
    item_id: str,
    updated_info_dict: dict = Depends(parse_update_item_form_data),
    image_file: UploadFile = File(None),
    session: AsyncSession = Depends(get_session),
):
    try:
        item_info = await item_service.get_item(item_id, session)
        if not item_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item info with Item ID {str(item_id)} unavailable at the database",
            )
        image_path = save_temp_image(image_file) if image_file is not None else None

        if image_path is not None:
            cloudinary_response = await uploadCloudinary(image_path)
            cloudinary_image = cloudinary_response.get("url")
            updated_info_dict["image"] = cloudinary_image
        update_item_response = await item_service.update_Item(
            item=item_info, updated_item=updated_info_dict, session=session
        )

        return JSONResponse(
            content={
                "message": f"Item updated successfully",
                "item": convert_str(update_item_response.model_dump()),
            },
            status_code=status.HTTP_202_ACCEPTED,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"Error Updating Item: {str(e)}",
        )


@item_router.patch("/category/{category_name}", dependencies=[admin_manager_checker])
async def update_category(
    category_name: str,
    update_category_dict: dict = Depends(parse_update_category_form_data),
    image_file: UploadFile = File(None),
    session: AsyncSession = Depends(get_session),
):
    try:
        print("CATEGORY NAME : ", category_name)
        category_info = await item_service.get_category_details(
            category_name=category_name, session=session
        )
        print("CATEGORY INFO DETAILS: -> ", category_info)
        if not category_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category info with Category name {str(category_name)} unavailable at the database",
            )
        image_path = save_temp_image(image_file) if image_file is not None else None
        if image_path is not None:
            cloudinary_response = await uploadCloudinary(image_path)
            cloudinary_image = cloudinary_response.get("url")
            update_category_dict["image"] = cloudinary_image
        update_category_response = await item_service.update_Category(
            category=category_info,
            updated_category=update_category_dict,
            session=session,
        )
        return JSONResponse(
            content={
                "message": f"Category updated successfully",
                "item": convert_str(update_category_response.model_dump()),
            },
            status_code=status.HTTP_202_ACCEPTED,
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error Updating Category: {str(e)}",
        )


@item_router.delete("/{item_id}", dependencies=[admin_manager_checker])
async def delete_item(item_id: str, session: AsyncSession = Depends(get_session)):
    try:
        await item_service.delete_Item(item_id, session)
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "message": "Item deleted successfully",
            },
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error Deleting Item : {str(e)}",
        )


@item_router.delete("/category/{category_name}", dependencies=[admin_manager_checker])
async def delete_item(category_name: str, session: AsyncSession = Depends(get_session)):
    try:
        await item_service.delete_Category(category_name=category_name, session=session)
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "message": "Category deleted successfully",
            },
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error Deleting Item : {str(e)}",
        )
