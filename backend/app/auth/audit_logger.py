import logging
import json
from datetime import datetime, timezone
from uuid import uuid4

from app.auth.permissions import PermissionDecision
from app.core.schemas import AuthContext, Intent, ToolResult
from app.db import execute


logger = logging.getLogger("robot_reception.audit")


class AuditLogger:
    """Audit hook for sensitive access."""

    def log_auth_event(
        self,
        *,
        event_type: str,
        account_id: str | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
        role: str | None = None,
        clinic_id: str | None = None,
        reason: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        audit = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "account_id": account_id,
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "clinic_id": clinic_id,
            "reason": reason,
            "metadata": metadata or {},
        }
        logger.info(event_type, extra={"audit": audit})
        self._insert_event(
            event_type=event_type,
            account_id=account_id,
            session_id=session_id,
            user_id=user_id,
            role=role,
            clinic_id=clinic_id,
            reason=reason,
            metadata=metadata or {},
        )

    def log_policy_decision(
        self,
        *,
        auth: AuthContext,
        intent: Intent,
        decision: PermissionDecision,
    ) -> None:
        logger.info(
            "policy_decision",
            extra={
                "audit": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "role": auth.role,
                    "user_id": auth.user_id,
                    "clinic_id": auth.clinic_id,
                    "intent": intent.intent,
                    "allowed": decision.allowed,
                    "reason": decision.reason,
                }
            },
        )
        self._insert_event(
            event_type="policy_decision",
            account_id=auth.account_id,
            session_id=auth.session_id,
            user_id=auth.user_id,
            role=str(auth.role),
            clinic_id=auth.clinic_id,
            intent=intent.intent,
            allowed=decision.allowed,
            reason=decision.reason,
        )

    def log_tool_result(
        self,
        *,
        auth: AuthContext,
        intent: Intent,
        result: ToolResult,
    ) -> None:
        logger.info(
            "tool_result",
            extra={
                "audit": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "role": auth.role,
                    "user_id": auth.user_id,
                    "clinic_id": auth.clinic_id,
                    "intent": intent.intent,
                    "tool_name": result.tool_name,
                    "source": result.source,
                    "row_count": len(result.rows),
                }
            },
        )
        self._insert_event(
            event_type="tool_result",
            account_id=auth.account_id,
            session_id=auth.session_id,
            user_id=auth.user_id,
            role=str(auth.role),
            clinic_id=auth.clinic_id,
            intent=intent.intent,
            tool_name=result.tool_name,
            source=result.source,
            row_count=len(result.rows),
        )

    def _insert_event(
        self,
        *,
        event_type: str,
        account_id: str | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
        role: str | None = None,
        clinic_id: str | None = None,
        intent: str | None = None,
        tool_name: str | None = None,
        source: str | None = None,
        allowed: bool | None = None,
        reason: str | None = None,
        row_count: int | None = None,
        metadata: dict | None = None,
    ) -> None:
        try:
            execute(
                """
                INSERT INTO robo_auth.audit_events (
                  id,
                  event_type,
                  account_id,
                  session_id,
                  user_id,
                  role,
                  clinic_id,
                  intent,
                  tool_name,
                  source,
                  allowed,
                  reason,
                  row_count,
                  metadata
                )
                VALUES (
                  %(id)s,
                  %(event_type)s,
                  %(account_id)s,
                  %(session_id)s,
                  %(user_id)s,
                  %(role)s,
                  %(clinic_id)s,
                  %(intent)s,
                  %(tool_name)s,
                  %(source)s,
                  %(allowed)s,
                  %(reason)s,
                  %(row_count)s,
                  %(metadata)s::jsonb
                )
                """,
                {
                    "id": str(uuid4()),
                    "event_type": event_type,
                    "account_id": account_id,
                    "session_id": session_id,
                    "user_id": user_id,
                    "role": role,
                    "clinic_id": clinic_id,
                    "intent": intent,
                    "tool_name": tool_name,
                    "source": source,
                    "allowed": allowed,
                    "reason": reason,
                    "row_count": row_count,
                    "metadata": json.dumps(metadata or {}, ensure_ascii=False),
                },
            )
        except Exception:
            logger.exception("audit_db_write_failed")
