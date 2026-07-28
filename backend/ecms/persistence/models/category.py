"""Category taxonomy ORM model.

User-defined technical domains (frontend, backend, security, ...) used by the
categorization agent to tag knowledge graph nodes. Defaults are seeded; users
can add/edit/delete. The agent uses each category's description as ground truth.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Integer, String, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from ecms.persistence.models.base import Base
from ecms.shared.time import utcnow

__all__ = ["Category"]


DEFAULT_CATEGORIES = [
    {"name": "security", "description": "Code handling auth, tokens, secrets, encryption, credentials, or access control", "color": "#ef4444", "priority": 1, "is_default": True},
    {"name": "infrastructure", "description": "Infrastructure-as-code, Docker, Kubernetes, CI/CD, cloud config, networking, Terraform", "color": "#f59e0b", "priority": 2, "is_default": True},
    {"name": "database", "description": "Schemas, migrations, ORM models, SQL queries, data access layers", "color": "#3b82f6", "priority": 3, "is_default": True},
    {"name": "frontend", "description": "UI components, React/Vue/Svelte, styles, client-side bundles, browser code", "color": "#10b981", "priority": 4, "is_default": True},
    {"name": "backend", "description": "APIs, services, business logic, server frameworks, route handlers", "color": "#8b5cf6", "priority": 5, "is_default": True},
    {"name": "data-ml", "description": "Notebooks, model training, datasets, ML pipelines, data science code", "color": "#ec4899", "priority": 6, "is_default": True},
    {"name": "documentation", "description": "Markdown, docs, READMEs, specs, wikis, architectural write-ups", "color": "#64748b", "priority": 7, "is_default": True},
    {"name": "uncategorized", "description": "Anything that does not match a defined category. Catch-all for unclassified nodes.", "color": "#94a3b8", "priority": 99, "is_default": True},
]


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String(128), primary_key=True, default=lambda: f"cat-{utcnow().timestamp()}")
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    color: Mapped[str] = mapped_column(String(16), nullable=False, default="#94a3b8")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=99)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "priority": self.priority,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "updated_at": self.updated_at.isoformat() if self.updated_at else "",
        }
