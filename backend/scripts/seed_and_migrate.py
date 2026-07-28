"""Seed agents into DB and copy permanent members to organization_members."""

import sqlite3
import json
import datetime

conn = sqlite3.connect('ecms.db')
cur = conn.cursor()

now = datetime.datetime.now(datetime.timezone.utc).isoformat()

agents = [
    ('agent-ceo','Vikram Sharma','ceo','','leadership',None,'Chief Executive Officer.','["Vision","Strategy","Fundraising","Board Relations"]'),
    ('agent-cto','Priya Mehta','cto','','leadership','agent-ceo','Chief Technology Officer.','["Architecture","Python","Cloud","Security"]'),
    ('agent-cfo','Arjun Nair','cfo','','leadership','agent-ceo','Chief Financial Officer.','["Finance","Budgeting","Compliance","Investor Relations"]'),
    ('agent-em-platform','Rohan Gupta','engineering_manager','','platform','agent-cto','Engineering Manager for Platform.','["Docker","Kubernetes","Terraform","AWS","Prometheus"]'),
    ('agent-tl-platform','Sneha Kapoor','tech_lead','','platform','agent-em-platform','Tech Lead Platform.','["CI/CD","GitHub Actions","Helm","Grafana","ArgoCD"]'),
    ('agent-sr-platform','Amit Joshi','senior_dev','','platform','agent-tl-platform','Senior Platform Engineer.','["Terraform","Vault","Pulumi","Ansible"]'),
    ('agent-jr-platform','Neha Reddy','junior_dev','','platform','agent-sr-platform','Junior Platform Engineer.','["Docker","Linux","Bash","Git"]'),
    ('agent-em-backend','Karan Malhotra','engineering_manager','','backend','agent-cto','Engineering Manager for Backend.','["Python","FastAPI","PostgreSQL","Microservices"]'),
    ('agent-tl-backend','Divya Singh','tech_lead','','backend','agent-em-backend','Tech Lead Backend.','["FastAPI","AsyncIO","PostgreSQL","Redis","Kafka"]'),
    ('agent-sr-backend-1','Rajesh Kumar','senior_dev','','backend','agent-tl-backend','Senior Backend Developer.','["Python","SQLAlchemy","FalkorDB","GraphQL"]'),
    ('agent-sr-backend-2','Ananya Iyer','senior_dev','','backend','agent-tl-backend','Senior Backend Developer.','["JWT","OAuth2","Stripe API","Encryption"]'),
    ('agent-jr-backend','Vikram Patil','junior_dev','','backend','agent-sr-backend-1','Junior Backend Developer.','["Python","FastAPI","pytest","PostgreSQL"]'),
    ('agent-em-frontend','Meera Choudhury','engineering_manager','','frontend','agent-cto','Engineering Manager for Frontend.','["React","Next.js","TypeScript","Design Systems"]'),
    ('agent-tl-frontend','Kunal Shah','tech_lead','','frontend','agent-em-frontend','Tech Lead Frontend.','["React","Tailwind CSS","shadcn/ui","a11y","WebSocket"]'),
    ('agent-sr-frontend','Pooja Verma','senior_dev','','frontend','agent-tl-frontend','Senior Frontend Developer.','["React","Zustand","TanStack Query","Cytoscape","Framer Motion"]'),
    ('agent-jr-frontend','Aakash Tiwari','junior_dev','','frontend','agent-sr-frontend','Junior Frontend Developer.','["React","CSS","TypeScript","Jest"]'),
    ('agent-sr-data','Sanjay Rao','senior_dev','','data','agent-em-backend','Senior Data Engineer.','["Python","Spark","Airflow","Snowflake","dbt"]'),
    ('agent-jr-data','Tanya Deshmukh','junior_dev','','data','agent-sr-data','Junior Data Engineer.','["PostgreSQL","Python","Pandas","Tableau"]'),
    ('agent-sr-qa','Ravi Menon','senior_dev','','qa','agent-em-backend','Senior QA Engineer.','["Selenium","Cypress","pytest","CI/CD","TestRail"]'),
    ('agent-jr-qa','Swati Das','junior_dev','','qa','agent-sr-qa','Junior QA Engineer.','["Test Cases","Bug Tracking","Selenium","Postman"]'),
]

for a in agents:
    cur.execute(
        "INSERT OR IGNORE INTO agents (id, name, role, designation, department, reports_to, role_description, skills, tool_policy, workspace_scope, status, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (a[0], a[1], a[2], a[3], a[4], a[5], a[6], a[7], '{}', '{}', 'active', now, now)
    )

conn.commit()
print(f'Seeded {len(agents)} agents into agents table')

# Copy permanent agents to organization_members
cur.execute("DELETE FROM organization_members")
cur.execute("""
    INSERT OR IGNORE INTO organization_members
        (id, name, designation, role, department, role_description, skills,
         reports_to, status, created_at, updated_at)
    SELECT
        id, name, designation, role, department, role_description, skills,
        reports_to, status, created_at, updated_at
    FROM agents
    WHERE project_id IS NULL
""")
conn.commit()

cur.execute('SELECT count(*) FROM organization_members')
print(f'Organization members: {cur.fetchone()[0]}')

cur.execute('SELECT id, name, department, role FROM organization_members ORDER BY department, role')
for r in cur.fetchall():
    print(f'  {r[0]}: {r[1]} ({r[2]}, {r[3]})')

conn.close()
print('\nDone!')
