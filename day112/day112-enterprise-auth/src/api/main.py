import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select
import jwt
from datetime import datetime, timedelta
import structlog
from typing import Dict, Optional, List
import hashlib
import asyncio

from config.settings import settings
from src.auth.models import User, UserGroup, AuthSession, AuthLog, Base
from src.ldap.service import ldap_service
from src.sync.service import sync_service

# Initialize logging
logger = structlog.get_logger()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise Authentication Service for Distributed Log Processing",
    version=settings.API_VERSION
)

# Database setup
engine = create_engine(settings.DATABASE_URL)
Base.metadata.create_all(bind=engine)

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Security
security = HTTPBearer(auto_error=False)

def get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()

def create_access_token(user: User, groups: List[UserGroup]) -> str:
    """Create JWT access token"""
    roles = list(set([group.role for group in groups]))
    payload = {
        'sub': user.username,
        'user_id': user.id,
        'email': user.email,
        'full_name': user.full_name,
        'department': user.department,
        'roles': roles,
        'exp': datetime.utcnow() + timedelta(minutes=settings.SESSION_EXPIRE_MINUTES),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current authenticated user"""
    if not credentials:
        return None
    
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=['HS256'])
        username = payload.get('sub')
        if not username:
            return None
        
        user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
        return user
        
    except jwt.PyJWTError:
        return None

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, user: User = Depends(get_current_user)):
    """Main authentication dashboard"""
    if not user:
        return templates.TemplateResponse("login.html", {"request": request})
    
    # Get user stats
    with Session(engine) as db:
        user_groups = db.execute(
            select(UserGroup).where(UserGroup.user_id == user.id)
        ).scalars().all()
        
        recent_logs = db.execute(
            select(AuthLog)
            .where(AuthLog.username == user.username)
            .order_by(AuthLog.timestamp.desc())
            .limit(10)
        ).scalars().all()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "groups": user_groups,
        "recent_logs": recent_logs
    })

@app.post("/api/auth/login")
async def login(request: Request, response: Response):
    """Enterprise authentication endpoint"""
    body = await request.json()
    username = body.get('username', '').strip()
    password = body.get('password', '')
    
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")
    
    # Get client info
    client_ip = request.client.host
    user_agent = request.headers.get('user-agent', '')
    
    # Authenticate against LDAP
    is_authenticated, user_info = await ldap_service.authenticate_user(username, password)
    
    with Session(engine) as db:
        if is_authenticated and user_info:
            # Get or create user
            user = db.execute(
                select(User).where(User.username == username)
            ).scalar_one_or_none()
            
            if not user:
                # Create user from LDAP info
                user = await sync_service.create_user_from_ldap(user_info)
                
            if user:
                # Get user groups
                user_groups = db.execute(
                    select(UserGroup).where(UserGroup.user_id == user.id)
                ).scalars().all()
                
                # Create session
                session_id = hashlib.sha256(f"{username}:{datetime.utcnow()}".encode()).hexdigest()
                session = AuthSession(
                    session_id=session_id,
                    user_id=user.id,
                    source_ip=client_ip,
                    user_agent=user_agent,
                    expires_at=datetime.utcnow() + timedelta(minutes=settings.SESSION_EXPIRE_MINUTES)
                )
                db.add(session)
                
                # Create access token
                token = create_access_token(user, user_groups)
                
                # Log successful login
                auth_log = AuthLog(
                    username=username,
                    action='login',
                    source_ip=client_ip,
                    user_agent=user_agent,
                    success=True,
                    message='Successful LDAP authentication'
                )
                db.add(auth_log)
                db.commit()
                
                logger.info("User login successful", username=username, ip=client_ip)
                
                return JSONResponse({
                    'status': 'success',
                    'token': token,
                    'user': {
                        'username': user.username,
                        'email': user.email,
                        'full_name': user.full_name,
                        'department': user.department,
                        'roles': list(set([g.role for g in user_groups]))
                    }
                })
        
        # Log failed login
        auth_log = AuthLog(
            username=username,
            action='failed_login',
            source_ip=client_ip,
            user_agent=user_agent,
            success=False,
            message='Invalid credentials or user not found'
        )
        db.add(auth_log)
        db.commit()
        
        logger.warning("Login failed", username=username, ip=client_ip)
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/auth/profile")
async def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user profile"""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_groups = db.execute(
        select(UserGroup).where(UserGroup.user_id == user.id)
    ).scalars().all()
    
    return {
        'username': user.username,
        'email': user.email,
        'full_name': user.full_name,
        'department': user.department,
        'manager': user.manager,
        'roles': list(set([g.role for g in user_groups])),
        'groups': [{'name': g.group_name, 'role': g.role} for g in user_groups]
    }

@app.post("/api/sync/user/{username}")
async def sync_user(username: str, user: User = Depends(get_current_user)):
    """Manually sync a user from LDAP"""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if user has admin role
    with Session(engine) as db:
        user_groups = db.execute(
            select(UserGroup).where(UserGroup.user_id == user.id)
        ).scalars().all()
        
        if 'Admin' not in [g.role for g in user_groups]:
            raise HTTPException(status_code=403, detail="Admin access required")
    
    # Perform sync
    result = await sync_service.sync_user(username)
    
    return {
        'status': 'success' if result else 'failed',
        'username': username,
        'message': 'User synchronized successfully' if result else 'Sync failed'
    }

@app.post("/api/sync/all")
async def sync_all_users(user: User = Depends(get_current_user)):
    """Sync all users from LDAP"""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check admin access
    with Session(engine) as db:
        user_groups = db.execute(
            select(UserGroup).where(UserGroup.user_id == user.id)
        ).scalars().all()
        
        if 'Admin' not in [g.role for g in user_groups]:
            raise HTTPException(status_code=403, detail="Admin access required")
    
    # Start background sync
    stats = await sync_service.sync_all_users()
    
    return {
        'status': 'completed',
        'stats': stats
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    ldap_healthy = await ldap_service.health_check()
    
    with Session(engine) as db:
        try:
            # Check database
            db.execute(select(1))
            db_healthy = True
        except:
            db_healthy = False
    
    overall_health = ldap_healthy and db_healthy
    
    return {
        'status': 'healthy' if overall_health else 'unhealthy',
        'services': {
            'ldap': 'healthy' if ldap_healthy else 'unhealthy',
            'database': 'healthy' if db_healthy else 'unhealthy'
        },
        'timestamp': datetime.utcnow().isoformat()
    }

@app.get("/api/admin/stats")
async def get_admin_stats(user: User = Depends(get_current_user)):
    """Get admin statistics"""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    with Session(engine) as db:
        user_groups = db.execute(
            select(UserGroup).where(UserGroup.user_id == user.id)
        ).scalars().all()
        
        if 'Admin' not in [g.role for g in user_groups]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get statistics
        total_users = db.execute(select(User)).scalars().all()
        active_sessions = db.execute(
            select(AuthSession).where(AuthSession.expires_at > datetime.utcnow())
        ).scalars().all()
        
        recent_logins = db.execute(
            select(AuthLog)
            .where(AuthLog.action == 'login')
            .where(AuthLog.timestamp > datetime.utcnow() - timedelta(hours=24))
        ).scalars().all()
        
        return {
            'total_users': len(total_users),
            'active_sessions': len(active_sessions),
            'logins_24h': len(recent_logins),
            'successful_logins_24h': len([l for l in recent_logins if l.success]),
            'ldap_health': await ldap_service.health_check()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
