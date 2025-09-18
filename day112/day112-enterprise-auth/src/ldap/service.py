import asyncio
from ldap3 import Server, Connection, ALL, SUBTREE, MODIFY_REPLACE
from ldap3.core.exceptions import LDAPException
import structlog
from typing import Dict, List, Optional, Tuple
from config.settings import settings
import ssl
from concurrent.futures import ThreadPoolExecutor
import time

logger = structlog.get_logger()

class LDAPService:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.connection_pool = {}
        self.last_health_check = 0
        
    def _get_server(self, use_ssl: bool = False) -> Server:
        """Create LDAP server instance with proper SSL configuration"""
        server_url = settings.LDAP_SERVER_SSL if use_ssl else settings.LDAP_SERVER
        
        if use_ssl:
            tls_config = ssl.create_default_context()
            tls_config.check_hostname = False
            tls_config.verify_mode = ssl.CERT_NONE
            return Server(server_url, get_info=ALL, use_ssl=True, tls=tls_config)
        else:
            return Server(server_url, get_info=ALL)
    
    async def authenticate_user(self, username: str, password: str) -> Tuple[bool, Optional[Dict]]:
        """Authenticate user against LDAP/AD"""
        loop = asyncio.get_event_loop()
        
        def _authenticate():
            try:
                # Try SSL first, fallback to plain
                for use_ssl in [True, False]:
                    try:
                        server = self._get_server(use_ssl)
                        
                        # Bind as admin to search for user
                        admin_conn = Connection(server, settings.LDAP_BIND_DN, 
                                              settings.LDAP_BIND_PASSWORD, auto_bind=True)
                        
                        # Search for user
                        search_filter = settings.LDAP_USER_SEARCH.format(username=username)
                        admin_conn.search(settings.LDAP_BASE_DN, search_filter, 
                                        SUBTREE, attributes=['cn', 'mail', 'uid', 'givenName', 'sn', 'description'])
                        
                        if not admin_conn.entries:
                            logger.warning("User not found in LDAP", username=username)
                            return False, None
                        
                        user_entry = admin_conn.entries[0]
                        user_dn = user_entry.entry_dn
                        
                        # Authenticate user with their credentials
                        user_conn = Connection(server, user_dn, password)
                        if user_conn.bind():
                            # Extract full name from givenName and sn
                            given_name = str(user_entry.givenName) if user_entry.givenName else ''
                            sn = str(user_entry.sn) if user_entry.sn else ''
                            full_name = f"{given_name} {sn}".strip() if given_name or sn else str(user_entry.cn) if user_entry.cn else username
                            
                            user_info = {
                                'dn': user_dn,
                                'username': username,
                                'email': str(user_entry.mail) if user_entry.mail else None,
                                'full_name': full_name,
                                'department': str(user_entry.description) if user_entry.description else None,
                                'manager': None  # Not available in basic schema
                            }
                            
                            user_conn.unbind()
                            admin_conn.unbind()
                            
                            logger.info("User authenticated successfully", username=username)
                            return True, user_info
                        else:
                            logger.warning("Invalid credentials", username=username)
                            return False, None
                            
                    except LDAPException as e:
                        if use_ssl:
                            logger.warning("SSL connection failed, trying plain", error=str(e))
                            continue
                        else:
                            logger.error("LDAP connection failed", error=str(e))
                            return False, None
                
                return False, None
                
            except Exception as e:
                logger.error("Authentication error", error=str(e), username=username)
                return False, None
        
        return await loop.run_in_executor(self.executor, _authenticate)
    
    async def get_user_groups(self, user_dn: str) -> List[Dict]:
        """Get user's group memberships"""
        loop = asyncio.get_event_loop()
        
        def _get_groups():
            try:
                server = self._get_server()
                conn = Connection(server, settings.LDAP_BIND_DN, 
                                settings.LDAP_BIND_PASSWORD, auto_bind=True)
                
                # Search for groups where user is a member
                group_filter = settings.LDAP_GROUP_SEARCH.format(user_dn=user_dn)
                conn.search(settings.LDAP_BASE_DN, group_filter, SUBTREE, 
                          attributes=['cn', 'description'])
                
                groups = []
                for entry in conn.entries:
                    groups.append({
                        'dn': entry.entry_dn,
                        'name': str(entry.cn) if entry.cn else None,
                        'description': str(entry.description) if entry.description else None
                    })
                
                conn.unbind()
                return groups
                
            except Exception as e:
                logger.error("Error getting user groups", error=str(e), user_dn=user_dn)
                return []
        
        return await loop.run_in_executor(self.executor, _get_groups)
    
    async def health_check(self) -> bool:
        """Check LDAP server connectivity"""
        current_time = time.time()
        
        # Cache health check for 30 seconds
        if current_time - self.last_health_check < 30:
            return True
        
        loop = asyncio.get_event_loop()
        
        def _health_check():
            try:
                server = self._get_server()
                conn = Connection(server, settings.LDAP_BIND_DN, 
                                settings.LDAP_BIND_PASSWORD)
                result = conn.bind()
                if conn.bound:
                    conn.unbind()
                return result
            except Exception as e:
                logger.error("LDAP health check failed", error=str(e))
                return False
        
        is_healthy = await loop.run_in_executor(self.executor, _health_check)
        if is_healthy:
            self.last_health_check = current_time
        
        return is_healthy

# Global LDAP service instance
ldap_service = LDAPService()
