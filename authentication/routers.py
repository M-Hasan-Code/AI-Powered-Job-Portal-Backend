from .login import router as login_router
from .register import router as register_router
from .resend_verification import router as resend_verification_router
from .verify_email import router as verify_email_router
from .forgot_password import router as forgot_password_router
from .reset_password import router as reset_password_router
from .logout import router as logout_router
from .refresh import router as refresh_router
from fastapi import APIRouter

router = APIRouter()

router.include_router(login_router)
router.include_router(register_router)
router.include_router(resend_verification_router)
router.include_router(verify_email_router)
router.include_router(forgot_password_router)
router.include_router(reset_password_router)
router.include_router(logout_router)
router.include_router(refresh_router)