from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app import models


PROVIDER_DISPLAY = {
    "siliconflow": "硅基流动",
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "custom": "自定义",
}


def value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def pick(obj: Any, fields: list[str]) -> dict[str, Any]:
    return {field: value(getattr(obj, field)) for field in fields}


def user_name(user: models.User | None) -> str:
    return user.username if user else ""


def department_name(department: models.Department | None) -> str:
    return department.name if department else ""


def contract_title(contract: models.Contract | None) -> str:
    return contract.title if contract else ""


def template_name(template: models.Template | None) -> str:
    return template.name if template else ""


def serialize_department(obj: models.Department) -> dict[str, Any]:
    return {
        "id": obj.id,
        "name": obj.name,
        "parent": obj.parent_id,
        "code": obj.code,
        "description": obj.description,
        "created_at": value(obj.created_at),
        "updated_at": value(obj.updated_at),
    }


def serialize_permission(obj: models.Permission) -> dict[str, Any]:
    return {
        "id": obj.id,
        "name": obj.name,
        "code": obj.code,
        "resource": obj.resource,
        "action": obj.action,
        "description": obj.description,
        "created_at": value(obj.created_at),
        "updated_at": value(obj.updated_at),
    }


def serialize_role(obj: models.Role) -> dict[str, Any]:
    permissions = [rp.permission for rp in obj.role_permissions if rp.permission and not rp.permission.is_deleted]
    return {
        "id": obj.id,
        "name": obj.name,
        "code": obj.code,
        "description": obj.description,
        "permissions": [serialize_permission(permission) for permission in permissions],
        "created_at": value(obj.created_at),
        "updated_at": value(obj.updated_at),
    }


def serialize_user(obj: models.User) -> dict[str, Any]:
    roles = [
        {
            "id": user_role.role.id,
            "name": user_role.role.name,
            "code": user_role.role.code,
            "description": user_role.role.description,
        }
        for user_role in obj.user_roles
        if user_role.role and not user_role.role.is_deleted
    ]
    return {
        "id": obj.id,
        "username": obj.username,
        "email": obj.email,
        "real_name": obj.real_name,
        "phone": obj.phone,
        "avatar": obj.avatar,
        "department": obj.department_id,
        "department_name": department_name(obj.department),
        "role": obj.role,
        "reviewer_level": obj.reviewer_level,
        "is_active": obj.is_active,
        "roles": roles,
        "created_at": value(obj.created_at),
        "updated_at": value(obj.updated_at),
    }


def serialize_audit_log(obj: models.AuditLog) -> dict[str, Any]:
    return {
        "id": obj.id,
        "user": obj.user_id,
        "user_name": user_name(obj.user) or "-",
        "action": obj.action,
        "resource_type": obj.resource_type,
        "resource_id": obj.resource_id,
        "ip_address": obj.ip_address,
        "user_agent": obj.user_agent,
        "request_data": obj.request_data,
        "response_data": obj.response_data,
        "status": obj.status,
        "error_message": obj.error_message,
        "created_at": value(obj.created_at),
    }


def serialize_contract_version(obj: models.ContractVersion) -> dict[str, Any]:
    return {
        "id": obj.id,
        "contract": obj.contract_id,
        "version": obj.version,
        "content": obj.content,
        "file_path": obj.file_path,
        "change_summary": obj.change_summary,
        "changed_by": obj.changed_by_id,
        "changed_by_name": user_name(obj.changed_by),
        "created_at": value(obj.created_at),
    }


def serialize_template(obj: models.Template) -> dict[str, Any]:
    return {
        "id": obj.id,
        "name": obj.name,
        "contract_type": obj.contract_type,
        "industry": obj.industry,
        "category": obj.category,
        "content": obj.content,
        "description": obj.description,
        "tags": obj.tags,
        "usage_count": obj.usage_count,
        "is_public": obj.is_public,
        "is_enterprise": obj.is_enterprise,
        "created_by": obj.created_by_id,
        "created_by_name": user_name(obj.created_by),
        "enterprise_id": obj.enterprise_id,
        "created_at": value(obj.created_at),
        "updated_at": value(obj.updated_at),
    }


