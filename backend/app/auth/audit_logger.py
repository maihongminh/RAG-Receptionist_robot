import logging
from datetime import datetime, timezone

from app.auth.permissions import PermissionDecision
from app.core.schemas import AuthContext, Intent, ToolResult


logger = logging.getLogger("robot_reception.audit")


class AuditLogger:
    """Audit hook for sensitive access.

    MVP behavior logs to application logger only. Later this should write to a
    dedicated audit table with immutable retention.
    """

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
