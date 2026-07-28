import os, requests, json, sys

BASE = os.environ.get("AEGIS_API_URL", "http://localhost:8000")
AUTH_TOKEN = os.environ.get("AEGIS_AUTH_TOKEN", "")
HEADERS = {"Authorization": f"Bearer {AUTH_TOKEN}"} if AUTH_TOKEN else {}

# ── AegisOS Organization Hierarchy (28 permanent employees) ─────────────────
#
# CEO
# ├── CTO
# │     ├── Director Engineering
# │     │      ├── Backend Manager
# │     │      ├── Frontend Manager
# │     │      ├── Platform Manager
# │     │      ├── QA Manager
# │     │      ├── DevOps Manager
# │     │      └── Data Lead
# │     └── Head of Security
# ├── CPO
# │     ├── Product Management
# │     └── Product Design
# ├── COO
# │     ├── Customer Success
# │     ├── Program Management
# │     └── People Operations
# └── CFO
#       ├── Controller
#       └── Finance

agents = [
    # ── C-Suite (5) ─────────────────────────────────────
    {"id": "agent-ceo", "name": "Vikram Sharma", "role": "ceo", "designation": "Chief Executive Officer", "department": "leadership", "reports_to": None, "role_description": "Sets company vision, leads fundraising, manages key client relationships and board reporting.", "skills": ["Strategy", "Fundraising", "Client Relations", "Product Vision"]},
    {"id": "agent-cto", "name": "Priya Mehta", "role": "cto", "designation": "Chief Technology Officer", "department": "leadership", "reports_to": "agent-ceo", "role_description": "Owns technical architecture, engineering hiring, technology roadmap, and platform reliability.", "skills": ["Architecture", "Python", "Cloud", "System Design"]},
    {"id": "agent-cpo", "name": "Aditya Bose", "role": "cpo", "designation": "Chief Product Officer", "department": "leadership", "reports_to": "agent-ceo", "role_description": "Owns product strategy, discovery, design, positioning, and the AegisOS product roadmap.", "skills": ["Product Strategy", "Market Research", "Roadmapping", "Product-Led Growth"]},
    {"id": "agent-coo", "name": "Leena Krishnan", "role": "coo", "designation": "Chief Operating Officer", "department": "leadership", "reports_to": "agent-ceo", "role_description": "Runs company operations, delivery governance, customer success, and organizational planning.", "skills": ["Operations", "Delivery Governance", "Capacity Planning", "Customer Success"]},
    {"id": "agent-cfo", "name": "Arjun Nair", "role": "cfo", "designation": "Chief Financial Officer", "department": "leadership", "reports_to": "agent-ceo", "role_description": "Manages budgets, vendor negotiations, resource allocation, and financial strategy.", "skills": ["Finance", "Budgeting", "Compliance", "Investor Relations"]},

    # ── Under CTO → Director Engineering (1) ────────────
    {"id": "agent-dir-eng", "name": "Siddharth Mehta", "role": "director_engineering", "designation": "Director of Engineering", "department": "engineering", "reports_to": "agent-cto", "role_description": "Manages all engineering pods. Owns delivery velocity, technical standards, cross-team coordination, and engineering culture.", "skills": ["Engineering Management", "Delivery", "Architecture Reviews", "Hiring"]},

    # ── Under Director Engineering → Backend (5) ────────
    {"id": "agent-lead-backend", "name": "Karan Malhotra", "role": "engineering_manager", "designation": "Backend Manager", "department": "backend", "reports_to": "agent-dir-eng", "role_description": "Leads backend team. Designs APIs, database schema, and owns service reliability.", "skills": ["Python", "FastAPI", "PostgreSQL", "Redis", "Microservices"]},
    {"id": "agent-sr-backend-1", "name": "Divya Singh", "role": "senior_dev", "designation": "Senior Backend Engineer", "department": "backend", "reports_to": "agent-lead-backend", "role_description": "Builds core platform services, authentication flows, and third-party integrations.", "skills": ["Python", "SQLAlchemy", "JWT", "OAuth2"]},
    {"id": "agent-sr-backend-2", "name": "Rajesh Kumar", "role": "senior_dev", "designation": "Senior Backend Engineer", "department": "backend", "reports_to": "agent-lead-backend", "role_description": "Owns search infrastructure, background jobs, and event-driven architecture.", "skills": ["Python", "Kafka", "Elasticsearch", "Celery"]},
    {"id": "agent-mid-backend", "name": "Ananya Iyer", "role": "mid_dev", "designation": "Backend Engineer", "department": "backend", "reports_to": "agent-lead-backend", "role_description": "Develops REST endpoints, writes integration tests, and maintains API documentation.", "skills": ["FastAPI", "pytest", "PostgreSQL", "OpenAPI"]},
    {"id": "agent-jr-backend", "name": "Vikram Patil", "role": "junior_dev", "designation": "Junior Backend Engineer", "department": "backend", "reports_to": "agent-sr-backend-1", "role_description": "Builds CRUD endpoints, writes unit tests, and resolves backlog bugs.", "skills": ["Python", "FastAPI", "SQL", "Git"]},

    # ── Under Director Engineering → Frontend (4) ───────
    {"id": "agent-lead-frontend", "name": "Kunal Shah", "role": "engineering_manager", "designation": "Frontend Manager", "department": "frontend", "reports_to": "agent-dir-eng", "role_description": "Leads frontend architecture, component library, and performance optimization.", "skills": ["React", "TypeScript", "Next.js", "Design Systems"]},
    {"id": "agent-sr-frontend-1", "name": "Pooja Verma", "role": "senior_dev", "designation": "Senior Frontend Engineer", "department": "frontend", "reports_to": "agent-lead-frontend", "role_description": "Builds complex dashboards, real-time collaboration UI, and state management.", "skills": ["React", "Zustand", "WebSocket", "D3.js"]},
    {"id": "agent-sr-frontend-2", "name": "Meera Choudhury", "role": "senior_dev", "designation": "Senior Frontend Engineer", "department": "frontend", "reports_to": "agent-lead-frontend", "role_description": "Owns responsive layouts, accessibility compliance, and cross-browser testing.", "skills": ["React", "Tailwind CSS", "a11y", "Playwright"]},
    {"id": "agent-mid-frontend", "name": "Aakash Tiwari", "role": "mid_dev", "designation": "Frontend Engineer", "department": "frontend", "reports_to": "agent-lead-frontend", "role_description": "Implements UI features from specs, writes component tests, and handles design handoffs.", "skills": ["React", "TypeScript", "CSS", "Jest"]},

    # ── Under Director Engineering → Platform (1) ───────
    {"id": "agent-platform-mgr", "name": "Rohan Gupta", "role": "engineering_manager", "designation": "Platform Manager", "department": "platform", "reports_to": "agent-dir-eng", "role_description": "Manages cloud infrastructure, developer experience, and internal platform tooling.", "skills": ["Docker", "Kubernetes", "Terraform", "AWS", "GitHub Actions"]},

    # ── Under Director Engineering → DevOps (1) ─────────
    {"id": "agent-devops-mgr", "name": "Sneha Kapoor", "role": "engineering_manager", "designation": "DevOps Manager", "department": "devops", "reports_to": "agent-dir-eng", "role_description": "Owns CI/CD pipelines, deployment automation, monitoring, and production reliability.", "skills": ["CI/CD", "Helm", "Prometheus", "Grafana", "ArgoCD"]},

    # ── Under Director Engineering → QA (2) ─────────────
    {"id": "agent-qa-mgr", "name": "Ravi Menon", "role": "quality_engineering_manager", "designation": "QA Manager", "department": "qa", "reports_to": "agent-dir-eng", "role_description": "Owns test strategy, automation framework, and release quality sign-off.", "skills": ["Cypress", "Playwright", "pytest", "CI/CD", "Test Strategy"]},
    {"id": "agent-qa", "name": "Swati Das", "role": "mid_dev", "designation": "QA Engineer", "department": "qa", "reports_to": "agent-qa-mgr", "role_description": "Writes test cases, automates regression suites, and tracks defect metrics.", "skills": ["Selenium", "Postman", "Bug Tracking", "Test Cases"]},

    # ── Under Director Engineering → Data Lead (1) ──────
    {"id": "agent-data-lead", "name": "Sanjay Rao", "role": "tech_lead", "designation": "Data Lead", "department": "data", "reports_to": "agent-dir-eng", "role_description": "Leads data engineering. Builds ETL pipelines, manages analytics warehouse, and creates dashboards.", "skills": ["Python", "SQL", "Airflow", "dbt", "Metabase"]},

    # ── Under Director Engineering → Full-Stack (1) ─────
    {"id": "agent-fullstack", "name": "Amit Joshi", "role": "mid_dev", "designation": "Full-Stack Engineer", "department": "engineering", "reports_to": "agent-platform-mgr", "role_description": "Works across backend and frontend. Builds features end-to-end and handles cross-cutting concerns.", "skills": ["React", "Python", "FastAPI", "PostgreSQL", "TypeScript"]},

    # ── Under CTO → Head of Security (1) ────────────────
    {"id": "agent-security", "name": "Harsh Vardhan", "role": "security_lead", "designation": "Head of Security", "department": "security", "reports_to": "agent-cto", "role_description": "Owns application security, privacy controls, threat management, and compliance readiness.", "skills": ["Security Architecture", "Threat Modeling", "ISO 27001", "AppSec"]},

    # ── Under CPO → Product & Design (2) ────────────────
    {"id": "agent-pm", "name": "Nisha Kulkarni", "role": "product_manager", "designation": "Product Manager", "department": "product", "reports_to": "agent-cpo", "role_description": "Owns product roadmap, user research, feature prioritization, and release planning.", "skills": ["Product Discovery", "User Research", "Agile", "Analytics"]},
    {"id": "agent-designer", "name": "Rhea Sen", "role": "product_designer", "designation": "Product Designer", "department": "design", "reports_to": "agent-cpo", "role_description": "Designs user workflows, maintains the design system, and validates usability through testing.", "skills": ["Figma", "UX Design", "Prototyping", "Design Systems"]},

    # ── Under COO → Operations (3) ──────────────────────
    {"id": "agent-cs", "name": "Anjali Desai", "role": "customer_success_head", "designation": "Head of Customer Success", "department": "customer_success", "reports_to": "agent-coo", "role_description": "Manages client onboarding, support escalations, adoption, and renewal health.", "skills": ["Customer Success", "Onboarding", "Communication", "CRM"]},
    {"id": "agent-program-mgr", "name": "Aparna Nandakumar", "role": "program_manager", "designation": "Program Manager", "department": "delivery_operations", "reports_to": "agent-coo", "role_description": "Coordinates strategic programs, dependencies, risks, and executive reporting.", "skills": ["Program Management", "Risk Management", "Planning", "Executive Reporting"]},
    {"id": "agent-people", "name": "Kavya Rao", "role": "people_operations_head", "designation": "Head of People Operations", "department": "people_operations", "reports_to": "agent-coo", "role_description": "Owns talent systems, performance, culture, learning, and employee experience.", "skills": ["People Strategy", "Performance", "Culture", "Learning"]},

    # ── Under CFO → Finance (2) ─────────────────────────
    {"id": "agent-controller", "name": "Shreya Mukherjee", "role": "financial_controller", "designation": "Financial Controller", "department": "finance", "reports_to": "agent-cfo", "role_description": "Owns financial controls, reporting, planning cycles, and operational accounting.", "skills": ["Financial Controls", "FP&A", "Accounting", "Reporting"]},
    {"id": "agent-finance-analyst", "name": "Naveen Pillai", "role": "finance_analyst", "designation": "Finance Analyst", "department": "finance", "reports_to": "agent-controller", "role_description": "Builds forecasts, unit economics, management reporting, and investment analysis.", "skills": ["Forecasting", "Unit Economics", "Excel", "Financial Modeling"]},
]