def serialize_contract(obj: models.Contract, include_versions: bool = True) -> dict[str, Any]:
    versions = []
    if include_versions:
        versions = [
            serialize_contract_version(version)
            for version in sorted(obj.versions, key=lambda item: item.version, reverse=True)
            if not version.is_deleted
        ]
    return {
        "id": obj.id,
        "contract_no": obj.contract_no,
        "title": obj.title,
        "contract_type": obj.contract_type,
        "industry": obj.industry,
        "status": obj.status,
        "content": obj.content,
        "file_path": obj.file_path,
        "file_format": obj.file_format,
        "template": obj.template_id,
        "template_name": template_name(obj.template),
        "drafter": obj.drafter_id,
        "drafter_name": user_name(obj.drafter),
        "current_version": obj.current_version,
        "versions": versions,
        "created_at": value(obj.created_at),
        "updated_at": value(obj.updated_at),
    }


def serialize_user_habit(obj: models.UserHabit) -> dict[str, Any]:
    return {
        "id": obj.id,
        "user": obj.user_id,
        "habit_type": obj.habit_type,
        "habit_key": obj.habit_key,
        "habit_value": obj.habit_value,
        "frequency": obj.frequency,
        "last_used_at": value(obj.last_used_at),
        "created_at": value(obj.created_at),
        "updated_at": value(obj.updated_at),
    }


def serialize_review_opinion(obj: models.ReviewOpinion) -> dict[str, Any]:
    return {
        "id": obj.id,
        "review_result": obj.review_result_id,
        "reviewer": obj.reviewer_id,
        "reviewer_name": user_name(obj.reviewer),
        "clause_id": obj.clause_id,
        "clause_content": obj.clause_content,
        "opinion_type": obj.opinion_type,
        "risk_level": obj.risk_level,
        "opinion_content": obj.opinion_content,
        "legal_basis": obj.legal_basis,
        "suggestion": obj.suggestion,
        "status": obj.status,
        "created_at": value(obj.created_at),
        "updated_at": value(obj.updated_at),
    }


def serialize_review_result(obj: models.ReviewResult, include_opinions: bool = True) -> dict[str, Any]:
    opinions = []
    if include_opinions:
        opinions = [
            serialize_review_opinion(opinion)
            for opinion in sorted(obj.opinions, key=lambda item: (item.risk_level or "", item.created_at), reverse=True)
            if not opinion.is_deleted
        ]
    return {
        "id": obj.id,
        "review_task": obj.review_task_id,
        "contract": obj.contract_id,
        "contract_title": contract_title(obj.contract),
        "overall_score": value(obj.overall_score),
        "risk_level": obj.risk_level,
        "risk_count": obj.risk_count,
        "summary": obj.summary,
        "report_path": obj.report_path,
        "report_format": obj.report_format,
        "review_data": obj.review_data,
        "opinions": opinions,
        "created_at": value(obj.created_at),
    }


def reviewer_assignments_detail(obj: models.ReviewTask) -> dict[str, Any]:
    assignments = obj.reviewer_assignments
    if not isinstance(assignments, dict):
        return {}

    detail = {}
    for level, reviewer_id in assignments.items():
        reviewer = None
        try:
            reviewer_id_int = int(reviewer_id)
        except (TypeError, ValueError):
            reviewer_id_int = None
        if reviewer_id_int:
            reviewer = next((role_user for role_user in []), None)
            # Relationship-free lookup is intentionally handled by routers for list performance.
        detail[level] = {
            "id": reviewer_id_int,
            "username": "未知用户" if reviewer_id_int else "未分配",
            "real_name": "未知用户" if reviewer_id_int else "未分配",
            "email": "",
        }
    return detail


