"""
Rich demo seed data for SmartEscrow.

Populates a realistic two-sided marketplace: contributors across every category,
multiple organizations with several open roles each, live applications,
active engagements with timesheets, funded wallets, saved demo cards, blocked
escrow holds, released payouts, and matching audit-log + wallet-transaction
records. Runs once (guarded by the `meta.seeded` flag).
"""
from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from app.marketplace import ai, db

DEMO_PASSWORD = "Password123!"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ago(**kwargs) -> str:
    return (datetime.now(timezone.utc) - timedelta(**kwargs)).isoformat(timespec="seconds")


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def _hash(password: str) -> str:
    salt = secrets.token_hex(8)
    return f"{salt}${hashlib.sha256(f'{salt}:{password}'.encode()).hexdigest()}"


def _hue(name: str) -> int:
    return (hash(name) % 360 + 360) % 360


def _audit(actor_id, actor_name, action, entity_type, entity_id, detail, created_at):
    category = action.split(".")[0] if "." in action else "general"
    db.execute(
        "INSERT INTO operations (user_id, user_name, action, category, entity_type, entity_id, details, created_at) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (actor_id, actor_name, action, category, entity_type, entity_id, db.dumps(detail), created_at),
    )


def seed_if_empty() -> None:
    if db.is_seeded():
        return
    _build()
    db.mark_seeded()