seed_ids = {a["id"] for a in agents}

# ── Create / Update ─────────────────────────────────────────────────────────
created = 0
updated = 0
skipped = 0
errors = []

for a in agents:
    try:
        r = requests.post(f"{BASE}/agents", json=a, headers=HEADERS, timeout=10)
        if r.status_code in (200, 201):
            created += 1
            print(f"  CREATED {a['name']} ({a['role']}, {a['department']})")
        elif r.status_code == 409:
            existing = requests.get(f"{BASE}/agents/{a['id']}", headers=HEADERS, timeout=10)
            if existing.status_code == 200 and existing.json().get("project_id"):
                skipped += 1
                print(f"  SKIPPED {a['name']} (has project_id, not modifying)")
                continue
            update_body = {key: value for key, value in a.items() if key != "id"}
            update_body["status"] = "active"
            update_response = requests.put(f"{BASE}/agents/{a['id']}", json=update_body, headers=HEADERS, timeout=10)
            if update_response.status_code == 200:
                updated += 1
                print(f"  UPDATED {a['name']} ({a['role']}, {a['department']})")
            else:
                err = update_response.json().get("detail", update_response.text)
                errors.append(f"{a['name']}: {err}")
                print(f"  ERROR {a['name']}: {err}")
        else:
            err = r.json().get("detail", r.text)
            errors.append(f"{a['name']}: {err}")
            print(f"  ERROR {a['name']}: {err}")
    except Exception as e:
        errors.append(f"{a['name']}: {e}")
        print(f"  ERROR {a['name']}: {e}")

# ── Cleanup: delete agents no longer in seed (only if project_id is null)
deleted = 0
try:
    all_agents = requests.get(f"{BASE}/agents", headers=HEADERS, timeout=10).json()
    for existing in all_agents:
        eid = existing["id"]
        if eid not in seed_ids and existing.get("project_id") is None:
            r = requests.delete(f"{BASE}/agents/{eid}", headers=HEADERS, timeout=10)
            if r.status_code == 200 and r.json().get("deleted"):
                deleted += 1
                print(f"  DELETED {existing['name']} ({eid})")
            else:
                print(f"  WARN could not delete {eid}: {r.status_code}")
except Exception as e:
    print(f"  WARN cleanup failed: {e}")

print(f"\nCreated: {created} · Updated: {updated} · Skipped: {skipped} · Deleted: {deleted} · Total seed: {len(agents)}")
if errors:
    print(f"Errors: {len(errors)}")
