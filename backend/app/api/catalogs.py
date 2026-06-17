import time
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Body, HTTPException, Request, Response, status
from sqlalchemy.orm import selectinload

from app import models
from app.api.deps import CurrentUser, DbSession
from app.api.router_utils import apply_filters, commit_or_400, create_item, delete_item, get_or_404, paginate, parse_bool, update_item
from app.serializers import (
    serialize_case,
    serialize_comparison_diff,
    serialize_comparison_task,
    serialize_contract_clause,
    serialize_file_review_checklist,
    serialize_knowledge_entity,
    serialize_knowledge_relation,
    serialize_recommendation,
    serialize_regulation,
    serialize_review_rule,
    serialize_risk,
    serialize_rule_match,
)
from app.services import simple_recommendations_for_contract_type


rules_router = APIRouter(prefix="/rules", tags=["rules"])
clauses_router = APIRouter(prefix="/clauses", tags=["clauses"])
risks_router = APIRouter(prefix="/risks", tags=["risks"])
comparisons_router = APIRouter(prefix="/comparisons", tags=["comparisons"])
knowledge_router = APIRouter(prefix="/knowledge", tags=["knowledge"])
recommendations_router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@rules_router.get("/rules/")
def list_rules(request: Request, db: DbSession, _: CurrentUser):
    query = db.query(models.ReviewRule).options(selectinload(models.ReviewRule.created_by))
    query = apply_filters(
        query,
        models.ReviewRule,
        request,
        filter_fields=["rule_type", "industry", "category", "risk_level", "is_active", "rule_name", "rule_code"],
        search_fields=["rule_name", "rule_code", "description"],
        ordering_fields=["priority", "created_at"],
        default_ordering=["-priority", "-created_at"],
        aliases={"created_by": "created_by_id"},
    )
    if "is_active" not in request.query_params and not parse_bool(request.query_params.get("include_inactive", False)):
        query = query.filter(models.ReviewRule.is_active.is_(True))
    query.order_by()
    return paginate(query, request, serialize_review_rule)


def checklist_query(db: DbSession):
    return db.query(models.FileReviewChecklist).options(
        selectinload(models.FileReviewChecklist.created_by),
        selectinload(models.FileReviewChecklist.updated_by),
        selectinload(models.FileReviewChecklist.rule_links).selectinload(models.FileReviewChecklistRule.rule).selectinload(models.ReviewRule.created_by),
    )


def normalize_rule_ids(payload: dict) -> list[int]:
    raw_rule_ids = payload.get("rule_ids")
    if raw_rule_ids is None and isinstance(payload.get("rules"), list):
        raw_rule_ids = [item.get("id") if isinstance(item, dict) else item for item in payload["rules"]]
    if raw_rule_ids is None:
        return []
    if not isinstance(raw_rule_ids, list):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="rule_ids必须是数组")

    rule_ids: list[int] = []
    seen: set[int] = set()
    for raw in raw_rule_ids:
        try:
            rule_id = int(raw)
        except (TypeError, ValueError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="规则ID格式不正确")
        if rule_id not in seen:
            seen.add(rule_id)
            rule_ids.append(rule_id)
    return rule_ids


def ensure_checklist_name_available(db: DbSession, name: str, exclude_id: int | None = None) -> None:
    query = db.query(models.FileReviewChecklist).filter(
        models.FileReviewChecklist.name == name,
        models.FileReviewChecklist.is_deleted.is_(False),
    )
    if exclude_id is not None:
        query = query.filter(models.FileReviewChecklist.id != exclude_id)
    if query.first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="审查清单名称已存在")


def validate_checklist_payload(db: DbSession, payload: dict, *, require_rules: bool = True, exclude_id: int | None = None) -> tuple[str, str, list[int]]:
    name = str(payload.get("name") or payload.get("checklist_name") or "").strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="审查清单名称不能为空")
    if len(name) > 100:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="审查清单名称不能超过100个字符")
    ensure_checklist_name_available(db, name, exclude_id=exclude_id)

    rule_ids = normalize_rule_ids(payload)
    if require_rules and not rule_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请至少选择一条审查规则")
    description = str(payload.get("description") or "").strip()
    return name, description, rule_ids


