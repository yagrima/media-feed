# Async Architecture Standard

**Created**: October 26, 2025  
**Version**: 1.0  
**Status**: **ARCHITECTURE DECREE** - All services must follow this standard

---

## 🚀 **ASYNC-FIRST ARCHITECTURE DECISION**

From this point forward, **ALL services in Me Feed SHALL implement async/await patterns**. This is not optional - it is a mandatory architectural standard.

---

## 📋 **MANDATORY IMPLEMENTATION REQUIREMENTS**

### **1. Database Services**
```python
# ❌ FORBIDDEN - Sync patterns
class Service:
    def __init__(self, db: Session):  # ❌ Invalid
        self.db = db
        
    def get_data(self):
        return self.db.query(Model).all()  # ❌ Never use .query()

# ✅ REQUIRED - Async patterns  
class Service:
    def __init__(self, db: AsyncSession):  # ✅ Required
        self.db = db
        
    async def get_data(self):  # ✅ All methods async
        query = select(Model)
        result = await self.db.execute(query)
        return result.scalars().all()  # ✅ Use select() + execute()
```

### **2. API Endpoints**
```python
# ❌ FORBIDDEN - Sync endpoint
@app.get("/data")
def get_data(db: Session = Depends(get_db)):  # ❌ Invalid
    service = Service(db)
    return service.get_data()

# ✅ REQUIRED - Async endpoint
@app.get("/data")
async def get_data(db: AsyncSession = Depends(get_db)):  # ✅ Required
    service = Service(db)
    return await service.get_data()  # ✅ Always await
```

### **3. Database Queries**
```python
# ❌ FORBIDDEN - SQLAlchemy ORM queries
results = db.query(User).filter(User.id == user_id).first()
db.session.commit()

# ✅ REQUIRED - SQLAlchemy Core async queries
query = select(User).where(User.id == user_id)
result = await db.execute(query)
user = result.scalar_one_or_none()
await db.commit()  # ✅ Always await commit/rollback
```

---

## 🏗️ **IMPLEMENTATION STATUS**

### **✅ COMPLIANT SERVICES**
- **AuthService** ✅ - Full async implementation
- **ImportService** ✅ - Full async implementation  
- **EmailService** ✅ - No DB dependencies, naturally async
- **NotificationService** ✅ - Completely rebuilt as async (`notification_service_async.py`)

### **ℹ️ NOTEWORTHY SERVICES**
- **SequelDetector** ℹ️ - No direct DB operations, OK as sync utility service
- **TitleParser** ℹ️ - Pure utility, sync is acceptable
- **Validators** ℹ️ - Pure validation, sync is acceptable

---

## 🔧 **MIGRATION PATTERN**

When converting sync services to async:

### **Step 1: Update Imports**
```python
from sqlalchemy.orm import Session → from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
```

### **Step 2: Update Method Signatures**
```python
def method(self) → async def method(self)  # Add async to all DB methods
db: Session → db: AsyncSession  # Update type hints
```

### **Step 3: Convert Queries**
```python
# Old sync pattern
results = db.query(Model).where(Model.field == value).all()

# New async pattern
query = select(Model).where(Model.field == value)
result = await db.execute(query)
results = result.scalars().all()
```

### **Step 4: Handle Transactions**
```python
# Always await DB operations
await db.commit()
await db.rollback()
```

---

## 📏 **CODE REVIEW CHECKLIST**

When reviewing async implementations:

- [ ] Method signatures include `async def`
- [ ] Database dependencies use `AsyncSession`  
- [ ] All database operations are awaited
- [ ] SQLAlchemy `select()` used instead of `.query()`
- [ ] No direct session access (`db.session` forbidden)
- [ ] Error handling includes `await db.rollback()`

---

## 🎯 **PERFORMANCE BENEFITS**

With async architecture:

- ✅ **Non-blocking I/O** - Handles concurrent requests efficiently
- ✅ **Better Resource Utilization** - No thread blocking on database operations  
- ✅ **Scalability** - 10x+ concurrent request handling vs sync
- ✅ **FastAPI Native** - Leverages framework design
- ✅ **Future-Proof** - Ready for high-traffic production

---

## ⚠️ **ENFORCEMENT**

### **Automated Checks**
- Import linting to detect `Session` usage
- Code analysis to flag `db.query()` patterns
- Type checking for `AsyncSession` compliance

### **Pull Request Requirements**
- All new services MUST implement async patterns
- Database changes MUST be async-first
- Code reviews MUST check async compliance

---

## 📚 **REFERENCE IMPLEMENTATIONS**

See these files for correct async patterns:
- `app/services/notification_service_async.py` - Complete async service
- `app/services/auth_service.py` - Auth service async patterns  
- `app/api/notification_api.py` - Async API endpoint patterns

---

**CONCLUSION**: This async-first approach is now the **official architectural standard** for Me Feed. All development must comply with these guidelines.

*Exceptions must be justified in architectural review and documented separately.*

---

**Signed**: Orchestrator AI Architecture Team  
**Effective**: October 26, 2025  
**Review**: Quarterly
