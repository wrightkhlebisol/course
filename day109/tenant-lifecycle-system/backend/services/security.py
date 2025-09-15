import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class SecurityService:
    """Handles tenant security setup and API key management"""
    
    def __init__(self):
        self.api_keys = {}  # In production, use proper key storage
    
    async def setup_tenant_security(self, tenant_id: str, tenant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Setup security boundaries for new tenant"""
        print(f"🔐 Setting up security for tenant {tenant_id}")
        
        # Generate API key
        api_key = self._generate_api_key(tenant_id)
        
        # Create access control policies
        policies = self._create_access_policies(tenant_id, tenant_data.get("plan", "basic"))
        
        # Setup encryption keys for tenant data
        encryption_key = self._generate_encryption_key()
        
        security_config = {
            "api_key": api_key,
            "access_policies": policies,
            "encryption_key_id": f"key-{tenant_id}",
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=365)).isoformat()
        }
        
        print(f"✅ Security configured for tenant {tenant_id}")
        return security_config
    
    def _generate_api_key(self, tenant_id: str) -> str:
        """Generate secure API key for tenant"""
        random_part = secrets.token_hex(16)
        tenant_hash = hashlib.sha256(tenant_id.encode()).hexdigest()[:8]
        api_key = f"tnt_{tenant_hash}_{random_part}"
        
        self.api_keys[api_key] = {
            "tenant_id": tenant_id,
            "created_at": datetime.now(),
            "active": True
        }
        
        return api_key
    
    def _generate_encryption_key(self) -> str:
        """Generate encryption key for tenant data"""
        return secrets.token_hex(32)
    
    def _create_access_policies(self, tenant_id: str, plan: str) -> Dict[str, Any]:
        """Create access control policies based on plan"""
        base_policies = {
            "log_ingestion": True,
            "log_query": True,
            "config_read": True,
            "config_write": False
        }
        
        if plan in ["pro", "enterprise"]:
            base_policies.update({
                "config_write": True,
                "advanced_analytics": True
            })
        
        if plan == "enterprise":
            base_policies.update({
                "admin_access": True,
                "audit_logs": True,
                "compliance_reporting": True
            })
        
        return base_policies
    
    async def revoke_tenant_security(self, tenant_id: str) -> Dict[str, Any]:
        """Revoke all security credentials for tenant"""
        print(f"🚫 Revoking security for tenant {tenant_id}")
        
        # Revoke API keys
        revoked_keys = []
        for api_key, key_data in self.api_keys.items():
            if key_data["tenant_id"] == tenant_id:
                key_data["active"] = False
                key_data["revoked_at"] = datetime.now()
                revoked_keys.append(api_key)
        
        print(f"✅ Security revoked for tenant {tenant_id}")
        return {
            "revoked_keys": len(revoked_keys),
            "revoked_at": datetime.now().isoformat()
        }