def set_checklist_rules(db: DbSession, checklist: models.FileReviewChecklist, rule_ids: list[int]) -> None:
    if checklist.id:
        db.query(models.FileReviewChecklistRule).filter(
            models.FileReviewChecklistRule.checklist_id == checklist.id
        ).delete(synchronize_session=False)
        db.flush()
        db.expire(checklist, ["rule_links"])

    if not rule_ids:
        checklist.rule_links = []
        return

    rules = (
        db.query(models.ReviewRule)
        .filter(
            models.ReviewRule.id.in_(rule_ids),
            models.ReviewRule.is_deleted.is_(False),
            models.ReviewRule.is_active.is_(True),
        )
        .all()
    )
    existing_ids = {rule.id for rule in rules}
    missing_ids = [rule_id for rule_id in rule_ids if rule_id not in existing_ids]
    if missing_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"规则不存在或未启用: {missing_ids}")

    checklist.rule_links = [
        models.FileReviewChecklistRule(rule_id=rule_id, sort_order=index)
        for index, rule_id in enumerate(rule_ids)
    ]


@rules_router.get("/checklists/")
def list_checklists(request: Request, db: DbSession, _: CurrentUser):
    query = checklist_query(db)
    query = apply_filters(
        query,
        models.FileReviewChecklist,
        request,
        filter_fields=["name"],
        search_fields=["name", "description"],
        ordering_fields=["updated_at", "created_at", "name"],
        default_ordering=["-updated_at"],
    )
    return paginate(query, request, serialize_file_review_checklist)


@rules_router.post("/checklists/", status_code=status.HTTP_201_CREATED)
def create_checklist(db: DbSession, current_user: CurrentUser, payload: dict = Body(...)):
    name, description, rule_ids = validate_checklist_payload(db, payload)
    item = models.FileReviewChecklist(
        name=name,
        description=description,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )
    db.add(item)
    db.flush()
    set_checklist_rules(db, item, rule_ids)
    commit_or_400(db)
    return serialize_file_review_checklist(
        checklist_query(db).filter(models.FileReviewChecklist.id == item.id).first()
    )


@rules_router.get("/checklists/{item_id}/")
def retrieve_checklist(item_id: int, db: DbSession, _: CurrentUser):
    item = checklist_query(db).filter(
        models.FileReviewChecklist.id == item_id,
        models.FileReviewChecklist.is_deleted.is_(False),
    ).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资源不存在")
    return serialize_file_review_checklist(item)


@rules_router.patch("/checklists/{item_id}/")
@rules_router.put("/checklists/{item_id}/")
def update_checklist(item_id: int, db: DbSession, current_user: CurrentUser, payload: dict = Body(...)):
    item = checklist_query(db).filter(
        models.FileReviewChecklist.id == item_id,
        models.FileReviewChecklist.is_deleted.is_(False),
    ).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资源不存在")

    name, description, rule_ids = validate_checklist_payload(db, payload, exclude_id=item.id)
    item.name = name
    item.description = description
    item.updated_by_id = current_user.id
    set_checklist_rules(db, item, rule_ids)
    commit_or_400(db)
    return serialize_file_review_checklist(
        checklist_query(db).filter(models.FileReviewChecklist.id == item.id).first()
    )


