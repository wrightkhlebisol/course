"""Initialize test database with sample log data."""
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import random
import json

def init_database():
    """Create logs table and populate with sample data."""
    engine = create_engine('sqlite:///data/logs.db')
    
    with engine.connect() as conn:
        # Create logs table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP NOT NULL,
                service TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                metadata TEXT
            )
        """))
        conn.commit()
        
        # Check if data exists
        result = conn.execute(text("SELECT COUNT(*) FROM logs"))
        count = result.fetchone()[0]
        
        if count > 0:
            print(f"Database already has {count} records")
            return
        
        # Generate sample logs
        services = ['api-gateway', 'auth-service', 'payment-service', 'user-service', 'notification-service']
        levels = ['INFO', 'WARNING', 'ERROR', 'DEBUG']
        messages = [
            'Request processed successfully',
            'Authentication failed',
            'Payment transaction completed',
            'User session created',
            'Email notification sent',
            'Database query slow',
            'Cache miss occurred',
            'Rate limit exceeded'
        ]
        
        print("Generating 5000 sample log entries...")
        
        logs = []
        for i in range(5000):
            timestamp = datetime.utcnow() - timedelta(hours=random.randint(0, 72))
            service = random.choice(services)
            level = random.choice(levels)
            message = random.choice(messages)
            metadata = json.dumps({
                'request_id': f'req_{random.randint(1000, 9999)}',
                'user_id': random.randint(1, 1000),
                'duration_ms': random.randint(10, 500)
            })
            
            logs.append({
                'timestamp': timestamp,
                'service': service,
                'level': level,
                'message': message,
                'metadata': metadata
            })
        
        # Insert in batches
        conn.execute(text("""
            INSERT INTO logs (timestamp, service, level, message, metadata)
            VALUES (:timestamp, :service, :level, :message, :metadata)
        """), logs)
        conn.commit()
        
        print(f"✓ Inserted {len(logs)} sample log entries")

if __name__ == '__main__':
    init_database()
