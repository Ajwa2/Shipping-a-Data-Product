# Setting Up PostgreSQL Database

You're getting a connection error because PostgreSQL is not running. Here are your options:

## Option 1: Install Docker Desktop (Recommended)

### Step 1: Install Docker Desktop
1. Download from: https://www.docker.com/products/docker-desktop/
2. Install Docker Desktop for Windows
3. Start Docker Desktop
4. Wait for it to fully start (whale icon in system tray)

### Step 2: Start PostgreSQL
```bash
cd medical-telegram-warehouse
docker compose up -d
```

### Step 3: Verify it's running
```bash
docker ps
```

You should see a container named `medical_warehouse_db` running.

---

## Option 2: Install PostgreSQL Locally

### Step 1: Download PostgreSQL
- Download from: https://www.postgresql.org/download/windows/
- Or use installer: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads

### Step 2: Install PostgreSQL
- Run the installer
- Remember the password you set for the `postgres` user
- Default port: 5432

### Step 3: Create Database
```sql
-- Open pgAdmin or psql and run:
CREATE DATABASE medical_warehouse;
```

### Step 4: Update .env file
```bash
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/medical_warehouse
```

---

## Option 3: Use Cloud PostgreSQL (Free Tier)

### Services with Free Tiers:
- **Supabase**: https://supabase.com (Free tier available)
- **Neon**: https://neon.tech (Free tier available)
- **Railway**: https://railway.app (Free tier available)

### Steps:
1. Sign up for one of the services
2. Create a PostgreSQL database
3. Get the connection string
4. Update your `.env` file:
   ```bash
   DATABASE_URL=your_cloud_connection_string_here
   ```

---

## After Setting Up Database

### 1. Load Raw Data
```bash
python scripts/load_raw_to_postgres.py
```

### 2. Run dbt Models
```bash
cd medical_warehouse
dbt run
```

### 3. Run Notebook
Now you can run your Jupyter notebook and it should connect successfully!

---

## Quick Test Connection

You can test if PostgreSQL is running with this Python script:

```python
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/medical_warehouse")

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
        print("✓ Database connection successful!")
except Exception as e:
    print(f"✗ Connection failed: {e}")
    print("\nPlease set up PostgreSQL using one of the options above.")
```

---

## Troubleshooting

### "Connection refused"
- PostgreSQL is not running
- Check if service is started (Windows Services)
- Verify port 5432 is not blocked by firewall

### "Database does not exist"
- Create the database: `CREATE DATABASE medical_warehouse;`

### "Authentication failed"
- Check username/password in `.env`
- Default: `postgres` / `postgres` (if using Docker)

### Docker not found
- Install Docker Desktop
- Make sure Docker Desktop is running
- Restart terminal after installation