def fill_reviewer_assignments_detail(
    obj: models.ReviewTask,
    users_by_id: dict[int, models.User] | None = None,
) -> dict[str, Any]:
    assignments = obj.reviewer_assignments
    if not isinstance(assignments, dict):
        return {}
    users_by_id = users_by_id or {}
    detail = {}
    for level, reviewer_id in assignments.items():
        try:
            reviewer_id_int = int(reviewer_id)
        except (TypeError, ValueError):
            reviewer_id_int = None
        reviewer = users_by_id.get(reviewer_id_int) if reviewer_id_int else None
        if reviewer:
            detail[level] = {
                "id": reviewer.id,
                "username": reviewer.username,
                "real_name": reviewer.real_name or reviewer.username,
                "email": reviewer.email,
            }
        elif reviewer_id_int:
            detail[level] = {
                "id": reviewer_id_int,
                "username": "未知用户",
                "real_name": "未知用户",
                "email": "",
            }
        else:
            detail[level] = {
                "id": None,
                "username": "未分配",
                "real_name": "未分配",
                "email": "",
            }
    return detail


def serialize_review_task(
    obj: models.ReviewTask,
    users_by_id: dict[int, models.User] | None = None,
) -> dict[str, Any]:
    return {
        "id": obj.id,
        "contract": obj.contract_id,
        "contract_title": contract_title(obj.contract),
        "contract_version": obj.contract_version,
        "status": obj.status,
        "priority": obj.priority,
        "reviewer": obj.reviewer_id,
        "reviewer_name": user_name(obj.reviewer),
        "reviewer_level": obj.reviewer_level,
        "review_levels": obj.review_levels,
        "reviewer_assignments": obj.reviewer_assignments,
        "reviewer_assignments_detail": fill_reviewer_assignments_detail(obj, users_by_id),
        "celery_task_id": obj.celery_task_id,
        "progress": obj.progress,
        "started_at": value(obj.started_at),
        "completed_at": value(obj.completed_at),
        "error_message": obj.error_message,
        "created_by": obj.created_by_id,
        "created_by_name": user_name(obj.created_by),
        "result": serialize_review_result(obj.result) if obj.result else None,
        "created_at": value(obj.created_at),
        "updated_at": value(obj.updated_at),
    }


def serialize_review_cycle(obj: models.ReviewCycle) -> dict[str, Any]:
    return {
        "id": obj.id,
        "contract": obj.contract_id,
        "contract_title": contract_title(obj.contract),
        "cycle_no": obj.cycle_no,
        "review_result": obj.review_result_id,
        "opinion_summary": obj.opinion_summary,
        "modification_summary": obj.modification_summary,
        "status": obj.status,
        "submitted_by": obj.submitted_by_id,
        "submitted_by_name": user_name(obj.submitted_by),
        "submitted_at": value(obj.submitted_at),
        "modified_by": obj.modified_by_id,
        "modified_by_name": user_name(obj.modified_by),
        "modified_at": value(obj.modified_at),
        "created_at": value(obj.created_at),
        "updated_at": value(obj.updated_at),
    }


def serialize_review_focus_config(obj: models.ReviewFocusConfig) -> dict[str, Any]:
    return {
        "id": obj.id,
        "level": obj.level,
        "level_name": obj.level_name,
        "focus_points": obj.focus_points,
        "focus_description": obj.focus_description,
        "review_standards": obj.review_standards,
        "attention_items": obj.attention_items,
        "is_active": obj.is_active,
        "created_by": obj.created_by_id,
        "created_by_name": user_name(obj.created_by),
        "updated_by": obj.updated_by_id,
        "updated_by_name": user_name(obj.updated_by),
        "created_at": value(obj.created_at),
        "updated_at": value(obj.updated_at),
    }


def serialize_ai_model_config(obj: models.AIModelConfig) -> dict[str, Any]:
    return {
        "id": obj.id,
        "name": obj.name,
        "provider": obj.provider,
        "provider_display": PROVIDER_DISPLAY.get(obj.provider, obj.provider or ""),
        "api_key": obj.api_key,
        "api_base_url": obj.api_base_url,
        "available_models": obj.available_models,
        "default_model": obj.default_model,
        "is_active": obj.is_active,
        "is_default": obj.is_default,
        "description": obj.description,
        "temperature": obj.temperature,
        "max_tokens": obj.max_tokens,
        "timeout": obj.timeout,
        "created_by": obj.created_by_id,
        "created_by_name": user_name(obj.created_by),
        "updated_by": obj.updated_by_id,
        "updated_by_name": user_name(obj.updated_by),
        "created_at": value(obj.created_at),
        "updated_at": value(obj.updated_at),
    }


