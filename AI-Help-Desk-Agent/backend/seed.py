from app.database import Base, engine, SessionLocal
from app.models import User, KnowledgeDocument, SystemService
from app.security import hash_password

Base.metadata.create_all(bind=engine)
db = SessionLocal()
if not db.query(User).filter_by(email="demo@helpdesk.local").first():
    db.add(User(email="demo@helpdesk.local", name="Demo Admin", password_hash=hash_password("demo1234"), role="admin"))
if not db.query(KnowledgeDocument).count():
    db.add_all([
        KnowledgeDocument(title="WiFi troubleshooting", category="network", content="Check airplane mode, reconnect to the correct SSID, restart the router, and test another device."),
        KnowledgeDocument(title="Password reset policy", category="security", content="Use the official password reset flow. Support will never ask for your password or one-time code."),
        KnowledgeDocument(title="VPN quick start", category="vpn", content="Confirm internet access, open the approved VPN client, sign in, and select the nearest organization gateway."),
    ])
if not db.query(SystemService).count():
    names = ["Authentication", "Database", "Email", "File Storage", "API Gateway", "Payment", "Notification"]
    db.add_all([SystemService(name=n, status="Operational", message="All systems normal") for n in names])
db.commit()
db.close()