@rules_router.delete("/checklists/{item_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_checklist(item_id: int, db: DbSession, _: CurrentUser):
    delete_item(db, get_or_404(db, models.FileReviewChecklist, item_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def generate_review_rule_code(db: DbSession) -> str:
    now = datetime.now()
    date_part = now.strftime("%Y%m%d")
    timestamp_tail = int(time.time() * 1000) % 100000

    for offset in range(100000):
        code = f"{date_part}{(timestamp_tail + offset) % 100000:05d}"
        exists = db.query(models.ReviewRule.id).filter(models.ReviewRule.rule_code == code).first()
        if not exists:
            return code

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="规则编码生成失败，请稍后重试")


@rules_router.post("/rules/", status_code=status.HTTP_201_CREATED)
def create_rule(db: DbSession, current_user: CurrentUser, payload: dict = Body(...)):
    item = models.ReviewRule(
        rule_code=generate_review_rule_code(db),
        rule_name=str(payload.get("rule_name") or "").strip(),
        rule_type=payload.get("rule_type") or "general",
        industry=str(payload.get("industry") or "").strip(),
        category=str(payload.get("category") or "").strip(),
        priority=int(payload.get("priority") or 0),
        rule_content=payload.get("rule_content") or {},
        risk_level=payload.get("risk_level") or "",
        legal_basis=str(payload.get("legal_basis") or "").strip(),
        description=str(payload.get("description") or "").strip(),
        is_active=parse_bool(payload.get("is_active", True)),
        version=int(payload.get("version") or 1),
        created_by_id=current_user.id,
    )
    db.add(item)
    commit_or_400(db)
    db.refresh(item)
    return serialize_review_rule(item)


@rules_router.get("/rules/{item_id}/")
def retrieve_rule(item_id: int, db: DbSession, _: CurrentUser):
    return serialize_review_rule(get_or_404(db, models.ReviewRule, item_id))


@rules_router.patch("/rules/{item_id}/")
@rules_router.put("/rules/{item_id}/")
def update_rule(item_id: int, db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    item = update_item(db, get_or_404(db, models.ReviewRule, item_id), payload, aliases={"created_by": "created_by_id"}, readonly={"id", "rule_code", "created_at", "updated_at", "created_by_id"})
    return serialize_review_rule(item)


@rules_router.delete("/rules/{item_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(item_id: int, db: DbSession, _: CurrentUser):
    delete_item(db, get_or_404(db, models.ReviewRule, item_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@rules_router.get("/matches/")
def list_rule_matches(request: Request, db: DbSession, _: CurrentUser):
    query = db.query(models.RuleMatch).options(selectinload(models.RuleMatch.rule))
    query = apply_filters(
        query,
        models.RuleMatch,
        request,
        filter_fields=["review_task", "rule", "contract_id"],
        ordering_fields=["match_score", "created_at"],
        default_ordering=["-match_score"],
        aliases={"review_task": "review_task_id", "rule": "rule_id"},
    )
    return paginate(query, request, serialize_rule_match)


@rules_router.get("/matches/{item_id}/")
def retrieve_rule_match(item_id: int, db: DbSession, _: CurrentUser):
    return serialize_rule_match(get_or_404(db, models.RuleMatch, item_id))


@clauses_router.get("/clauses/")
def list_clauses(request: Request, db: DbSession, _: CurrentUser):
    query = db.query(models.ContractClause).options(selectinload(models.ContractClause.contract), selectinload(models.ContractClause.confirmed_by))
    query = apply_filters(
        query,
        models.ContractClause,
        request,
        filter_fields=["contract", "contract_version", "clause_type", "is_confirmed"],
        ordering_fields=["start_position", "created_at"],
        default_ordering=["start_position"],
        aliases={"contract": "contract_id", "confirmed_by": "confirmed_by_id"},
    )
    return paginate(query, request, serialize_contract_clause)


@clauses_router.post("/clauses/", status_code=status.HTTP_201_CREATED)
def create_clause(db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    item = create_item(db, models.ContractClause, payload, aliases={"contract": "contract_id", "confirmed_by": "confirmed_by_id"}, readonly={"id", "created_at", "updated_at"})
    return serialize_contract_clause(item)


@clauses_router.get("/clauses/{item_id}/")
def retrieve_clause(item_id: int, db: DbSession, _: CurrentUser):
    return serialize_contract_clause(get_or_404(db, models.ContractClause, item_id))


@clauses_router.patch("/clauses/{item_id}/")
@clauses_router.put("/clauses/{item_id}/")
def update_clause(item_id: int, db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    item = update_item(db, get_or_404(db, models.ContractClause, item_id), payload, aliases={"contract": "contract_id", "confirmed_by": "confirmed_by_id"}, readonly={"id", "created_at", "updated_at"})
    return serialize_contract_clause(item)


@clauses_router.delete("/clauses/{item_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_clause(item_id: int, db: DbSession, _: CurrentUser):
    db.delete(get_or_404(db, models.ContractClause, item_id))
    commit_or_400(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@clauses_router.post("/clauses/{item_id}/confirm/")
def confirm_clause(item_id: int, db: DbSession, current_user: CurrentUser):
    clause = get_or_404(db, models.ContractClause, item_id)
    clause.is_confirmed = True
    clause.confirmed_by_id = current_user.id
    clause.confirmed_at = datetime.now()
    commit_or_400(db)
    return serialize_contract_clause(clause)


@risks_router.get("/risks/")
def list_risks(request: Request, db: DbSession, _: CurrentUser):
    query = db.query(models.RiskIdentification).options(selectinload(models.RiskIdentification.clause), selectinload(models.RiskIdentification.handled_by))
    query = apply_filters(
        query,
        models.RiskIdentification,
        request,
        filter_fields=["review_result", "contract_id", "risk_type", "risk_category", "risk_level", "status"],
        ordering_fields=["risk_level", "created_at"],
        default_ordering=["-risk_level", "-created_at"],
        aliases={"review_result": "review_result_id", "handled_by": "handled_by_id", "clause": "clause_id"},
    )
    return paginate(query, request, serialize_risk)


@risks_router.post("/risks/", status_code=status.HTTP_201_CREATED)
def create_risk(db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    item = create_item(db, models.RiskIdentification, payload, aliases={"review_result": "review_result_id", "handled_by": "handled_by_id", "clause": "clause_id"}, readonly={"id", "created_at"})
    return serialize_risk(item)


@risks_router.get("/risks/{item_id}/")
def retrieve_risk(item_id: int, db: DbSession, _: CurrentUser):
    return serialize_risk(get_or_404(db, models.RiskIdentification, item_id))


@risks_router.patch("/risks/{item_id}/")
@risks_router.put("/risks/{item_id}/")
def update_risk(item_id: int, db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    item = update_item(db, get_or_404(db, models.RiskIdentification, item_id), payload, aliases={"review_result": "review_result_id", "handled_by": "handled_by_id", "clause": "clause_id"}, readonly={"id", "created_at"})
    return serialize_risk(item)


@risks_router.delete("/risks/{item_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_risk(item_id: int, db: DbSession, _: CurrentUser):
    db.delete(get_or_404(db, models.RiskIdentification, item_id))
    commit_or_400(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@risks_router.post("/risks/{item_id}/handle/")
def handle_risk(item_id: int, db: DbSession, current_user: CurrentUser):
    risk = get_or_404(db, models.RiskIdentification, item_id)
    risk.status = "handled"
    risk.handled_by_id = current_user.id
    risk.handled_at = datetime.now()
    commit_or_400(db)
    return serialize_risk(risk)


@comparisons_router.get("/tasks/")
def list_comparison_tasks(request: Request, db: DbSession, _: CurrentUser):
    query = db.query(models.ComparisonTask).options(
        selectinload(models.ComparisonTask.source_contract),
        selectinload(models.ComparisonTask.target_contract),
        selectinload(models.ComparisonTask.template),
        selectinload(models.ComparisonTask.created_by),
        selectinload(models.ComparisonTask.diffs),
    )
    query = apply_filters(
        query,
        models.ComparisonTask,
        request,
        filter_fields=["task_type", "status"],
        ordering_fields=["created_at"],
        default_ordering=["-created_at"],
        aliases={"source_contract": "source_contract_id", "target_contract": "target_contract_id", "created_by": "created_by_id", "template": "template_id"},
    )
    return paginate(query, request, serialize_comparison_task)


@comparisons_router.post("/tasks/", status_code=status.HTTP_201_CREATED)
def create_comparison_task(db: DbSession, current_user: CurrentUser, payload: dict = Body(...)):
    item = create_item(
        db,
        models.ComparisonTask,
        payload,
        aliases={"source_contract": "source_contract_id", "target_contract": "target_contract_id", "created_by": "created_by_id", "template": "template_id"},
        readonly={"id", "created_at", "completed_at", "created_by_id"},
        extra={"created_by_id": current_user.id},
    )
    return serialize_comparison_task(item)


@comparisons_router.get("/tasks/{item_id}/")
def retrieve_comparison_task(item_id: int, db: DbSession, _: CurrentUser):
    return serialize_comparison_task(get_or_404(db, models.ComparisonTask, item_id))


@comparisons_router.patch("/tasks/{item_id}/")
@comparisons_router.put("/tasks/{item_id}/")
def update_comparison_task(item_id: int, db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    item = update_item(db, get_or_404(db, models.ComparisonTask, item_id), payload, aliases={"source_contract": "source_contract_id", "target_contract": "target_contract_id", "created_by": "created_by_id", "template": "template_id"}, readonly={"id", "created_at", "completed_at", "created_by_id"})
    return serialize_comparison_task(item)


@comparisons_router.delete("/tasks/{item_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_comparison_task(item_id: int, db: DbSession, _: CurrentUser):
    db.delete(get_or_404(db, models.ComparisonTask, item_id))
    commit_or_400(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@comparisons_router.get("/diffs/")
def list_comparison_diffs(request: Request, db: DbSession, _: CurrentUser):
    query = db.query(models.ComparisonDiff)
    query = apply_filters(
        query,
        models.ComparisonDiff,
        request,
        filter_fields=["comparison_task", "diff_type", "diff_level", "risk_level"],
        ordering_fields=["risk_level", "created_at"],
        default_ordering=["-risk_level", "created_at"],
        aliases={"comparison_task": "comparison_task_id"},
    )
    return paginate(query, request, serialize_comparison_diff)


@comparisons_router.get("/diffs/{item_id}/")
def retrieve_comparison_diff(item_id: int, db: DbSession, _: CurrentUser):
    return serialize_comparison_diff(get_or_404(db, models.ComparisonDiff, item_id))


@knowledge_router.get("/entities/")
def list_entities(request: Request, db: DbSession, _: CurrentUser):
    query = db.query(models.KnowledgeEntity)
    query = apply_filters(
        query,
        models.KnowledgeEntity,
        request,
        filter_fields=["entity_type"],
        search_fields=["entity_name", "entity_code", "description"],
        ordering_fields=["created_at"],
        default_ordering=["entity_type", "entity_name"],
    )
    return paginate(query, request, serialize_knowledge_entity)


@knowledge_router.post("/entities/", status_code=status.HTTP_201_CREATED)
def create_entity(db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    return serialize_knowledge_entity(create_item(db, models.KnowledgeEntity, payload, readonly={"id", "created_at", "updated_at"}))


@knowledge_router.get("/entities/{item_id}/")
def retrieve_entity(item_id: int, db: DbSession, _: CurrentUser):
    return serialize_knowledge_entity(get_or_404(db, models.KnowledgeEntity, item_id))


@knowledge_router.patch("/entities/{item_id}/")
@knowledge_router.put("/entities/{item_id}/")
def update_entity(item_id: int, db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    return serialize_knowledge_entity(update_item(db, get_or_404(db, models.KnowledgeEntity, item_id), payload, readonly={"id", "created_at", "updated_at"}))


@knowledge_router.delete("/entities/{item_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_entity(item_id: int, db: DbSession, _: CurrentUser):
    delete_item(db, get_or_404(db, models.KnowledgeEntity, item_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@knowledge_router.get("/relations/")
def list_relations(request: Request, db: DbSession, _: CurrentUser):
    query = db.query(models.KnowledgeRelation).options(selectinload(models.KnowledgeRelation.source_entity), selectinload(models.KnowledgeRelation.target_entity))
    aliases = {"source_entity": "source_entity_id", "target_entity": "target_entity_id"}
    query = apply_filters(
        query,
        models.KnowledgeRelation,
        request,
        filter_fields=["source_entity", "target_entity", "relation_type"],
        ordering_fields=["confidence", "created_at"],
        default_ordering=["-confidence"],
        aliases=aliases,
    )
    return paginate(query, request, serialize_knowledge_relation)


@knowledge_router.post("/relations/", status_code=status.HTTP_201_CREATED)
def create_relation(db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    return serialize_knowledge_relation(create_item(db, models.KnowledgeRelation, payload, aliases={"source_entity": "source_entity_id", "target_entity": "target_entity_id"}, readonly={"id", "created_at", "updated_at"}))


@knowledge_router.get("/relations/{item_id}/")
def retrieve_relation(item_id: int, db: DbSession, _: CurrentUser):
    return serialize_knowledge_relation(get_or_404(db, models.KnowledgeRelation, item_id))


@knowledge_router.patch("/relations/{item_id}/")
@knowledge_router.put("/relations/{item_id}/")
def update_relation(item_id: int, db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    return serialize_knowledge_relation(update_item(db, get_or_404(db, models.KnowledgeRelation, item_id), payload, aliases={"source_entity": "source_entity_id", "target_entity": "target_entity_id"}, readonly={"id", "created_at", "updated_at"}))


@knowledge_router.delete("/relations/{item_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_relation(item_id: int, db: DbSession, _: CurrentUser):
    delete_item(db, get_or_404(db, models.KnowledgeRelation, item_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@knowledge_router.get("/regulations/")
def list_regulations(request: Request, db: DbSession, _: CurrentUser):
    query = db.query(models.Regulation).options(selectinload(models.Regulation.entity)).filter(models.Regulation.is_active.is_(True))
    query = apply_filters(
        query,
        models.Regulation,
        request,
        filter_fields=["regulation_type", "is_active"],
        search_fields=["title", "regulation_no", "content"],
        ordering_fields=["publish_date", "effective_date"],
        default_ordering=["-publish_date"],
        aliases={"entity": "entity_id"},
    )
    return paginate(query, request, serialize_regulation)


@knowledge_router.post("/regulations/", status_code=status.HTTP_201_CREATED)
def create_regulation(db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    return serialize_regulation(create_item(db, models.Regulation, payload, aliases={"entity": "entity_id"}, readonly={"id", "created_at", "updated_at"}))


@knowledge_router.get("/regulations/{item_id}/")
def retrieve_regulation(item_id: int, db: DbSession, _: CurrentUser):
    return serialize_regulation(get_or_404(db, models.Regulation, item_id))


@knowledge_router.patch("/regulations/{item_id}/")
@knowledge_router.put("/regulations/{item_id}/")
def update_regulation(item_id: int, db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    return serialize_regulation(update_item(db, get_or_404(db, models.Regulation, item_id), payload, aliases={"entity": "entity_id"}, readonly={"id", "created_at", "updated_at"}))


@knowledge_router.delete("/regulations/{item_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_regulation(item_id: int, db: DbSession, _: CurrentUser):
    delete_item(db, get_or_404(db, models.Regulation, item_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@knowledge_router.get("/cases/")
def list_cases(request: Request, db: DbSession, _: CurrentUser):
    query = db.query(models.LegalCase).options(selectinload(models.LegalCase.entity))
    query = apply_filters(
        query,
        models.LegalCase,
        request,
        filter_fields=["case_type"],
        search_fields=["case_title", "case_no", "case_summary"],
        ordering_fields=["judge_date"],
        default_ordering=["-judge_date"],
        aliases={"entity": "entity_id"},
    )
    return paginate(query, request, serialize_case)


@knowledge_router.post("/cases/", status_code=status.HTTP_201_CREATED)
def create_case(db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    return serialize_case(create_item(db, models.LegalCase, payload, aliases={"entity": "entity_id"}, readonly={"id", "created_at", "updated_at"}))


@knowledge_router.get("/cases/{item_id}/")
def retrieve_case(item_id: int, db: DbSession, _: CurrentUser):
    return serialize_case(get_or_404(db, models.LegalCase, item_id))


@knowledge_router.patch("/cases/{item_id}/")
@knowledge_router.put("/cases/{item_id}/")
def update_case(item_id: int, db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    return serialize_case(update_item(db, get_or_404(db, models.LegalCase, item_id), payload, aliases={"entity": "entity_id"}, readonly={"id", "created_at", "updated_at"}))


@knowledge_router.delete("/cases/{item_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_case(item_id: int, db: DbSession, _: CurrentUser):
    delete_item(db, get_or_404(db, models.LegalCase, item_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@recommendations_router.post("/recommendations/recommend_clauses/")
def recommend_clauses(db: DbSession, current_user: CurrentUser, payload: dict = Body(...)):
    contract_id = payload.get("contract_id")
    if not contract_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="contract_id不能为空")
    contract = get_or_404(db, models.Contract, int(contract_id))
    context = payload.get("context", "drafting")
    recommendations = []
    for clause in simple_recommendations_for_contract_type(contract.contract_type):
        item = models.Recommendation(
            user_id=current_user.id,
            contract_id=contract.id,
            recommendation_type="clause",
            recommendation_context=context,
            item_type="clause",
            item_content=clause,
            score=Decimal("0.80"),
            reason=f"基于合同类型“{contract.contract_type}”的推荐条款",
        )
        db.add(item)
        db.flush()
        recommendations.append(serialize_recommendation(item))
    commit_or_400(db)
    return {"success": True, "recommendations": recommendations, "count": len(recommendations)}


@recommendations_router.post("/recommendations/recommend_templates/")
def recommend_templates(db: DbSession, current_user: CurrentUser, payload: dict = Body(...)):
    contract_type = payload.get("contract_type")
    if not contract_type:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="contract_type不能为空")
    query = db.query(models.Template).filter(models.Template.contract_type == contract_type, models.Template.is_deleted.is_(False), models.Template.is_public.is_(True))
    if payload.get("industry"):
        query = query.filter(models.Template.industry == payload["industry"])
    templates = query.order_by(models.Template.usage_count.desc(), models.Template.created_at.desc()).limit(5).all()
    recommendations = []
    for template in templates:
        item = models.Recommendation(
            user_id=current_user.id,
            recommendation_type="template",
            recommendation_context="drafting",
            item_type="template",
            item_id=template.id,
            item_content=template.name,
            score=Decimal("0.80"),
            reason="基于合同类型和行业的推荐模板",
        )
        db.add(item)
        db.flush()
        recommendations.append(serialize_recommendation(item))
    commit_or_400(db)
    return {"success": True, "recommendations": recommendations, "count": len(recommendations)}


@recommendations_router.post("/recommendations/recommend_risk_responses/")
def recommend_risk_responses(db: DbSession, current_user: CurrentUser, payload: dict = Body(...)):
    contract_id = payload.get("contract_id")
    if not contract_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="contract_id不能为空")
    contract = get_or_404(db, models.Contract, int(contract_id))
    recommendations = []
    if payload.get("review_result_id"):
        opinions = (
            db.query(models.ReviewOpinion)
            .filter(models.ReviewOpinion.review_result_id == payload["review_result_id"], models.ReviewOpinion.risk_level.in_(["high", "medium"]))
            .limit(5)
            .all()
        )
        for opinion in opinions:
            item = models.Recommendation(
                user_id=current_user.id,
                contract_id=contract.id,
                recommendation_type="risk_response",
                recommendation_context="reviewing",
                item_type="risk_response",
                item_id=opinion.id,
                item_content=opinion.suggestion or "建议结合风险点补充明确条款责任边界。",
                score=Decimal("0.90") if opinion.risk_level == "high" else Decimal("0.70"),
                reason=f"针对风险意见“{opinion.opinion_content[:50]}”的应对建议",
            )
            db.add(item)
            db.flush()
            recommendations.append(serialize_recommendation(item))
    commit_or_400(db)
    return {"success": True, "recommendations": recommendations, "count": len(recommendations)}


@recommendations_router.get("/recommendations/")
def list_recommendations(request: Request, db: DbSession, current_user: CurrentUser):
    query = db.query(models.Recommendation).options(selectinload(models.Recommendation.user), selectinload(models.Recommendation.contract))
    if not current_user.is_staff:
        query = query.filter(models.Recommendation.user_id == current_user.id)
    query = apply_filters(
        query,
        models.Recommendation,
        request,
        filter_fields=["user", "contract", "recommendation_type", "recommendation_context", "is_accepted"],
        ordering_fields=["score", "created_at"],
        default_ordering=["-score", "-created_at"],
        aliases={"user": "user_id", "contract": "contract_id"},
    )
    return paginate(query, request, serialize_recommendation)


@recommendations_router.post("/recommendations/", status_code=status.HTTP_201_CREATED)
def create_recommendation(db: DbSession, current_user: CurrentUser, payload: dict = Body(...)):
    item = create_item(
        db,
        models.Recommendation,
        payload,
        aliases={"user": "user_id", "contract": "contract_id"},
        readonly={"id", "created_at", "user_id"},
        extra={"user_id": current_user.id},
    )
    return serialize_recommendation(item)


@recommendations_router.get("/recommendations/{item_id}/")
def retrieve_recommendation(item_id: int, db: DbSession, _: CurrentUser):
    return serialize_recommendation(get_or_404(db, models.Recommendation, item_id))


@recommendations_router.patch("/recommendations/{item_id}/")
@recommendations_router.put("/recommendations/{item_id}/")
def update_recommendation(item_id: int, db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    item = update_item(db, get_or_404(db, models.Recommendation, item_id), payload, aliases={"user": "user_id", "contract": "contract_id"}, readonly={"id", "created_at", "user_id"})
    return serialize_recommendation(item)


@recommendations_router.delete("/recommendations/{item_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_recommendation(item_id: int, db: DbSession, _: CurrentUser):
    db.delete(get_or_404(db, models.Recommendation, item_id))
    commit_or_400(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@recommendations_router.post("/recommendations/{item_id}/accept/")
def accept_recommendation(item_id: int, db: DbSession, _: CurrentUser):
    item = get_or_404(db, models.Recommendation, item_id)
    item.is_accepted = True
    commit_or_400(db)
    return serialize_recommendation(item)


@recommendations_router.post("/recommendations/{item_id}/reject/")
def reject_recommendation(item_id: int, db: DbSession, _: CurrentUser):
    item = get_or_404(db, models.Recommendation, item_id)
    item.is_accepted = False
    commit_or_400(db)
    return serialize_recommendation(item)