def serialize_review_rule(obj: models.ReviewRule) -> dict[str, Any]:
    return {
        "id": obj.id,
        "rule_code": obj.rule_code,
        "rule_name": obj.rule_name,
        "rule_type": obj.rule_type,
        "industry": obj.industry,
        "category": obj.category,
        "priority": obj.priority,
        "rule_content": obj.rule_content,
        "risk_level": obj.risk_level,
        "legal_basis": obj.legal_basis,
        "description": obj.description,
        "is_active": obj.is_active,
        "version": obj.version,
        "created_by": obj.created_by_id,
        "created_by_name": user_name(obj.created_by),
        "created_at": value(obj.created_at),
        "updated_at": value(obj.updated_at),
    }


def serialize_file_review_checklist(obj: models.FileReviewChecklist) -> dict[str, Any]:
    rules = [
        serialize_review_rule(link.rule)
        for link in sorted(obj.rule_links or [], key=lambda link: link.sort_order)
        if link.rule and not link.rule.is_deleted
    ]
    return {
        "id": obj.id,
        "name": obj.name,
        "description": obj.description,
        "rule_count": len(rules),
        "rule_ids": [rule["id"] for rule in rules],
        "rules": rules,
        "created_by": obj.created_by_id,
        "created_by_name": user_name(obj.created_by),
        "updated_by": obj.updated_by_id,
        "updated_by_name": user_name(obj.updated_by),
        "created_at": value(obj.created_at),
        "updated_at": value(obj.updated_at),
    }


def serialize_rule_match(obj: models.RuleMatch) -> dict[str, Any]:
    return {
        "id": obj.id,
        "review_task": obj.review_task_id,
        "rule": obj.rule_id,
        "rule_name": obj.rule.rule_name if obj.rule else "",
        "contract_id": obj.contract_id,
        "matched_clause": obj.matched_clause,
        "match_score": value(obj.match_score),
        "match_result": obj.match_result,
        "created_at": value(obj.created_at),
    }


def serialize_contract_clause(obj: models.ContractClause) -> dict[str, Any]:
    return {
        "id": obj.id,
        "contract": obj.contract_id,
        "contract_title": contract_title(obj.contract),
        "contract_version": obj.contract_version,
        "clause_no": obj.clause_no,
        "clause_type": obj.clause_type,
        "clause_title": obj.clause_title,
        "clause_content": obj.clause_content,
        "start_position": obj.start_position,
        "end_position": obj.end_position,
        "extracted_data": obj.extracted_data,
        "confidence": value(obj.confidence),
        "is_confirmed": obj.is_confirmed,
        "confirmed_by": obj.confirmed_by_id,
        "confirmed_by_name": user_name(obj.confirmed_by),
        "confirmed_at": value(obj.confirmed_at),
        "created_at": value(obj.created_at),
        "updated_at": value(obj.updated_at),
    }


def serialize_risk(obj: models.RiskIdentification) -> dict[str, Any]:
    return {
        "id": obj.id,
        "review_result": obj.review_result_id,
        "contract_id": obj.contract_id,
        "clause": obj.clause_id,
        "clause_content": obj.clause.clause_content if obj.clause else "",
        "risk_type": obj.risk_type,
        "risk_category": obj.risk_category,
        "risk_level": obj.risk_level,
        "risk_description": obj.risk_description,
        "risk_location": obj.risk_location,
        "legal_basis": obj.legal_basis,
        "suggestion": obj.suggestion,
        "status": obj.status,
        "handled_by": obj.handled_by_id,
        "handled_by_name": user_name(obj.handled_by),
        "handled_at": value(obj.handled_at),
        "created_at": value(obj.created_at),
    }


def serialize_comparison_diff(obj: models.ComparisonDiff) -> dict[str, Any]:
    return {
        "id": obj.id,
        "comparison_task": obj.comparison_task_id,
        "diff_type": obj.diff_type,
        "diff_level": obj.diff_level,
        "source_content": obj.source_content,
        "target_content": obj.target_content,
        "clause_id": obj.clause_id,
        "risk_level": obj.risk_level,
        "created_at": value(obj.created_at),
    }


