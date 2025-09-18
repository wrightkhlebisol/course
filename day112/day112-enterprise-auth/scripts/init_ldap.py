#!/usr/bin/env python3
"""Initialize LDAP directory with test data"""

import asyncio
from ldap3 import Server, Connection, ALL, SUBTREE, MODIFY_ADD
import time
import os

def wait_for_ldap():
    """Wait for LDAP server to be ready"""
    print("Waiting for LDAP server to start...")
    max_attempts = 30
    
    for attempt in range(max_attempts):
        try:
            ldap_server = os.getenv('LDAP_SERVER', 'ldap://localhost:389')
            bind_dn = os.getenv('LDAP_BIND_DN', 'cn=admin,dc=company,dc=com')
            bind_password = os.getenv('LDAP_BIND_PASSWORD', 'admin')
            server = Server(ldap_server, get_info=ALL)
            conn = Connection(server, bind_dn, bind_password, auto_bind=True)
            print("✅ LDAP server is ready!")
            conn.unbind()
            return True
        except Exception as e:
            if attempt < max_attempts - 1:
                print(f"Attempt {attempt + 1}/{max_attempts} failed, retrying...")
                time.sleep(2)
            else:
                print(f"❌ LDAP server not ready after {max_attempts} attempts")
                return False
    
    return False

def init_ldap_data():
    """Initialize LDAP with test users and groups"""
    try:
        ldap_server = os.getenv('LDAP_SERVER', 'ldap://localhost:389')
        bind_dn = os.getenv('LDAP_BIND_DN', 'cn=admin,dc=company,dc=com')
        bind_password = os.getenv('LDAP_BIND_PASSWORD', 'admin')
        base_dn = os.getenv('LDAP_BASE_DN', 'dc=company,dc=com')
        server = Server(ldap_server, get_info=ALL)
        conn = Connection(server, bind_dn, bind_password, auto_bind=True)
        
        print("🔧 Initializing LDAP directory structure...")
        
        # Create organizational units
        ou_entries = [
            ('ou=users,dc=company,dc=com', ['organizationalUnit'], {'ou': 'users'}),
            ('ou=groups,dc=company,dc=com', ['organizationalUnit'], {'ou': 'groups'})
        ]
        
        for dn, object_classes, attrs in ou_entries:
            try:
                conn.add(dn, object_classes, attrs)
                print(f"✅ Created OU: {dn}")
            except Exception as e:
                print(f"⚠️  OU {dn} might already exist: {e}")
        
        # Create test users
        users = [
            {
                'dn': 'cn=testuser,ou=users,dc=company,dc=com',
                'object_classes': ['inetOrgPerson', 'organizationalPerson', 'person', 'top'],
                'attrs': {
                    'cn': 'testuser',
                    'sn': 'User',
                    'givenName': 'Test',
                    'mail': 'test@company.com',
                    'userPassword': 'password123',
                    'uid': 'testuser',
                    'description': 'Test User - IT Department'
                }
            },
            {
                'dn': 'cn=admin,ou=users,dc=company,dc=com',
                'object_classes': ['inetOrgPerson', 'organizationalPerson', 'person', 'top'],
                'attrs': {
                    'cn': 'admin',
                    'sn': 'Administrator',
                    'givenName': 'System',
                    'mail': 'admin@company.com',
                    'userPassword': 'admin123',
                    'uid': 'admin',
                    'description': 'System Administrator - IT Department'
                }
            },
            {
                'dn': 'cn=analyst,ou=users,dc=company,dc=com',
                'object_classes': ['inetOrgPerson', 'organizationalPerson', 'person', 'top'],
                'attrs': {
                    'cn': 'analyst',
                    'sn': 'Analyst',
                    'givenName': 'Log',
                    'mail': 'analyst@company.com',
                    'userPassword': 'analyst123',
                    'uid': 'analyst',
                    'description': 'Log Analyst - Analytics Department'
                }
            }
        ]
        
        for user in users:
            try:
                conn.add(user['dn'], user['object_classes'], user['attrs'])
                print(f"✅ Created user: {user['attrs']['cn']}")
            except Exception as e:
                print(f"⚠️  User {user['attrs']['cn']} might already exist: {e}")
        
        # Create test groups
        groups = [
            {
                'dn': 'cn=administrators,ou=groups,dc=company,dc=com',
                'attrs': {
                    'cn': 'administrators',
                    'description': 'System administrators',
                    'member': ['cn=admin,ou=users,dc=company,dc=com', 'cn=testuser,ou=users,dc=company,dc=com']
                }
            },
            {
                'dn': 'cn=log-analysts,ou=groups,dc=company,dc=com',
                'attrs': {
                    'cn': 'log-analysts',
                    'description': 'Log data analysts',
                    'member': ['cn=analyst,ou=users,dc=company,dc=com', 'cn=testuser,ou=users,dc=company,dc=com']
                }
            },
            {
                'dn': 'cn=log-viewers,ou=groups,dc=company,dc=com',
                'attrs': {
                    'cn': 'log-viewers',
                    'description': 'Log data viewers',
                    'member': ['cn=testuser,ou=users,dc=company,dc=com']
                }
            }
        ]
        
        for group in groups:
            try:
                conn.add(group['dn'], ['groupOfNames'], group['attrs'])
                print(f"✅ Created group: {group['attrs']['cn']}")
            except Exception as e:
                print(f"⚠️  Group {group['attrs']['cn']} might already exist: {e}")
        
        conn.unbind()
        print("🎉 LDAP initialization completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ LDAP initialization failed: {e}")
        return False

if __name__ == "__main__":
    if wait_for_ldap():
        init_ldap_data()
    else:
        exit(1)
