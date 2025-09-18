from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # App Configuration
    APP_NAME: str = "Enterprise Authentication Service"
    DEBUG: bool = False
    API_VERSION: str = "v1"
    SECRET_KEY: str = "enterprise-auth-secret-key-change-in-production"
    
    # LDAP Configuration
    LDAP_SERVER: str = "ldap://localhost:389"
    LDAP_SERVER_SSL: str = "ldaps://localhost:636"
    LDAP_BIND_DN: str = "cn=admin,dc=company,dc=com"
    LDAP_BIND_PASSWORD: str = "admin"
    LDAP_BASE_DN: str = "dc=company,dc=com"
    LDAP_USER_SEARCH: str = "(uid={username})"
    LDAP_GROUP_SEARCH: str = "(member={user_dn})"
    
    # Active Directory Configuration  
    AD_SERVER: str = "ldap://ad.company.com:389"
    AD_DOMAIN: str = "COMPANY"
    AD_BASE_DN: str = "DC=company,DC=com"
    AD_USER_SEARCH: str = "(&(objectClass=user)(sAMAccountName={username}))"
    AD_GROUP_SEARCH: str = "(&(objectClass=group)(member={user_dn}))"
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://user:pass@localhost/enterprise_auth"
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Session Configuration
    SESSION_EXPIRE_MINUTES: int = 480  # 8 hours
    CACHE_EXPIRE_MINUTES: int = 15
    
    # Sync Configuration
    SYNC_INTERVAL_MINUTES: int = 30
    BATCH_SIZE: int = 100
    
    class Config:
        env_file = ".env"

settings = Settings()