def serialize_comparison_task(obj: models.ComparisonTask) -> dict[str, Any]:
    return {
        "id": obj.id,
        "task_type": obj.task_type,
        "source_contract": obj.source_contract_id,
        "source_contract_title": contract_title(obj.source_contract),
        "target_contract": obj.target_contract_id,
        "target_contract_title": contract_title(obj.target_contract),
        "source_version": obj.source_version,
        "target_version": obj.target_version,
        "template": obj.template_id,
        "template_name": template_name(obj.template),
        "status": obj.status,
        "result_data": obj.result_data,
        "created_by": obj.created_by_id,
        "created_by_name": user_name(obj.created_by),
        "diffs": [serialize_comparison_diff(diff) for diff in obj.diffs],
        "created_at": value(obj.created_at),
        "completed_at": value(obj.completed_at),
    }


def serialize_knowledge_entity(obj: models.KnowledgeEntity) -> dict[str, Any]:
    return {
        "id": obj.id,
        "entity_type": obj.entity_type,
        "entity_name": obj.entity_name,
        "entity_code": obj.entity_code,
        "description": obj.description,
        "properties": obj.properties,
        "source": obj.source,
        "created_at": value(obj.created_at),
        "updated_at": value(obj.updated_at),
    }


def serialize_knowledge_relation(obj: models.KnowledgeRelation) -> dict[str, Any]:
    return {
        "id": obj.id,
        "source_entity": obj.source_entity_id,
        "source_entity_id": obj.source_entity_id,
        "source_entity_name": obj.source_entity.entity_name if obj.source_entity else "",
        "target_entity": obj.target_entity_id,
        "target_entity_id": obj.target_entity_id,
        "target_entity_name": obj.target_entity.entity_name if obj.target_entity else "",
        "relation_type": obj.relation_type,
        "relation_properties": obj.relation_properties,
        "confidence": value(obj.confidence),
        "created_at": value(obj.created_at),
        "updated_at": value(obj.updated_at),
    }


def serialize_regulation(obj: models.Regulation) -> dict[str, Any]:
    return {
        "id": obj.id,
        "title": obj.title,
        "regulation_no": obj.regulation_no,
        "regulation_type": obj.regulation_type,
        "publish_date": value(obj.publish_date),
        "effective_date": value(obj.effective_date),
        "expiry_date": value(obj.expiry_date),
        "content": obj.content,
        "source_url": obj.source_url,
        "entity": obj.entity_id,
        "entity_name": obj.entity.entity_name if obj.entity else "",
        "is_active": obj.is_active,
        "created_at": value(obj.created_at),
        "updated_at": value(obj.updated_at),
    }


def serialize_case(obj: models.LegalCase) -> dict[str, Any]:
    return {
        "id": obj.id,
        "case_no": obj.case_no,
        "case_title": obj.case_title,
        "case_type": obj.case_type,
        "court": obj.court,
        "judge_date": value(obj.judge_date),
        "case_summary": obj.case_summary,
        "case_content": obj.case_content,
        "related_clauses": obj.related_clauses,
        "entity": obj.entity_id,
        "entity_name": obj.entity.entity_name if obj.entity else "",
        "created_at": value(obj.created_at),
        "updated_at": value(obj.updated_at),
    }


def serialize_recommendation(obj: models.Recommendation) -> dict[str, Any]:
    return {
        "id": obj.id,
        "user": obj.user_id,
        "user_name": user_name(obj.user),
        "contract": obj.contract_id,
        "contract_title": contract_title(obj.contract),
        "recommendation_type": obj.recommendation_type,
        "recommendation_context": obj.recommendation_context,
        "item_type": obj.item_type,
        "item_id": obj.item_id,
        "item_content": obj.item_content,
        "score": value(obj.score),
        "reason": obj.reason,
        "is_accepted": obj.is_accepted,
        "created_at": value(obj.created_at),
    }
