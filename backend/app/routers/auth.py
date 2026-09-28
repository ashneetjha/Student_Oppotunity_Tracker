from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import User
from backend.app.schemas import UserRegister, UserLogin, UserOut, TokenResponse, UserProfileUpdate
from backend.app.utils.security import hash_password, verify_password
from backend.app.utils.jwt import create_access_token
from backend.app.dependencies.auth import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    # Check duplicate email
    existing_user = db.query(User).filter(User.email == user_data.email.lower().strip()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists"
        )

    # Validate role
    role = "student"
    if user_data.role and user_data.role.lower() == "admin":
        role = "admin"

    new_user = User(
        name=user_data.name.strip(),
        email=user_data.email.lower().strip(),
        password_hash=hash_password(user_data.password),
        college=user_data.college.strip(),
        role=role,
        bio=user_data.bio
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(data={"sub": str(new_user.user_id), "role": new_user.role, "email": new_user.email})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserOut.model_validate(new_user)
    )

@router.post("/login", response_model=TokenResponse)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email.lower().strip()).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = create_access_token(data={"sub": str(user.user_id), "role": user.role, "email": user.email})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserOut.model_validate(user)
    )

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)

@router.put("/profile", response_model=UserOut)
def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if profile_data.name is not None:
        current_user.name = profile_data.name.strip()
    if profile_data.college is not None:
        current_user.college = profile_data.college.strip()
    if profile_data.bio is not None:
        current_user.bio = profile_data.bio.strip()
    
    db.commit()
    db.refresh(current_user)
    return UserOut.model_validate(current_user)
