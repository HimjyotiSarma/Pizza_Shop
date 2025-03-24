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
from .schema import ItemSchema, CategorySchema

item_router = APIRouter()
item_service = ItemService()

admin_checker = Depends(RoleChecker(["admin"]))
manager_user = Depends(RoleChecker(["admin", "manager"]))
admin_manager_checker = Depends(RoleChecker(["admin", "manager"]))


def parse_category_form_data(
    name: str = Form(), type_of: str = Form(), description: str = Form()
) -> CategorySchema:
    return CategorySchema(name=name, type_of=type_of, description=description)


@item_router.post("/create", dependencies=[admin_manager_checker])
async def create_new_Item(
    item_details: ItemSchema, session: AsyncSession = Depends(get_session)
):
    try:
        new_item_details = await item_service.create_new_item(item_details, session)

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
