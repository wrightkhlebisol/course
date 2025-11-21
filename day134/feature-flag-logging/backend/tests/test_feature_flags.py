import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.feature_flag import Base
from app.services.feature_flag_service import flag_service
from app.core.database import get_db

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

@pytest.fixture
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.mark.asyncio
async def test_create_feature_flag(db):
    """Test creating a new feature flag"""
    flag = await flag_service.create_flag(
        db=db,
        name="test_flag",
        description="Test flag description",
        enabled=True,
        rollout_percentage="50"
    )
    
    assert flag.name == "test_flag"
    assert flag.enabled == True
    assert flag.rollout_percentage == "50"

@pytest.mark.asyncio
async def test_update_feature_flag(db):
    """Test updating an existing feature flag"""
    # Create flag first
    flag = await flag_service.create_flag(db=db, name="update_test", enabled=False)
    
    # Update the flag
    updated_flag = await flag_service.update_flag(
        db=db,
        flag_id=flag.id,
        updates={"enabled": True, "rollout_percentage": "75"}
    )
    
    assert updated_flag.enabled == True
    assert updated_flag.rollout_percentage == "75"

@pytest.mark.asyncio
async def test_evaluate_feature_flag(db):
    """Test feature flag evaluation"""
    # Create enabled flag with 100% rollout
    flag = await flag_service.create_flag(
        db=db,
        name="eval_test",
        enabled=True,
        rollout_percentage="100"
    )
    
    result = await flag_service.evaluate_flag(
        db=db,
        flag_name="eval_test",
        user_context={"user_id": "test_user"}
    )
    
    assert result == True

@pytest.mark.asyncio
async def test_delete_feature_flag(db):
    """Test deleting a feature flag"""
    # Create flag first
    flag = await flag_service.create_flag(db=db, name="delete_test")
    
    # Delete the flag
    result = await flag_service.delete_flag(db=db, flag_id=flag.id)
    
    assert result == True
    
    # Verify it's deleted
    flags = await flag_service.get_all_flags(db)
    flag_names = [f.name for f in flags]
    assert "delete_test" not in flag_names

if __name__ == "__main__":
    pytest.main([__file__])
