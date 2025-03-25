from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from pydantic import EmailStr
from datetime import datetime
from src.db.main import get_session
from src.db.redis import add_token_to_blacklist
from src.auth.dependencies import (
    AccessTokenBearer,
    RefreshTokenBearer,
    RoleChecker,
    get_current_user,
)
from src.auth.service import AuthService
from .utils import (
    generate_password_hash,
    verify_password,
    create_token,
    convert_str,
    templates,
    create_safe_token,
    decode_safe_token,
)
from src.config import settings
from src.mail import create_message, mail
from .schema import (
    LoginSchema,
    UserSchema,
    EmailSchema,
    PasswordResetSchema,
    PasswordConfirmSchema,
    UserUpdateSchema,
    UserRoleUpdate,
)
from src.db.models import User

admin_checker = Depends(RoleChecker(["admin"]))
manager_user = Depends(RoleChecker(["manager"]))
admin_manager_checker = Depends(RoleChecker(["admin", "manager"]))

auth_router = APIRouter()
auth_service = AuthService()

# For the token data pass the following, email, user_id, role

# TODO : -> Create Staff Routes
# TODO : -> Create Update User role but only admin can access it
# TODO : -> Update for User with customer role but everyone can access it.


@auth_router.post("/send_email")
async def send_background_email(
    email_details: EmailSchema, background_task: BackgroundTasks
):
    try:
        email_message = create_message(
            email_details.emails, email_details.subject, email_details.body
        )
        background_task.add_task(mail.send_message, email_message)

        return JSONResponse(
            content={
                "message": f"Email Sent Succesfully to {str(email_details.emails)}"
            },
            status_code=status.HTTP_201_CREATED,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Unable to Send Email: {str(e)}",
        )


@auth_router.get("/login")
async def user_logger(
    login_details: LoginSchema, session: AsyncSession = Depends(get_session)
):
    # Verify Email and password and create a new Access and Refresh Token
    user = await auth_service.get_user(login_details.email, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email {str(login_details.email)} is not present in the database",
        )
    if not verify_password(login_details.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Passsword didn't matched. Please Check the password and Try Again",
        )

    token_payload = {
        "email": login_details.email,
        "user_id": str(user.uid),
        "role": user.role,
    }
    access_token = create_token(token_payload)
    refresh_token = create_token(token_payload, True)

    return JSONResponse(
        content={
            "message": "User Logged in Succesfully",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user_id": str(user.uid),
        },
        status_code=status.HTTP_200_OK,
    )


@auth_router.get("/logout")
async def logout_user(
    token_data=Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    try:
        await add_token_to_blacklist(token_data["jti"])
        return JSONResponse(
            content={"message": "User Logged out successfully"},
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Something went wrong when accessing logout service: {str(e)}",
        )


@auth_router.get("/verify/{safe_token}")
async def verify_user_account(
    safe_token: str, session: AsyncSession = Depends(get_session)
):
    token_data = decode_safe_token(safe_token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail="Token id Expired or Invalid. Please Try again",
        )

    email_id = token_data.get("email")
    if not email_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Something went wrong when parsing token value",
        )
    user_info, customer_info = await auth_service.get_user_cum_customer(
        email_id, session
    )

    update_customer = await auth_service.update_customer(
        customer_info, {"is_verified": True}, session
    )

    return JSONResponse(
        content={
            "message": f"Customer with email {str(email_id)} is verified succesfully"
        },
        status_code=status.HTTP_201_CREATED,
    )


@auth_router.get("/generate_access_token")
async def generate_access_token(
    session: AsyncSession = Depends(get_session),
    token_data=Depends(RefreshTokenBearer()),
):
    expiry_timestamp = token_data["expiry"]
    current_timestamp = datetime.now().isoformat()
    if current_timestamp >= expiry_timestamp:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Refresh Token Expired. Please Login again",
        )

    new_access_token = create_token(token_data["user"])

    return JSONResponse(
        content={"message": "Access Token Generated", "access_token": new_access_token},
        status_code=status.HTTP_201_CREATED,
    )
    # expiry_datetime = expiry_timestamp


@auth_router.post("/create_customer")
async def create_new_customer(
    user_input: UserSchema,
    background_task: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    try:
        await auth_service.create_user(user_input, session)
        await auth_service.create_customer(user_input.email, session)

        new_user_customer = await auth_service.get_user_cum_customer(
            user_input.email, session
        )
        if not new_user_customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User Customer record not found",
            )
        user_info, customer_info = new_user_customer
        user_info_dict = convert_str(user_info.model_dump(exclude={"password_hash"}))
        customer_info_dict = convert_str(customer_info.model_dump())

        # Send a Verify account to the new customer
        safe_token = create_safe_token({"email": user_info.email})
        verification_link = f"http://{settings.DOMAIN}/{settings.ROOT_ROUTE}/{settings.APP_VERSION}/verify/{safe_token}"
        email_html = templates.get_template("email_verification_template.html").render(
            user_name=f"{str(user_info.firstname)} {str(user_info.lastname)}",
            verification_url=verification_link,
            current_year=datetime.today().year,
        )
        email_modal = EmailSchema(
            emails=[user_input.email], subject="Verify Account", body=email_html
        )
        await send_background_email(email_modal, background_task)

        return JSONResponse(
            content={
                "message": "Customer created successfully. To verify your account please check the email",
                "user_info": user_info_dict,
                "customer_info": customer_info_dict,
            },
            status_code=status.HTTP_201_CREATED,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error Creating New User : {str(e)}",
        )


