# Cơ Sở Dữ Liệu DocMind (Database Architecture & ERD)

Tài liệu này mô tả chi tiết thiết kế Cơ sở dữ liệu (Database Schema), sơ đồ quan hệ thực thể (ERD), và quy ước khóa cho hệ thống **DocMind**.

---

## 1. Sơ Đồ Quan Hệ Thực Thể (ERD - Entity Relationship Diagram)

```text
┌─────────────────────────────────┐
│           documents             │
├─────────────────────────────────┤
│ PK  id               String(64) │◄───┐
│     filename         String(255)│    │
│     file_size        Integer    │    │ 1:N (CASCADE)
│     page_count       Integer    │    ├───┐
│     created_at       DateTime   │    │   │
└─────────────────────────────────┘    │   │
                                       │   │
        ┌──────────────────────────────┘   │
        ▼                                  ▼
┌─────────────────────────────────┐      ┌─────────────────────────────────┐
│        document_pages           │      │             chunks              │
├─────────────────────────────────┤      ├─────────────────────────────────┤
│ PK  id               Integer    │      │ PK  id               String(64) │
│ FK  document_id      String(64) │      │ FK  document_id      String(64) │
│     page_number      Integer    │      │     text             Text       │
│     text             Text       │      │     token_count      Integer    │
└─────────────────────────────────┘      │     page_numbers     JSON       │
                                         │     sequence_number  Integer    │
                                         └─────────────────────────────────┘

┌─────────────────────────────────┐
│         chat_sessions           │
├─────────────────────────────────┤
│ PK  id               String(64) │◄───┐
│     title            String(255)│    │ 1:N (CASCADE)
│     created_at       DateTime   │    │
│     updated_at       DateTime   │    │
└─────────────────────────────────┘    │
                                       │
        ┌──────────────────────────────┘
        ▼
┌─────────────────────────────────┐
│          chat_messages          │
├─────────────────────────────────┤
│ PK  id               String(64) │
│ FK  session_id       String(64) │
│     role             String(20) │
│     content          Text       │
│     sources          JSON       │
│     tokens_used      JSON       │
│     created_at       DateTime   │
└─────────────────────────────────┘
```

---

## 2. Quản Lý Phiên Bản Cơ Sở Dữ Liệu (Alembic Migrations)

Toàn bộ các bảng trên được quản lý và tạo lập bằng công cụ **Alembic**:

* **Tệp cấu hình**: [alembic.ini](../../alembic.ini) và [migrations/env.py](../../migrations/env.py)
* **File migration đầu tiên**: [migrations/versions/acd377e1a164_create_initial_core_tables.py](../../migrations/versions/acd377e1a164_create_initial_core_tables.py)

**Các lệnh thường dùng:**
```bash
# Áp dụng các thay đổi mới nhất lên CSDL
alembic upgrade head

# Xem phiên bản migration hiện tại của CSDL
alembic current

# Tự động sinh file migration mới khi có thay đổi trong models.py
alembic revision --autogenerate -m "ten_thay_doi"
```
