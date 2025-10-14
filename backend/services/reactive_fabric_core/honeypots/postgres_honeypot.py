"""
PostgreSQL Honeypot Implementation
Database honeypot with realistic fake data and honeytokens
"""

import asyncio
import hashlib
import json
import logging
import random
import string
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base_honeypot import BaseHoneypot, HoneypotType, AttackCapture, AttackStage

logger = logging.getLogger(__name__)

class PostgreSQLHoneypot(BaseHoneypot):
    """
    PostgreSQL Database Honeypot
    Contains realistic fake data with planted honeytokens
    """

    def __init__(self,
                 honeypot_id: str = "postgres_db",
                 port: int = 5433,
                 layer: int = 3):
        """
        Initialize PostgreSQL honeypot

        Args:
            honeypot_id: Unique identifier
            port: PostgreSQL port to listen on
            layer: Network layer
        """
        super().__init__(
            honeypot_id=honeypot_id,
            honeypot_type=HoneypotType.DATABASE,
            port=port,
            layer=layer
        )

        self.db_config = self._generate_config()
        self.honeytokens_planted: List[Dict] = []

        # Query tracking
        self.suspicious_queries: List[Dict] = []
        self.query_count = 0

    def _generate_config(self) -> Dict[str, Any]:
        """Generate PostgreSQL configuration"""
        return {
            "database": "production_backup",
            "user": "backup_user",
            "password": "Backup2024!",  # Weak but realistic
            "max_connections": 100,
            "shared_buffers": "256MB",
            "log_statement": "all",  # Log everything
            "log_connections": True,
            "log_disconnections": True
        }

    def get_docker_config(self) -> Dict[str, Any]:
        """Get Docker configuration for PostgreSQL"""
        return {
            "image": "postgres:14",
            "internal_port": 5432,
            "hostname": "db-backup-01",
            "environment": {
                "POSTGRES_DB": self.db_config["database"],
                "POSTGRES_USER": self.db_config["user"],
                "POSTGRES_PASSWORD": self.db_config["password"],
                "POSTGRES_INITDB_ARGS": "-c shared_buffers=256MB",
                "PGDATA": "/var/lib/postgresql/data/pgdata"
            },
            "volumes": [
                f"{self.log_path}/data:/var/lib/postgresql/data",
                f"{self.log_path}/logs:/var/log/postgresql",
                f"{self.log_path}/init:/docker-entrypoint-initdb.d"
            ],
            "memory": "2g",
            "cpus": "1.5",
            "command": [
                "postgres",
                "-c", "log_statement=all",
                "-c", "log_connections=on",
                "-c", "log_disconnections=on",
                "-c", "log_duration=on"
            ]
        }

    async def start(self) -> bool:
        """Start PostgreSQL honeypot"""
        logger.info(f"Starting PostgreSQL honeypot on port {self.port}")

        # Create necessary directories
        for dir_name in ["data", "logs", "init", "backups"]:
            (self.log_path / dir_name).mkdir(parents=True, exist_ok=True)

        # Generate initialization SQL with fake data
        await self._generate_init_sql()

        # Deploy container
        success = await self.deploy()

        if success:
            # Wait for PostgreSQL to be ready
            await asyncio.sleep(10)

            # Start log monitoring
            asyncio.create_task(self._monitor_postgres_logs())

            # Start query analysis
            asyncio.create_task(self._analyze_queries())

        return success

    async def stop(self) -> bool:
        """Stop PostgreSQL honeypot"""
        logger.info("Stopping PostgreSQL honeypot")
        await self.shutdown()
        return True

    async def _generate_init_sql(self):
        """Generate SQL initialization script with fake data"""
        init_sql_path = self.log_path / "init" / "01-init.sql"

        sql_content = self._build_database_schema()
        sql_content += self._build_fake_customer_data()
        sql_content += self._build_honeytoken_tables()
        sql_content += self._build_audit_triggers()

        with open(init_sql_path, "w") as f:
            f.write(sql_content)

        logger.info("Generated initialization SQL with fake data and honeytokens")

    def _build_database_schema(self) -> str:
        """Build realistic database schema"""
        return """
-- Production Backup Database
-- Created: 2025-10-13
-- CONFIDENTIAL - Internal Use Only

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    customer_code VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    ssn VARCHAR(11),  -- Social Security Number (SENSITIVE!)
    date_of_birth DATE,
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    credit_card_last4 VARCHAR(4),
    credit_limit DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active'
);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id BIGSERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    transaction_date TIMESTAMP NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    description TEXT,
    merchant VARCHAR(255),
    category VARCHAR(50),
    status VARCHAR(20) DEFAULT 'completed'
);

-- User accounts table
CREATE TABLE IF NOT EXISTS user_accounts (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    last_login TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    account_locked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_ssn ON customers(ssn);
CREATE INDEX idx_transactions_customer ON transactions(customer_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);

"""

    def _build_fake_customer_data(self) -> str:
        """Generate realistic but fake customer data"""
        sql = "\n-- Inserting fake customer data\n"

        # Generate 1000 fake customers
        first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa",
                       "James", "Mary", "William", "Patricia", "Richard", "Jennifer", "Charles"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
                      "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez"]

        cities = [("New York", "NY"), ("Los Angeles", "CA"), ("Chicago", "IL"),
                  ("Houston", "TX"), ("Phoenix", "AZ"), ("Philadelphia", "PA"),
                  ("San Antonio", "TX"), ("San Diego", "CA"), ("Dallas", "TX")]

        for i in range(1000):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            email = f"{first_name.lower()}.{last_name.lower()}{i}@email.com"

            # Generate fake SSN (not real format)
            ssn = f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"

            # Random date of birth
            days_ago = random.randint(18*365, 80*365)
            dob = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

            city, state = random.choice(cities)
            zip_code = f"{random.randint(10000, 99999)}"

            credit_card = f"{random.randint(1000, 9999)}"
            credit_limit = random.randint(1000, 50000)

            sql += f"""
INSERT INTO customers (customer_code, first_name, last_name, email, phone, ssn,
                      date_of_birth, city, state, zip_code, credit_card_last4, credit_limit)
VALUES ('CUST{i:06d}', '{first_name}', '{last_name}', '{email}',
        '555-{random.randint(1000, 9999)}', '{ssn}', '{dob}',
        '{city}', '{state}', '{zip_code}', '{credit_card}', {credit_limit});
"""

        # Add some admin users with weak passwords
        sql += """
-- Admin user accounts (WEAK PASSWORDS - FOR TESTING ONLY!)
INSERT INTO user_accounts (username, password_hash, email, role)
VALUES
    ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7GxOJwxzKK', 'admin@company.com', 'administrator'),
    ('backup_admin', '$2b$12$4X1RhMCj8.kT4G8qv9R7Q.xLZR0Rd0/LewY5NU7GxOJwxzKK', 'backup@company.com', 'backup_admin'),
    ('db_admin', '$2b$12$5Y2SiNDk9.lU5H9rw0S8R.yMaSR1Se1/MfxZ6OV8HyPKyAKxxALL', 'dbadmin@company.com', 'dba');
"""

        return sql

    def _build_honeytoken_tables(self) -> str:
        """Build tables with honeytokens"""
        sql = """
-- Honeytokens table (HIGHLY SENSITIVE)
CREATE TABLE IF NOT EXISTS api_credentials (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    api_key VARCHAR(255) NOT NULL,
    api_secret VARCHAR(255) NOT NULL,
    environment VARCHAR(20) DEFAULT 'production',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    notes TEXT
);

-- Plant honeytokens
INSERT INTO api_credentials (service_name, api_key, api_secret, environment, notes)
VALUES
    ('AWS Production', 'AKIAIOSFODNN7EXAMPLE', 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY', 'production', 'Main AWS account - DO NOT SHARE'),
    ('Stripe Payment Gateway', 'sk_live_51HnToken12345Example', 'whsec_HoneytokenWebhookSecret123', 'production', 'Production payment processing'),
    ('SendGrid Email', 'SG.HoneytokenExampleSendGridKey.1234567890abcdef', NULL, 'production', 'Email service API key'),
    ('GitHub Deploy', 'ghp_HoneytokenGitHubPersonalAccessToken123456', NULL, 'production', 'CI/CD deployment key'),
    ('Database Backup', 'backup_user:Sup3rS3cr3tBackupP@ssw0rd!', NULL, 'production', 'Automated backup credentials');

-- SSH Keys table
CREATE TABLE IF NOT EXISTS ssh_keys (
    id SERIAL PRIMARY KEY,
    key_name VARCHAR(100) NOT NULL,
    public_key TEXT NOT NULL,
    private_key TEXT NOT NULL,
    passphrase VARCHAR(255),
    server VARCHAR(255),
    purpose TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Plant SSH honeytokens
INSERT INTO ssh_keys (key_name, public_key, private_key, server, purpose)
VALUES (
    'production-server-key',
    'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDHoneytokenPublicKey root@prod',
    '-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAHoneytokenPrivateKeyContent
[... truncated for brevity ...]
-----END RSA PRIVATE KEY-----',
    'prod-app-01.internal.company.com',
    'Production application server access'
);

-- Internal endpoints table
CREATE TABLE IF NOT EXISTS internal_endpoints (
    id SERIAL PRIMARY KEY,
    endpoint_name VARCHAR(100),
    url VARCHAR(500),
    api_key VARCHAR(255),
    description TEXT
);

INSERT INTO internal_endpoints (endpoint_name, url, api_key, description)
VALUES
    ('Internal Admin API', 'https://admin.internal.company.com/api/v1', 'admin_token_honeytoken_12345', 'Internal admin dashboard API'),
    ('Metrics Collector', 'https://metrics.internal.company.com', 'metrics_key_honeytoken_67890', 'Application metrics endpoint'),
    ('CI/CD Webhook', 'https://deploy.internal.company.com/webhook', 'webhook_secret_honeytoken_abcdef', 'Deployment automation');
"""

        # Track planted honeytokens
        self.honeytokens_planted = [
            {"type": "aws_credentials", "identifier": "AKIAIOSFODNN7EXAMPLE"},
            {"type": "stripe_key", "identifier": "sk_live_51HnToken12345Example"},
            {"type": "ssh_private_key", "identifier": "production-server-key"},
            {"type": "github_pat", "identifier": "ghp_HoneytokenGitHub"},
            {"type": "internal_api", "identifier": "admin_token_honeytoken"}
        ]

        return sql

    def _build_audit_triggers(self) -> str:
        """Build audit triggers to detect suspicious access"""
        return """
-- Audit log table
CREATE TABLE IF NOT EXISTS query_audit_log (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    username VARCHAR(100),
    database_name VARCHAR(100),
    query_text TEXT,
    rows_affected INTEGER,
    execution_time_ms INTEGER,
    client_ip VARCHAR(50),
    suspicious BOOLEAN DEFAULT FALSE,
    alert_triggered BOOLEAN DEFAULT FALSE
);

-- Function to log sensitive table access
CREATE OR REPLACE FUNCTION log_sensitive_access()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO query_audit_log (username, database_name, query_text, suspicious, alert_triggered)
    VALUES (
        current_user,
        current_database(),
        current_query(),
        TRUE,  -- Mark as suspicious
        TRUE   -- Trigger alert
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for sensitive tables
CREATE TRIGGER audit_api_credentials_access
    AFTER SELECT ON api_credentials
    FOR EACH STATEMENT
    EXECUTE FUNCTION log_sensitive_access();

CREATE TRIGGER audit_ssh_keys_access
    AFTER SELECT ON ssh_keys
    FOR EACH STATEMENT
    EXECUTE FUNCTION log_sensitive_access();

-- Grant permissions to honeypot user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO backup_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO backup_user;
"""

    async def _process_logs(self):
        """Process PostgreSQL logs for suspicious activity"""
        pass  # Implemented in monitor task

    async def _monitor_postgres_logs(self):
        """Monitor PostgreSQL logs in real-time"""
        log_file = self.log_path / "logs" / "postgresql.log"

        # Wait for log file
        while not log_file.exists() and self._running:
            await asyncio.sleep(5)

        if not self._running:
            return

        cmd = ["tail", "-f", str(log_file)]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        while self._running:
            try:
                line = await process.stdout.readline()
                if not line:
                    break

                log_entry = line.decode().strip()
                await self._process_log_entry(log_entry)

            except Exception as e:
                logger.error(f"Error monitoring PostgreSQL logs: {e}")

        process.terminate()

    async def _process_log_entry(self, log_entry: str):
        """Process a PostgreSQL log entry"""
        # Look for connections
        if "connection received" in log_entry or "connection authorized" in log_entry:
            await self._handle_connection(log_entry)

        # Look for queries
        elif "statement:" in log_entry or "execute" in log_entry:
            await self._handle_query(log_entry)

        # Look for errors (SQL injection attempts often cause errors)
        elif "ERROR:" in log_entry or "FATAL:" in log_entry:
            await self._handle_error(log_entry)

    async def _handle_connection(self, log_entry: str):
        """Handle new database connection"""
        # Extract connection details
        # Example: 2025-10-13 10:00:00 UTC [1234-1] user=backup_user,db=production_backup,host=1.2.3.4

        self.query_count += 1
        logger.info(f"New PostgreSQL connection detected: {log_entry[:100]}")

    async def _handle_query(self, log_entry: str):
        """Handle SQL query execution"""
        # Check for suspicious patterns
        suspicious_patterns = [
            "api_credentials",
            "ssh_keys",
            "password_hash",
            "ssn",
            "credit_card",
            "UNION SELECT",
            "DROP TABLE",
            "pg_sleep",
            "pg_read_file",
            "COPY.*FROM PROGRAM"
        ]

        is_suspicious = any(pattern.lower() in log_entry.lower()
                           for pattern in suspicious_patterns)

        if is_suspicious:
            self.suspicious_queries.append({
                "timestamp": datetime.now(),
                "query": log_entry,
                "alert_level": "HIGH"
            })

            logger.warning(f"SUSPICIOUS QUERY detected: {log_entry[:200]}")

            # Check if honeytoken was accessed
            if any(token in log_entry for token in ["api_credentials", "ssh_keys", "internal_endpoints"]):
                logger.critical("HONEYTOKEN TABLE ACCESSED!")
                await self._trigger_honeytoken_alert(log_entry)

    async def _handle_error(self, log_entry: str):
        """Handle database errors (often from SQL injection)"""
        logger.info(f"Database error logged: {log_entry[:100]}")

        # SQL injection attempts often cause syntax errors
        if "syntax error" in log_entry.lower():
            logger.warning("Potential SQL injection attempt detected")

    async def _trigger_honeytoken_alert(self, query: str):
        """Trigger critical alert when honeytoken is accessed"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "honeypot_id": self.honeypot_id,
            "alert_type": "HONEYTOKEN_ACCESSED",
            "severity": "CRITICAL",
            "query": query,
            "honeytokens_exposed": [
                token for token in self.honeytokens_planted
                if token["identifier"].lower() in query.lower()
            ]
        }

        # Save alert
        alert_file = self.log_path / "alerts" / f"honeytoken_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        alert_file.parent.mkdir(exist_ok=True)

        with open(alert_file, "w") as f:
            json.dump(alert, f, indent=2)

        logger.critical(f"HONEYTOKEN ALERT saved: {alert_file}")

    async def _analyze_queries(self):
        """Periodic analysis of query patterns"""
        while self._running:
            await asyncio.sleep(300)  # Every 5 minutes

            if self.suspicious_queries:
                logger.info(f"Analyzed {len(self.suspicious_queries)} suspicious queries")

                # Generate report
                report_path = self.log_path / "reports" / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
                report_path.parent.mkdir(exist_ok=True)

                with open(report_path, "w") as f:
                    json.dump({
                        "timestamp": datetime.now().isoformat(),
                        "total_queries": self.query_count,
                        "suspicious_queries": len(self.suspicious_queries),
                        "recent_suspicious": self.suspicious_queries[-10:]
                    }, f, indent=2, default=str)

    def get_honeytoken_status(self) -> Dict:
        """Get status of planted honeytokens"""
        return {
            "total_planted": len(self.honeytokens_planted),
            "honeytokens": self.honeytokens_planted,
            "last_check": datetime.now().isoformat()
        }