def _build() -> None:
    # Track wallet balances locally so transactions stay consistent.
    avail: dict[str, float] = {}
    blocked: dict[str, float] = {}
    names: dict[str, str] = {}

    def _uname(email):
        return email.split("@")[0].lower()

    def add_contributor(email, name, title, rate, years, location, country, skills, bio,
                        experiences, achievements, portfolio, rating, completed, github, services, phone=""):
        uid = _id("usr")
        names[uid] = name
        resume = (
            f"{name} — {title}\n{location} · {years} years experience\n\n"
            f"SUMMARY\n{bio}\n\nSKILLS\n{', '.join(skills)}\n\nEXPERIENCE\n"
            + "\n".join(f"- {e['role']}, {e['company']} ({e['period']}): {e['summary']}" for e in experiences)
            + "\n\nACHIEVEMENTS\n" + "\n".join(f"- {a}" for a in achievements)
        )
        db.execute(
            """INSERT INTO users (
                id,email,username,phone,password_hash,full_name,role,active_mode,is_freelancer,is_employer,firm_verified,
                email_verified,phone_verified,title,headline,bio,location,country_code,
                hourly_rate_usd,years_experience,availability,github_username,rating,completed_jobs,
                avatar_hue,skills,services,experiences,achievements,portfolio,languages,
                resume_text,resume_filename,resume_updated_at,created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (uid, email, _uname(email), phone, _hash(DEMO_PASSWORD), name, "contributor", "freelancer", 1, 0, 0,
             1, 1, title, title, bio, location, country,
             rate, years, "available", github, rating, completed, _hue(name),
             db.dumps(skills), db.dumps(services), db.dumps(experiences), db.dumps(achievements),
             db.dumps(portfolio), db.dumps(["English"]),
             resume, f"{_uname(email)}_resume.pdf", _ago(days=10), _ago(days=years * 8 + 20)),
        )
        avail[uid] = 0.0
        blocked[uid] = 0.0
        return uid

    def add_client(email, name, company, size, industry, website, bio, phone=""):
        uid = _id("usr")
        names[uid] = company
        db.execute(
            """INSERT INTO users (
                id,email,username,phone,password_hash,full_name,role,active_mode,is_freelancer,is_employer,firm_verified,
                firm_reg_number,firm_work_email,email_verified,phone_verified,
                headline,bio,location,country_code,
                company_name,company_size,industry,website,rating,jobs_posted,avatar_hue,
                skills,services,experiences,achievements,portfolio,languages,created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (uid, email, _uname(email), phone, _hash(DEMO_PASSWORD), name, "client", "employer", 0, 1, 1,
             f"REG-{abs(hash(company)) % 900000 + 100000}", email, 1, 1,
             f"{company} — {industry}", bio, "Global", "US",
             company, size, industry, website, 4.8, 0, _hue(company),
             db.dumps([]), db.dumps([]), db.dumps([]), db.dumps([]), db.dumps([]), db.dumps(["English"]),
             _ago(days=150)),
        )
        avail[uid] = 0.0
        blocked[uid] = 0.0
        return uid

    # ---------------------- Contributors (12) ---------------------- #
    c_ava = add_contributor(
        "ava.chen@smartescrow.io", "Ava Chen", "Senior Full-Stack Engineer", 75, 8, "Singapore", "SG",
        ["Python", "FastAPI", "React", "Next.js", "PostgreSQL", "AWS", "TypeScript"],
        "Full-stack engineer specializing in high-concurrency fintech backends and enterprise React dashboards. "
        "I ship production systems with clean architecture and strong test coverage.",
        [{"company": "Stripe", "role": "Senior Engineer", "period": "2021–2024", "summary": "Payment orchestration at scale."},
         {"company": "Grab", "role": "Backend Engineer", "period": "2018–2021", "summary": "Wallet & ledger systems across SEA."}],
        ["AWS Certified Solutions Architect", "Top 1% code review score"],
        [{"title": "Ledger API Platform", "url": "https://github.com", "summary": "Double-entry ledger with gRPC."}],
        4.9, 34, "avachen",
        [{"title": "Backend architecture & API design", "rate": 90}, {"title": "React/Next.js dashboard build", "rate": 75}],
    )
    c_marcus = add_contributor(
        "marcus.bauer@smartescrow.io", "Marcus Bauer", "Backend Engineer (Go / Rust)", 72, 7, "Berlin", "DE",
        ["Go", "Rust", "gRPC", "PostgreSQL", "Kubernetes", "Microservices", "Architecture"],
        "Systems-focused backend engineer building fast, reliable microservices and APIs with Go and Rust.",
        [{"company": "Zalando", "role": "Senior Backend Engineer", "period": "2020–2024", "summary": "High-throughput order services."}],
        ["Go contributor", "Cut p99 latency by 40%"],
        [{"title": "gRPC Service Mesh", "url": "https://github.com", "summary": "Reference microservice stack."}],
        4.7, 22, "marcusb",
        [{"title": "Microservice backend build", "rate": 85}, {"title": "API performance tuning", "rate": 72}],
    )
    c_yuki = add_contributor(
        "yuki.tanaka@smartescrow.io", "Yuki Tanaka", "Frontend Engineer (React)", 68, 6, "Tokyo", "JP",
        ["React", "Next.js", "TypeScript", "Tailwind", "CSS", "HTML", "UI"],
        "Frontend engineer crafting fast, accessible interfaces and design systems with React and Next.js.",
        [{"company": "Mercari", "role": "Frontend Engineer", "period": "2020–2024", "summary": "Rebuilt web marketplace UI."}],
        ["Core Web Vitals all green", "Open-source component library 3k★"],
        [{"title": "Realtime Dashboard UI", "url": "https://github.com", "summary": "Next.js + WebSockets."}],
        4.8, 26, "yukidev",
        [{"title": "Next.js frontend build", "rate": 78}, {"title": "Design system engineering", "rate": 68}],
    )
    c_sofia = add_contributor(
        "sofia.rossi@smartescrow.io", "Sofia Rossi", "Frontend / UI Engineer", 60, 5, "Milan", "IT",
        ["React", "TypeScript", "Tailwind", "CSS", "Figma", "UI", "HTML"],
        "UI-focused frontend engineer bridging design and code to deliver pixel-perfect, performant interfaces.",
        [{"company": "Bending Spoons", "role": "Frontend Engineer", "period": "2021–2024", "summary": "Consumer app web surfaces."}],
        ["Awwwards nominee"],
        [{"title": "Marketing Site System", "url": "https://github.com", "summary": "Reusable landing blocks."}],
        4.6, 18, "sofiar",
        [{"title": "Landing page development", "rate": 65}, {"title": "UI component build", "rate": 60}],
    )
    c_diego = add_contributor(
        "diego.m@smartescrow.io", "Diego Morales", "ML / LLM Engineer", 95, 7, "Remote — Mexico City", "MX",
        ["Python", "PyTorch", "LLM", "NLP", "AI", "Machine Learning", "Docker", "GCP"],
        "Applied ML engineer focused on LLM systems, retrieval pipelines, and evaluation. I turn research into "
        "reliable, cost-efficient production inference.",
        [{"company": "Hugging Face", "role": "ML Engineer", "period": "2022–2024", "summary": "Fine-tuning & eval tooling."},
         {"company": "MercadoLibre", "role": "Data Scientist", "period": "2019–2022", "summary": "Fraud models, -23% chargebacks."}],
        ["NeurIPS workshop paper", "Kaggle Grandmaster"],
        [{"title": "RAG Evaluation Toolkit", "url": "https://github.com", "summary": "Open-source eval harness."}],
        4.8, 21, "diegoml",
        [{"title": "LLM integration & RAG pipeline", "rate": 120}, {"title": "ML model training & evaluation", "rate": 95}],
    )
    c_aisha = add_contributor(
        "aisha.khan@smartescrow.io", "Aisha Khan", "Data Scientist", 70, 6, "Dubai", "AE",
        ["Python", "Data", "Analytics", "Machine Learning", "SQL", "ETL", "Spark"],
        "Data scientist delivering forecasting, analytics, and ML pipelines that drive measurable business value.",
        [{"company": "Careem", "role": "Data Scientist", "period": "2020–2024", "summary": "Demand forecasting models."}],
        ["Published forecasting benchmark"],
        [{"title": "Forecasting Toolkit", "url": "https://github.com", "summary": "Time-series pipeline."}],
        4.7, 19, "aishadata",
        [{"title": "Data pipeline & ETL build", "rate": 80}, {"title": "Analytics & forecasting", "rate": 70}],
    )
    c_priya = add_contributor(
        "priya.r@smartescrow.io", "Priya Raman", "Product Designer (UI/UX)", 55, 6, "Bangalore", "IN",
        ["Figma", "UI", "UX", "Design", "Tailwind", "React", "HTML", "CSS"],
        "Product designer bridging research and polished front-end. I design enterprise dashboards and design "
        "systems that engineers love to build.",
        [{"company": "Atlassian", "role": "Senior Product Designer", "period": "2020–2024", "summary": "Jira dashboard design system."}],
        ["Awwwards honorable mention", "Design system adopted org-wide"],
        [{"title": "Enterprise Design System", "url": "https://figma.com", "summary": "120+ components."}],
        4.9, 28, "priyadesign",
        [{"title": "Design system & UI kit", "rate": 65}, {"title": "UX audit & redesign", "rate": 55}],
    )
    c_noah = add_contributor(
        "noah.w@smartescrow.io", "Noah Williams", "UX Researcher / Designer", 58, 7, "Austin", "US",
        ["UX", "Design", "Figma", "UI", "Research"],
        "UX researcher and designer who grounds product decisions in real user insight and clean interaction design.",
        [{"company": "Dell", "role": "UX Researcher", "period": "2019–2024", "summary": "Enterprise research program."}],
        ["NN/g UX certified"],
        [{"title": "Research Ops Playbook", "url": "https://figma.com", "summary": "Reusable research kit."}],
        4.6, 15, "noahux",
        [{"title": "UX research study", "rate": 68}, {"title": "Usability testing", "rate": 58}],
    )
    c_sam = add_contributor(
        "sam.okafor@smartescrow.io", "Sam Okafor", "DevOps / SRE Engineer", 80, 9, "Remote — Lagos", "NG",
        ["Kubernetes", "Docker", "Terraform", "AWS", "CI/CD", "DevOps", "SRE", "Go"],
        "Reliability-focused platform engineer. I build secure, observable infrastructure and automate delivery "
        "pipelines for fast-moving teams.",
        [{"company": "Cloudflare", "role": "SRE", "period": "2021–2024", "summary": "Multi-region Kubernetes platforms."}],
        ["CKA + CKS certified", "Cut deploy times 60%"],
        [{"title": "GitOps Platform Blueprint", "url": "https://github.com", "summary": "Terraform + ArgoCD."}],
        4.7, 19, "samsre",
        [{"title": "Kubernetes platform setup", "rate": 95}, {"title": "CI/CD pipeline automation", "rate": 80}],
    )
    c_lena = add_contributor(
        "lena.k@smartescrow.io", "Lena Kowalski", "Security Engineer", 100, 10, "Berlin", "DE",
        ["Security", "Pentest", "Cryptography", "Python", "Go", "API", "Architecture"],
        "Offensive + defensive security engineer. I harden APIs, run threat models, and deliver actionable "
        "pentest reports for regulated industries.",
        [{"company": "Trail of Bits", "role": "Security Engineer", "period": "2019–2024", "summary": "Fintech & infra audits."}],
        ["OSCP + OSWE", "Disclosed 12 CVEs"],
        [{"title": "API Threat Model Template", "url": "https://github.com", "summary": "Reusable STRIDE kit."}],
        5.0, 24, "lenasec",
        [{"title": "Security audit & pentest", "rate": 125}, {"title": "Threat modeling workshop", "rate": 100}],
    )
    c_tomas = add_contributor(
        "tomas.silva@smartescrow.io", "Tomás Silva", "Mobile Engineer (iOS/Android)", 65, 6, "Lisbon", "PT",
        ["Swift", "Kotlin", "Flutter", "React Native", "Mobile", "iOS", "Android"],
        "Cross-platform mobile engineer delivering smooth, native-feeling apps with strong attention to "
        "performance and UX detail.",
        [{"company": "Revolut", "role": "Mobile Engineer", "period": "2020–2024", "summary": "Card & payments flows, 10M+ users."}],
        ["App featured on App Store", "4.8★ average app rating"],
        [{"title": "Fintech Wallet App", "url": "https://github.com", "summary": "Flutter + biometric auth."}],
        4.6, 16, "tomasmobile",
        [{"title": "Mobile app development", "rate": 80}, {"title": "App performance optimization", "rate": 65}],
    )
    c_hannah = add_contributor(
        "hannah.lee@smartescrow.io", "Hannah Lee", "QA / Test Automation Engineer", 52, 5, "Seoul", "KR",
        ["Testing", "QA", "Selenium", "Playwright", "Python", "CI/CD"],
        "QA automation engineer building reliable end-to-end test suites and CI pipelines that catch bugs early.",
        [{"company": "Coupang", "role": "QA Engineer", "period": "2021–2024", "summary": "E2E automation for checkout."}],
        ["ISTQB certified"],
        [{"title": "E2E Test Framework", "url": "https://github.com", "summary": "Playwright + CI."}],
        4.5, 14, "hannahqa",
        [{"title": "Test automation setup", "rate": 60}, {"title": "QA audit & strategy", "rate": 52}],
    )

    # ---------------------- Indian contributors ---------------------- #
    c_arjun = add_contributor(
        "arjun.nair@smartescrow.io", "Arjun Nair", "Senior Backend Engineer", 62, 8, "Chennai", "IN",
        ["Java", "Spring", "Python", "PostgreSQL", "Microservices", "AWS", "Architecture"],
        "Backend engineer specializing in resilient Java/Spring microservices and payment integrations for "
        "high-scale Indian fintech products.",
        [{"company": "Razorpay", "role": "Senior Engineer", "period": "2020–2024", "summary": "Payment gateway core services."},
         {"company": "Freshworks", "role": "Backend Engineer", "period": "2017–2020", "summary": "SaaS billing platform."}],
        ["AWS Certified", "Scaled payments to 10k TPS"],
        [{"title": "Payments Core Service", "url": "https://github.com", "summary": "Idempotent Spring Boot APIs."}],
        4.8, 30, "arjunnair",
        [{"title": "Spring Boot backend build", "rate": 75}, {"title": "Payment integration", "rate": 62}],
        phone="+91 98840 12345",
    )
    c_ananya = add_contributor(
        "ananya.reddy@smartescrow.io", "Ananya Reddy", "Frontend Engineer (React)", 55, 5, "Hyderabad", "IN",
        ["React", "Next.js", "TypeScript", "Tailwind", "UI", "CSS", "HTML"],
        "Frontend engineer crafting clean, responsive React interfaces with a sharp eye for accessibility and detail.",
        [{"company": "Swiggy", "role": "Frontend Engineer", "period": "2021–2024", "summary": "Consumer web ordering flows."}],
        ["GDE nominee", "Shipped PWA used by millions"],
        [{"title": "Design System in React", "url": "https://github.com", "summary": "Accessible component kit."}],
        4.7, 22, "ananyar",
        [{"title": "React frontend build", "rate": 65}, {"title": "UI component engineering", "rate": 55}],
        phone="+91 99490 23456",
    )
    c_rohit = add_contributor(
        "rohit.sharma@smartescrow.io", "Rohit Sharma", "DevOps / Cloud Engineer", 58, 7, "Pune", "IN",
        ["Kubernetes", "Docker", "Terraform", "AWS", "CI/CD", "DevOps", "Python"],
        "Cloud and DevOps engineer automating secure, scalable infrastructure and delivery pipelines for product teams.",
        [{"company": "Infosys", "role": "Cloud Engineer", "period": "2018–2024", "summary": "Enterprise cloud migrations."}],
        ["CKA certified", "AWS Solutions Architect"],
        [{"title": "Terraform Modules Library", "url": "https://github.com", "summary": "Reusable IaC."}],
        4.6, 20, "rohitdevops",
        [{"title": "Cloud infrastructure setup", "rate": 70}, {"title": "CI/CD automation", "rate": 58}],
        phone="+91 98230 34567",
    )
    c_meera = add_contributor(
        "meera.iyer@smartescrow.io", "Meera Iyer", "Data Scientist / ML Engineer", 60, 6, "Bengaluru", "IN",
        ["Python", "Machine Learning", "AI", "Data", "Analytics", "SQL", "PyTorch"],
        "Data scientist building ML and analytics solutions that turn messy data into clear, actionable decisions.",
        [{"company": "Flipkart", "role": "Data Scientist", "period": "2020–2024", "summary": "Recommendation & pricing models."}],
        ["Kaggle Expert", "Published recommender benchmark"],
        [{"title": "Recommender Toolkit", "url": "https://github.com", "summary": "Production ranking pipeline."}],
        4.8, 24, "meeraml",
        [{"title": "ML model development", "rate": 72}, {"title": "Analytics & insights", "rate": 60}],
        phone="+91 99020 45678",
    )

    contributors = [c_ava, c_marcus, c_yuki, c_sofia, c_diego, c_aisha, c_priya, c_noah, c_sam, c_lena,
                    c_tomas, c_hannah, c_arjun, c_ananya, c_rohit, c_meera]

    # ---------------------- Clients (5) ---------------------- #
    cl_apex = add_client("client@apexlabs.io", "Jordan Blake", "Apex Labs", "201-500", "Financial Technology",
                         "https://apexlabs.io", "Institutional-grade trading infrastructure. We hire elite engineers for high-stakes delivery.",
                         phone="+1 415 555 0101")
    cl_nova = add_client("hiring@novaworks.io", "Mara Lindqvist", "NovaWorks", "51-200", "SaaS / Enterprise",
                         "https://novaworks.io", "Enterprise SaaS company modernizing our product suite with top external talent.",
                         phone="+46 70 555 0102")
    cl_north = add_client("talent@northlane.com", "Ethan Park", "Northlane GCC", "1000+", "Global Capability Center",
                          "https://northlane.com", "Global Capability Center scaling multiple engineering pods across security, data, and platform.",
                          phone="+1 206 555 0103")
    cl_helix = add_client("jobs@helixhealth.io", "Dr. Amara Osei", "Helix Health", "501-1000", "HealthTech",
                          "https://helixhealth.io", "HealthTech building compliant, patient-centric digital products with world-class contributors.",
                          phone="+1 617 555 0104")
    cl_vertex = add_client("recruiting@vertexdyn.com", "Liam Chen", "Vertex Dynamics", "1000+", "Enterprise / MNC",
                           "https://vertexdyn.com", "Global enterprise modernizing core platforms across data, cloud, and backend.",
                           phone="+1 408 555 0105")
    cl_infytech = add_client("careers@infytechindia.com", "Kavya Menon", "InfyTech India", "1000+", "IT Services / GCC",
                             "https://infytechindia.com", "India-based global capability center delivering engineering pods for enterprise clients worldwide.",
                             phone="+91 80 4555 0106")

    # ---------------------- Jobs (15) ---------------------- #
    def add_job(client_id, title, category, desc, skills, rate_min, rate_max, level, hours, duration, days_ago):
        jid = _id("job")
        db.execute(
            """INSERT INTO jobs (
                id,client_id,company_name,title,category,description,skills_required,engagement_type,
                hourly_rate_min,hourly_rate_max,experience_level,location,hours_per_week,duration,status,ai,created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (jid, client_id, names[client_id], title, category, desc, db.dumps(skills), "hourly",
             rate_min, rate_max, level, "Remote", hours, duration, "open",
             db.dumps(ai.analyze_job(title, desc, skills)), _ago(days=days_ago)),
        )
        db.execute("UPDATE users SET jobs_posted = jobs_posted + 1 WHERE id = ?", (client_id,))
        return jid

    j_backend1 = add_job(cl_apex, "Senior Backend Engineer — Payments Ledger", "Backend",
        "We are building a double-entry payments ledger that must handle high-concurrency settlement with strict "
        "correctness guarantees. You will design async FastAPI services, model transactional data in PostgreSQL, and "
        "expose clean gRPC and REST APIs. Strong experience with idempotency and event-driven architecture is essential.",
        ["Python", "FastAPI", "PostgreSQL", "gRPC", "Architecture"], 70, 110, "Senior", 30, "3-6 months", 2)
    j_backend2 = add_job(cl_vertex, "Go Microservices Engineer — Core Platform", "Backend",
        "Join our platform team to build high-throughput Go microservices. You will design service boundaries, "
        "implement gRPC APIs, and ensure reliability under load. Experience with Kubernetes and observability required.",
        ["Go", "gRPC", "Kubernetes", "Microservices", "PostgreSQL"], 65, 105, "Senior", 40, "6-12 months", 7)
    j_frontend1 = add_job(cl_apex, "React/Next.js Frontend Engineer — Trading UI", "Frontend",
        "Build a fast, real-time trading dashboard in Next.js with TypeScript and Tailwind. You will implement complex "
        "data tables, WebSocket streaming, and accessible components. A strong eye for performance and UX polish is essential.",
        ["React", "Next.js", "TypeScript", "Tailwind", "CSS"], 65, 100, "Senior", 30, "3-5 months", 5)
    j_frontend2 = add_job(cl_nova, "Frontend Engineer — Design System", "Frontend",
        "Help us build and maintain a company-wide design system in React. You will create reusable, accessible "
        "components, document them, and partner with designers to keep our product cohesive.",
        ["React", "TypeScript", "Tailwind", "UI", "CSS"], 55, 90, "Mid-level", 25, "2-4 months", 3)
    j_ai1 = add_job(cl_nova, "LLM Integration Engineer — AI Features", "AI / ML",
        "Help us ship AI features across our SaaS product. You will integrate LLMs for summarization and "
        "recommendations, build retrieval pipelines, and set up evaluation so quality stays high while cost stays low. "
        "Experience with RAG and production inference is required. Bonus for local model experience with Ollama.",
        ["Python", "LLM", "NLP", "AI", "Docker"], 90, 140, "Senior", 25, "2-4 months", 4)
    j_ai2 = add_job(cl_helix, "ML Engineer — Fraud & Risk Models", "AI / ML",
        "Build and deploy machine-learning models for fraud and risk scoring in a regulated healthcare-payments "
        "context. You will own feature engineering, training, evaluation, and monitoring in production.",
        ["Python", "Machine Learning", "AI", "Data", "Docker"], 85, 130, "Senior", 30, "3-6 months", 6)
    j_design1 = add_job(cl_nova, "Product Designer — Enterprise Dashboard", "Design",
        "Redesign our enterprise analytics dashboard into a clean, modern experience. You will run a quick UX audit, "
        "build a cohesive design system in Figma, and partner closely with React engineers to ship.",
        ["Figma", "UI", "UX", "Design", "React"], 45, 80, "Mid-level", 20, "1-3 months", 1)
    j_design2 = add_job(cl_helix, "UX Researcher — Patient Experience", "Design",
        "Lead UX research for our patient-facing products. You will plan and run studies, synthesize insights, and "
        "translate findings into clear design direction for a compliant, accessible experience.",
        ["UX", "Research", "Design", "Figma"], 50, 85, "Mid-level", 20, "2-3 months", 8)
    j_devops1 = add_job(cl_north, "Kubernetes Platform Engineer (GCC Pod)", "DevOps",
        "Join a Global Capability Center pod to build a secure, multi-region Kubernetes platform. You will automate "
        "infrastructure with Terraform, set up GitOps delivery, and improve observability for a long-term engagement.",
        ["Kubernetes", "Terraform", "AWS", "CI/CD", "DevOps"], 75, 110, "Senior", 40, "6-12 months", 6)
    j_devops2 = add_job(cl_vertex, "CI/CD Automation Engineer", "DevOps",
        "Modernize our delivery pipelines. You will build CI/CD automation, containerize services, and reduce lead "
        "time to production with strong DevOps practices.",
        ["CI/CD", "Docker", "DevOps", "AWS", "Go"], 65, 100, "Mid-level", 30, "3-6 months", 9)
    j_sec1 = add_job(cl_north, "Application Security Engineer — API Hardening", "Security",
        "We need a security engineer to threat-model and harden our public APIs. Deliverables include a STRIDE threat "
        "model, a full pentest, and a prioritized remediation plan. Experience auditing fintech or regulated systems preferred.",
        ["Security", "Pentest", "Cryptography", "API"], 100, 150, "Lead", 20, "1-2 months", 3)
    j_sec2 = add_job(cl_apex, "Cloud Security Audit — AWS", "Security",
        "Audit our AWS environment for misconfigurations and compliance gaps. Provide a prioritized remediation plan "
        "and harden IAM, networking, and data protection controls.",
        ["Security", "AWS", "Cryptography", "DevOps"], 90, 140, "Senior", 15, "1-2 months", 10)
    j_mobile1 = add_job(cl_helix, "Mobile Engineer — iOS / Flutter", "Mobile",
        "Build a patient companion mobile app with Flutter. You will implement secure auth, offline sync, and a smooth, "
        "accessible UI across iOS and Android.",
        ["Flutter", "Mobile", "iOS", "Android", "Swift"], 60, 95, "Senior", 30, "3-5 months", 4)
    j_data1 = add_job(cl_vertex, "Data Pipeline Engineer — Analytics", "Data",
        "Design and build reliable data pipelines feeding our analytics platform. You will own ETL, data quality, and "
        "orchestration with modern tooling.",
        ["Python", "ETL", "Spark", "SQL", "Data"], 65, 100, "Senior", 30, "3-6 months", 5)
    j_qa1 = add_job(cl_nova, "QA Automation Engineer", "QA",
        "Own end-to-end test automation for our SaaS product. You will build Playwright suites, integrate them into CI, "
        "and improve release confidence.",
        ["Testing", "QA", "Playwright", "CI/CD", "Python"], 45, 80, "Mid-level", 25, "2-4 months", 2)
    j_backend3 = add_job(cl_infytech, "Java / Spring Backend Engineer — GCC Pod", "Backend",
        "Join our India-based GCC pod building enterprise Java/Spring microservices and payment integrations for a "
        "global client. Strong experience with Spring Boot, PostgreSQL, and clean API design required.",
        ["Java", "Spring", "PostgreSQL", "Microservices", "AWS"], 55, 90, "Senior", 40, "6-12 months", 2)
    j_data2 = add_job(cl_infytech, "ML / Data Scientist — Recommendations", "AI / ML",
        "Build recommendation and analytics models for a large e-commerce client. You will own feature engineering, "
        "model training, and evaluation with strong Python and ML fundamentals.",
        ["Python", "Machine Learning", "AI", "Data", "SQL"], 55, 90, "Senior", 30, "3-6 months", 3)

    # ---------------------- Applications ---------------------- #
    def add_application(job_id, contributor_id, rate, status, note, days_ago):
        aid = _id("app")
        db.execute(
            "INSERT INTO applications (id,job_id,contributor_id,proposed_hourly_rate,status,cover_letter,created_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (aid, job_id, contributor_id, rate, status, note, _ago(days=days_ago)),
        )
        _audit(contributor_id, names[contributor_id], "application.submit", "application", aid,
               {"job_id": job_id, "rate": rate}, _ago(days=days_ago))
        return aid

    add_application(j_backend1, c_ava, 85, "shortlisted",
                    "I built Stripe's payment orchestration and can design your ledger with strong correctness guarantees.", 1)
    add_application(j_backend1, c_marcus, 80, "submitted",
                    "Go/Rust systems engineer — I can deliver a fast, correct ledger service with clean gRPC APIs.", 1)
    add_application(j_frontend1, c_yuki, 82, "interview",
                    "I rebuilt Mercari's marketplace UI and love real-time dashboards. Performance is my obsession.", 2)
    add_application(j_frontend2, c_sofia, 70, "submitted",
                    "Design-systems frontend engineer — happy to start with a component audit and Storybook setup.", 0)
    add_application(j_ai1, c_diego, 120, "interview",
                    "LLM systems are my specialty — I shipped evaluation tooling at Hugging Face.", 2)
    add_application(j_ai2, c_aisha, 110, "shortlisted",
                    "I built fraud models at Careem reducing chargebacks significantly. Ready for your risk scope.", 3)
    add_application(j_design1, c_priya, 60, "submitted",
                    "I design enterprise dashboards and design systems. Happy to start with a quick UX audit.", 0)
    add_application(j_design2, c_noah, 72, "submitted",
                    "Enterprise UX researcher — I can stand up a lean research program fast.", 1)
    add_application(j_sec1, c_lena, 135, "offer",
                    "OSCP/OSWE certified with 12 disclosed CVEs. I can deliver a STRIDE model and full pentest.", 3)
    add_application(j_mobile1, c_tomas, 85, "submitted",
                    "Flutter engineer from Revolut — secure auth and offline sync are right in my wheelhouse.", 1)
    add_application(j_qa1, c_hannah, 60, "shortlisted",
                    "I build Playwright E2E suites wired into CI. I can raise your release confidence quickly.", 1)
    add_application(j_data1, c_aisha, 85, "submitted",
                    "Data engineer/scientist — I can own your ETL and data-quality end to end.", 2)
    add_application(j_backend3, c_arjun, 72, "shortlisted",
                    "Ex-Razorpay engineer — Spring Boot microservices and payment integrations are my core strength.", 1)
    add_application(j_backend1, c_arjun, 75, "submitted",
                    "I've scaled payments to 10k TPS. Happy to bring that rigor to your ledger.", 1)
    add_application(j_frontend2, c_ananya, 60, "interview",
                    "Ex-Swiggy frontend engineer — I build accessible React design systems used at scale.", 2)
    add_application(j_devops2, c_rohit, 65, "submitted",
                    "Cloud/DevOps engineer — I can modernize your pipelines with Terraform and GitOps.", 1)
    add_application(j_data2, c_meera, 65, "shortlisted",
                    "Ex-Flipkart data scientist — recommendation and ranking models are exactly my area.", 1)

    # ---------------------- Wallets, cards, engagements, escrow, payments ---------------------- #
    def set_wallet(uid):
        wid = _id("wal")
        db.execute(
            "INSERT INTO wallets (id,user_id,available_balance,blocked_balance,currency,created_at) VALUES (?,?,?,?,?,?)",
            (wid, uid, round(avail[uid], 2), round(blocked[uid], 2), "USD", _ago(days=120)),
        )
        return wid

    wallet_ids: dict[str, str] = {}

    def wtx(uid, tx_type, amount, ref, note, days_ago):
        db.execute(
            "INSERT INTO wallet_transactions (id,wallet_id,user_id,type,amount,available_after,blocked_after,ref,note,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (_id("wtx"), wallet_ids[uid], uid, tx_type, amount, round(avail[uid], 2), round(blocked[uid], 2),
             ref, note, _ago(days=days_ago)),
        )

    def add_card(uid, brand, last4, exp_m, exp_y, holder, default):
        db.execute(
            "INSERT INTO payment_methods (id,user_id,brand,last4,exp_month,exp_year,holder_name,is_default,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (_id("pm"), uid, brand, last4, exp_m, exp_y, holder, default, _ago(days=100)),
        )

    # Seed client deposits (available balances) before blocking escrow.
    client_deposits = {cl_apex: 60000, cl_nova: 40000, cl_north: 90000, cl_helix: 35000, cl_vertex: 75000, cl_infytech: 50000}
    for cid, amount in client_deposits.items():
        avail[cid] = float(amount)

    # Build active engagements with escrow + payouts.
    def add_engagement(job_id, client_id, contributor_id, title, rate, weeks, days_ago):
        eid = _id("eng")
        total_hours = 0
        db.execute(
            "INSERT INTO engagements (id,job_id,client_id,contributor_id,title,hourly_rate,hours_logged,status,started_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (eid, job_id, client_id, contributor_id, title, rate, 0, "active", _ago(days=days_ago)),
        )
        _audit(client_id, names[client_id], "engagement.create", "engagement", eid,
               {"contributor_id": contributor_id, "rate": rate}, _ago(days=days_ago))
        for i, (hrs, note) in enumerate(weeks):
            db.execute(
                "INSERT INTO timesheets (id,engagement_id,week,hours,note,created_at) VALUES (?,?,?,?,?,?)",
                (_id("ts"), eid, f"Week {i + 1}", hrs, note, _ago(days=days_ago - (i + 1) * 7)),
            )
            total_hours += hrs
        db.execute("UPDATE engagements SET hours_logged = ? WHERE id = ?", (total_hours, eid))
        return eid, total_hours

    def fund_escrow(eid, client_id, contributor_id, rate, hours, status, days_ago):
        amount = rate * hours
        # Block from client available -> blocked.
        avail[client_id] -= amount
        blocked[client_id] += amount
        hid = _id("esc")
        db.execute(
            "INSERT INTO escrow_holds (id,engagement_id,client_id,contributor_id,amount_usd,hours,status,created_at,released_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (hid, eid, client_id, contributor_id, amount, hours, "held" if status == "in_escrow" else "released",
             _ago(days=days_ago), None if status == "in_escrow" else _ago(days=max(days_ago - 3, 0))),
        )
        pid = _id("pay")
        db.execute(
            "INSERT INTO payments (id,engagement_id,client_id,contributor_id,amount_usd,type,status,hours,gateway_ref,note,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (pid, eid, client_id, contributor_id, amount,
             "released" if status == "completed" else "escrow_funded",
             "completed" if status == "completed" else "in_escrow",
             hours, hid, f"Escrow — {hours}h", _ago(days=days_ago)),
        )
        return hid, pid, amount

    # Engagement 1: Northlane hires Sam (DevOps) — one released + one in escrow.
    e1, e1_hours = add_engagement(j_devops1, cl_north, c_sam, "Kubernetes Platform Engineer (GCC Pod)", 90,
                                  [(28, "Platform setup & Terraform"), (18, "GitOps & observability")], 24)
    # Engagement 2: Apex hires Ava (Frontend) — in escrow.
    e2, e2_hours = add_engagement(j_frontend1, cl_apex, c_ava, "React/Next.js Frontend Engineer — Trading UI", 85,
                                  [(32, "Data tables & streaming")], 16)
    # Engagement 3: Vertex hires Marcus (Backend) — released.
    e3, e3_hours = add_engagement(j_backend2, cl_vertex, c_marcus, "Go Microservices Engineer — Core Platform", 80,
                                  [(30, "Service scaffolding"), (24, "gRPC APIs")], 20)

    # Build wallet ids now that deposits are set.
    for uid in list(avail.keys()):
        wallet_ids[uid] = set_wallet(uid)  # placeholder; will update balances after escrow math

    # Recompute: we must set balances AFTER escrow adjustments, so delete+rebuild is messy.
    # Instead, we adjust balances in-memory then UPDATE the wallet rows.

    # Escrow flows:
    # e1: release 28h to Sam, keep 18h in escrow.
    _, p1a, amt1a = fund_escrow(e1, cl_north, c_sam, 90, 28, "completed", 20)
    avail[c_sam] += amt1a  # payout received
    blocked[cl_north] -= amt1a  # released from blocked
    _, p1b, amt1b = fund_escrow(e1, cl_north, c_sam, 90, 18, "in_escrow", 2)

    # e2: Ava 32h in escrow.
    _, p2, amt2 = fund_escrow(e2, cl_apex, c_ava, 85, 32, "in_escrow", 3)

    # e3: Marcus 54h released.
    _, p3, amt3 = fund_escrow(e3, cl_vertex, c_marcus, 80, 54, "completed", 14)
    avail[c_marcus] += amt3
    blocked[cl_vertex] -= amt3

    # Persist final balances.
    for uid in avail:
        db.execute(
            "UPDATE wallets SET available_balance = ?, blocked_balance = ? WHERE user_id = ?",
            (round(avail[uid], 2), round(blocked[uid], 2), uid),
        )

    # Wallet transactions (representative history).
    wtx(cl_north, "deposit", 90000, "ch_seed_north", "Visa •••• 4242 deposit", 30)
    wtx(cl_north, "escrow_block", -(90 * 28), e1, "Blocked for 28h", 20)
    wtx(cl_north, "escrow_release", -(90 * 28), p1a, "Released to Sam Okafor", 17)
    wtx(cl_north, "escrow_block", -(90 * 18), e1, "Blocked for 18h", 2)
    wtx(c_sam, "earning", 90 * 28, p1a, "Escrow payout received", 17)

    wtx(cl_apex, "deposit", 60000, "ch_seed_apex", "Mastercard •••• 4444 deposit", 28)
    wtx(cl_apex, "escrow_block", -(85 * 32), e2, "Blocked for 32h", 3)

    wtx(cl_vertex, "deposit", 75000, "ch_seed_vertex", "Visa •••• 4242 deposit", 25)
    wtx(cl_vertex, "escrow_block", -(80 * 54), e3, "Blocked for 54h", 14)
    wtx(cl_vertex, "escrow_release", -(80 * 54), p3, "Released to Marcus Bauer", 11)
    wtx(c_marcus, "earning", 80 * 54, p3, "Escrow payout received", 11)

    wtx(cl_nova, "deposit", 40000, "ch_seed_nova", "Visa •••• 4242 deposit", 26)
    wtx(cl_helix, "deposit", 35000, "ch_seed_helix", "Mastercard •••• 4444 deposit", 22)
    wtx(cl_infytech, "deposit", 50000, "ch_seed_infytech", "Visa •••• 4242 deposit", 20)

    # Saved demo cards for clients.
    add_card(cl_apex, "Mastercard", "4444", 11, 2028, "Jordan Blake", 1)
    add_card(cl_nova, "Visa", "4242", 4, 2027, "Mara Lindqvist", 1)
    add_card(cl_north, "Visa", "4242", 7, 2029, "Ethan Park", 1)
    add_card(cl_helix, "Mastercard", "4444", 9, 2028, "Amara Osei", 1)
    add_card(cl_vertex, "Visa", "4242", 3, 2030, "Liam Chen", 1)
    add_card(cl_infytech, "Visa", "4242", 6, 2029, "Kavya Menon", 1)