@auth_router.patch("/password_reset")
async def send_password_reset(
    email_details: PasswordResetSchema,
    background_task: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    try:
        if not email_details.email_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Please provide email id for furthur Password Reset Process",
            )
        user_info = await auth_service.get_user(email_details.email_id, session)
        pass_safe_token = create_safe_token({"email": email_details.email_id})
        password_reset_link = f"http://{settings.DOMAIN}/{settings.ROOT_ROUTE}/{settings.APP_VERSION}/password_reset_confirm/{pass_safe_token}"
        email_html = templates.get_template("password_reset_template.html").render(
            company_logo=f"http://{settings.DOMAIN}/static/images/pizza_icon_img.jpg",
            company_name="Pizza Plus",
            user_name=f"{user_info.firstname} {user_info.lastname}",
            reset_link=password_reset_link,
            current_year=datetime.today().year,
        )
        email_schema = EmailSchema(
            emails=[email_details.email_id],
            subject="Password Reset Request",
            body=email_html,
        )

        await send_background_email(
            email_details=email_schema, background_task=background_task
        )

        return JSONResponse(
            content={
                "message": f"Password Reset link sent successfully. Please check your email {str(email_details.email_id)} for furthur process"
            },
            status_code=status.HTTP_201_CREATED,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error Sending Password Reset Email : {str(e)}",
        )


@auth_router.patch("/update-user/{user_id}")
async def update_user(
    user_id: str,
    updated_info: UserUpdateSchema,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Fetch User to be Updated
    user_tobe_updated = await auth_service.get_user_by_uid(user_id, session)

    # Authorization Check
    if user.role == "customer":
        # Customers can only update themselves
        if user_id != str(user.uid):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Customers can only update their own account.",
            )
    elif user.role == "manager":
        # Managers can update Customers and other Managers, but NOT Admins
        if user_tobe_updated.role == "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Managers cannot update Admin accounts.",
            )
    elif user.role == "admin":
        # Admins can update anyone (no restrictions)
        pass
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid role permissions.",
        )
    update_user_response = await auth_service.update_user(
        user=user_tobe_updated, updated_info=updated_info, session=session
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": f"User with {str(user_tobe_updated.email)} email has been updated succesfully",
            "user": convert_str(
                update_user_response.model_dump(exclude={"password_hash", "role"})
            ),
        },
    )


@auth_router.patch("/update-role/{user_id}")
async def update_role(
    user_id: str,
    updated_role: UserRoleUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        user_to_be_updated = await auth_service.get_user_by_uid(user_id, session)
        if user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin is allowed to access this service",
            )
        updated_response = await auth_service.update_user_role(
            user=user, updated_schema=updated_role, session=session
        )
        return JSONResponse(
            content={
                "message": "User Role Updated Successfully",
                "user": convert_str(
                    updated_response.model_dump(exclude={"password_hash"})
                ),
            }
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error Updating User role: {str(e)}",
        )


@auth_router.patch("/password_reset_confirm/{password_safe_token}")
async def set_new_password(
    password_safe_token: str,
    new_password_details: PasswordConfirmSchema,
    session: AsyncSession = Depends(get_session),
):
    try:
        email_info = decode_safe_token(password_safe_token)
        email_id = email_info["email"]
        print("Email Decoded: ", email_id)
        if not email_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The Token is Expired or Invalid. Please resend Email again",
            )
        user_details = await auth_service.get_user(email_id, session)

        update_password = await auth_service.update_password(
            user=user_details, new_password_schema=new_password_details, session=session
        )
        if not update_password:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong when updating password. Please try again",
            )
        return JSONResponse(
            content={"message": "Password updated successfully."},
            status_code=status.HTTP_201_CREATED,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error Updating new Password : {str(e)}",
        )


@auth_router.get("/my_info")
async def get_user_info(
    token_details: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    print("Token Details:", token_details)
    user_email = token_details.get("user").get("email")
    user_details = await auth_service.get_user(user_email, session)
    if not user_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with {str(user_email)} could not be found in Database",
        )
    user_details_dict = convert_str(user_details.model_dump())
    user_details_dict.pop("password_hash", None)
    return JSONResponse(
        content={"message": "User Details found", "user details": user_details_dict},
        status_code=status.HTTP_200_OK,
    )
