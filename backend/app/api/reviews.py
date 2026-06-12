import os
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Body, HTTPException, Request, Response, status
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy import or_
from sqlalchemy.orm import selectinload

from app import models
from app.api.deps import CurrentUser, DbSession
from app.api.router_utils import apply_filters, commit_or_400, create_item, delete_item, get_or_404, paginate, update_item
from app.core.config import get_settings
from app.serializers import (
    serialize_ai_model_config,
    serialize_review_cycle,
    serialize_review_focus_config,
    serialize_review_opinion,
    serialize_review_result,
    serialize_review_task,
)
from app.services import (
    AIService,
    generate_reviewer_suggestions,
    process_review_task,
    summarize_opinions,
    write_review_report,
)


router = APIRouter(prefix="/reviews", tags=["reviews"])
settings = get_settings()

TASK_ALIASES = {"contract": "contract_id", "reviewer": "reviewer_id", "created_by": "created_by_id"}
RESULT_ALIASES = {"review_task": "review_task_id", "contract": "contract_id"}
OPINION_ALIASES = {"review_result": "review_result_id", "reviewer": "reviewer_id"}
CYCLE_ALIASES = {
    "contract": "contract_id",
    "review_result": "review_result_id",
    "submitted_by": "submitted_by_id",
    "modified_by": "modified_by_id",
}
FOCUS_ALIASES = {"created_by": "created_by_id", "updated_by": "updated_by_id"}
AI_CONFIG_ALIASES = {"created_by": "created_by_id", "updated_by": "updated_by_id"}


def task_query(db: DbSession):
    return db.query(models.ReviewTask).options(
        selectinload(models.ReviewTask.contract).selectinload(models.Contract.drafter),
        selectinload(models.ReviewTask.reviewer),
        selectinload(models.ReviewTask.created_by),
        selectinload(models.ReviewTask.result).selectinload(models.ReviewResult.opinions).selectinload(models.ReviewOpinion.reviewer),
        selectinload(models.ReviewTask.result).selectinload(models.ReviewResult.contract),
    )


def reviewers_map(db: DbSession) -> dict[int, models.User]:
    return {user.id: user for user in db.query(models.User).filter(models.User.is_deleted.is_(False)).all()}


@router.get("/tasks/reviewers/")
def get_reviewers(request: Request, db: DbSession, _: CurrentUser):
    level = request.query_params.get("level")
    query = db.query(models.User).filter(
        models.User.role == "reviewer",
        models.User.is_active.is_(True),
        models.User.is_deleted.is_(False),
    )
    if level:
        query = query.filter(models.User.reviewer_level == level)
    users = query.order_by(models.User.reviewer_level, models.User.username).all()
    reviewers = [
        {
            "id": user.id,
            "username": user.username,
            "real_name": user.real_name or user.username,
            "email": user.email,
            "reviewer_level": user.reviewer_level,
            "level": user.reviewer_level,
        }
        for user in users
    ]
    grouped: dict[str, list[dict]] = {}
    for reviewer in reviewers:
        grouped.setdefault(reviewer["reviewer_level"] or "unassigned", []).append(reviewer)
    return {"reviewers": reviewers, "grouped": grouped}


@router.post("/tasks/check_stuck_tasks/")
def check_stuck_tasks(db: DbSession, _: CurrentUser):
    threshold = datetime.now() - timedelta(minutes=30)
    tasks = db.query(models.ReviewTask).filter(models.ReviewTask.status.in_(["processing", "ai_processing"]), models.ReviewTask.started_at < threshold).all()
    fixed_count = 0
    for task in tasks:
        task.status = "completed" if task.result else "failed"
        task.error_message = "" if task.result else "任务超时，自动标记为失败"
        task.completed_at = datetime.now()
        fixed_count += 1
    commit_or_400(db)
    return {"message": f"已修复 {fixed_count} 个卡住的任务", "fixed_count": fixed_count}


@router.get("/tasks/")
def list_tasks(request: Request, db: DbSession, current_user: CurrentUser):
    query = task_query(db)
    if current_user.role == "reviewer" and current_user.reviewer_level:
        query = query.filter(or_(models.ReviewTask.reviewer_id == current_user.id, models.ReviewTask.reviewer_assignments.isnot(None)))
    query = apply_filters(
        query,
        models.ReviewTask,
        request,
        filter_fields=["contract", "status", "task_type"],
        ordering_fields=["created_at", "priority"],
        default_ordering=["-created_at"],
        aliases=TASK_ALIASES,
    )
    user_map = reviewers_map(db)
    return paginate(query, request, lambda item: serialize_review_task(item, user_map))


@router.post("/tasks/", status_code=status.HTTP_201_CREATED)
def create_task(db: DbSession, current_user: CurrentUser, payload: dict = Body(...)):
    item = create_item(
        db,
        models.ReviewTask,
        payload,
        aliases=TASK_ALIASES,
        readonly={"id", "created_at", "updated_at", "started_at", "completed_at", "created_by_id"},
        extra={"created_by_id": current_user.id},
    )
    return serialize_review_task(item, reviewers_map(db))


@router.get("/tasks/{item_id}/")
def retrieve_task(item_id: int, db: DbSession, _: CurrentUser):
    item = task_query(db).filter(models.ReviewTask.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资源不存在")
    return serialize_review_task(item, reviewers_map(db))


@router.patch("/tasks/{item_id}/")
@router.put("/tasks/{item_id}/")
def update_task(item_id: int, db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    item = get_or_404(db, models.ReviewTask, item_id)
    item = update_item(
        db,
        item,
        payload,
        aliases=TASK_ALIASES,
        readonly={"id", "created_at", "updated_at", "started_at", "completed_at", "created_by_id"},
    )
    return serialize_review_task(item, reviewers_map(db))


@router.delete("/tasks/{item_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(item_id: int, db: DbSession, _: CurrentUser):
    delete_item(db, get_or_404(db, models.ReviewTask, item_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/tasks/{item_id}/start/")
def start_task(item_id: int, db: DbSession, _: CurrentUser):
    item = task_query(db).filter(models.ReviewTask.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资源不存在")
    if item.status not in {"pending", "failed"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="任务状态不允许启动")
    result = process_review_task(db, item)
    return {"message": "审核任务已完成（同步）", "task": serialize_review_task(item, reviewers_map(db)), "result": result}


@router.get("/tasks/{item_id}/result/")
def task_result(item_id: int, db: DbSession, _: CurrentUser):
    item = task_query(db).filter(models.ReviewTask.id == item_id).first()
    if not item or not item.result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="审核结果不存在")
    return serialize_review_result(item.result)


@router.post("/tasks/{item_id}/complete_manually/")
def complete_task_manually(item_id: int, db: DbSession, _: CurrentUser):
    item = task_query(db).filter(models.ReviewTask.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资源不存在")
    if item.result:
        item.status = "completed"
        item.completed_at = datetime.now()
        commit_or_400(db)
        return {"message": "任务已标记为完成"}
    result = process_review_task(db, item)
    return {"message": "任务已手动完成", "task": serialize_review_task(item, reviewers_map(db)), "result": result}


@router.post("/tasks/{item_id}/submit_review/")
def submit_review(item_id: int, db: DbSession, current_user: CurrentUser, payload: dict = Body(...)):
    task = task_query(db).filter(models.ReviewTask.id == item_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资源不存在")
    if current_user.role != "reviewer" or not current_user.reviewer_level:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有审核员可以提交审核意见")

    assigned = task.reviewer_id == current_user.id
    if not assigned and isinstance(task.reviewer_assignments, dict):
        assigned = str(task.reviewer_assignments.get(current_user.reviewer_level)) == str(current_user.id)
    if not assigned:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="该任务未分配给您")

    if task.status == "pending":
        task.status = "manual_reviewing"
        task.started_at = datetime.now()

    result = task.result
    if not result:
        result = models.ReviewResult(review_task_id=task.id, contract_id=task.contract_id)
        db.add(result)
        db.flush()

    for opinion_data in payload.get("opinions", []):
        db.add(
            models.ReviewOpinion(
                review_result_id=result.id,
                reviewer_id=current_user.id,
                clause_id=opinion_data.get("clause_id", ""),
                clause_content=opinion_data.get("clause_content", ""),
                opinion_type=opinion_data.get("opinion_type", "suggestion"),
                risk_level=opinion_data.get("risk_level", "low"),
                opinion_content=opinion_data.get("opinion_content", ""),
                legal_basis=opinion_data.get("legal_basis", ""),
                suggestion=opinion_data.get("suggestion", ""),
                status="pending",
            )
        )

    task.reviewer_id = current_user.id
    task.reviewer_level = current_user.reviewer_level
    db.flush()

    if isinstance(task.review_levels, list) and task.review_levels:
        completed_levels = {
            opinion.reviewer.reviewer_level
            for opinion in result.opinions
            if opinion.reviewer and opinion.reviewer.reviewer_level
        }
        completed_levels.add(current_user.reviewer_level)
        if set(task.review_levels).issubset(completed_levels):
            task.status = "completed"
            task.completed_at = datetime.now()
    commit_or_400(db)
    return {"message": "审核意见已提交", "task_id": task.id, "review_result_id": result.id}


@router.get("/results/")
def list_results(request: Request, db: DbSession, _: CurrentUser):
    query = db.query(models.ReviewResult).options(
        selectinload(models.ReviewResult.contract),
        selectinload(models.ReviewResult.opinions).selectinload(models.ReviewOpinion.reviewer),
    )
    query = apply_filters(
        query,
        models.ReviewResult,
        request,
        filter_fields=["contract", "risk_level"],
        ordering_fields=["created_at"],
        default_ordering=["-created_at"],
        aliases=RESULT_ALIASES,
    )
    return paginate(query, request, serialize_review_result)


@router.get("/results/{item_id}/")
def retrieve_result(item_id: int, db: DbSession, _: CurrentUser):
    return serialize_review_result(get_or_404(db, models.ReviewResult, item_id))


@router.get("/results/{item_id}/generate_report/")
@router.post("/results/{item_id}/generate_report/")
def generate_report(item_id: int, db: DbSession, _: CurrentUser, payload: dict = Body(default={})):
    result = get_or_404(db, models.ReviewResult, item_id)
    contract = result.contract
    report_path = write_review_report(result, contract, payload.get("format", "word"))
    result.report_path = report_path
    result.report_format = Path(report_path).suffix.lstrip(".")
    commit_or_400(db)
    return {"success": True, "report_path": report_path, "message": "报告生成成功"}


@router.get("/results/{item_id}/download_report/")
def download_report(item_id: int, db: DbSession, _: CurrentUser):
    return report_file_response(db, item_id, as_attachment=True)


@router.get("/results/{item_id}/preview_report/")
def preview_report(item_id: int, db: DbSession, _: CurrentUser):
    return report_file_response(db, item_id, as_attachment=False)


def report_file_response(db: DbSession, result_id: int, *, as_attachment: bool):
    result = get_or_404(db, models.ReviewResult, result_id)
    if not result.report_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="报告文件不存在")
    file_path = settings.media_root / result.report_path
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="报告文件不存在")
    disposition = "attachment" if as_attachment else "inline"
    media_type = "application/pdf" if file_path.suffix.lower() == ".pdf" else "application/octet-stream"
    return FileResponse(file_path, media_type=media_type, filename=file_path.name, content_disposition_type=disposition)


@router.get("/opinions/")
def list_opinions(request: Request, db: DbSession, _: CurrentUser):
    query = db.query(models.ReviewOpinion).options(selectinload(models.ReviewOpinion.reviewer))
    query = apply_filters(
        query,
        models.ReviewOpinion,
        request,
        filter_fields=["review_result", "opinion_type", "risk_level", "status"],
        ordering_fields=["risk_level", "created_at"],
        default_ordering=["-risk_level", "-created_at"],
        aliases=OPINION_ALIASES,
    )
    return paginate(query, request, serialize_review_opinion)


@router.post("/opinions/", status_code=status.HTTP_201_CREATED)
def create_opinion(db: DbSession, current_user: CurrentUser, payload: dict = Body(...)):
    item = create_item(
        db,
        models.ReviewOpinion,
        payload,
        aliases=OPINION_ALIASES,
        readonly={"id", "created_at", "updated_at", "reviewer_id"},
        extra={"reviewer_id": current_user.id},
    )
    return serialize_review_opinion(item)


@router.get("/opinions/{item_id}/")
def retrieve_opinion(item_id: int, db: DbSession, _: CurrentUser):
    return serialize_review_opinion(get_or_404(db, models.ReviewOpinion, item_id))


@router.patch("/opinions/{item_id}/")
@router.put("/opinions/{item_id}/")
def update_opinion(item_id: int, db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    item = update_item(db, get_or_404(db, models.ReviewOpinion, item_id), payload, aliases=OPINION_ALIASES, readonly={"id", "created_at", "updated_at"})
    return serialize_review_opinion(item)


@router.delete("/opinions/{item_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_opinion(item_id: int, db: DbSession, _: CurrentUser):
    delete_item(db, get_or_404(db, models.ReviewOpinion, item_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/cycles/summarize_opinions/")
def summarize_cycle_opinions(db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    contract_id = payload.get("contract_id")
    if not contract_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请提供contract_id参数")
    contract = get_or_404(db, models.Contract, int(contract_id))
    query = task_query(db).filter(models.ReviewTask.contract_id == contract.id)
    if payload.get("review_task_ids"):
        query = query.filter(models.ReviewTask.id.in_(payload["review_task_ids"]))
    tasks = query.all()
    summary_table = summarize_opinions(contract, tasks)
    return {
        "success": True,
        "contract_id": contract.id,
        "total_opinions": summary_table["statistics"]["total_opinions"],
        "summary_table": summary_table,
    }


@router.post("/cycles/feedback_to_drafter/")
def feedback_to_drafter(db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    contract_id = payload.get("contract_id")
    if not contract_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请提供contract_id参数")
    contract = get_or_404(db, models.Contract, int(contract_id))
    contract.status = "reviewing"
    commit_or_400(db)
    return {
        "success": True,
        "contract_id": contract.id,
        "contract_status": contract.status,
        "summary_table": payload.get("summary_table"),
        "feedback_message": payload.get("feedback_message") or "请根据审核意见修改合同",
    }


@router.post("/cycles/resubmit_for_review/")
def resubmit_for_review(db: DbSession, current_user: CurrentUser, payload: dict = Body(...)):
    contract_id = payload.get("contract_id")
    if not contract_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请提供contract_id参数")
    contract = get_or_404(db, models.Contract, int(contract_id))
    new_version = contract.current_version + 1
    db.add(
        models.ContractVersion(
            contract_id=contract.id,
            version=new_version,
            content=contract.content,
            file_path=contract.file_path,
            change_summary=payload.get("change_summary") or "根据审核意见修改后重新提交",
            changed_by_id=current_user.id,
        )
    )
    contract.current_version = new_version
    contract.status = "reviewing"
    task = models.ReviewTask(contract_id=contract.id, contract_version=new_version, status="pending", created_by_id=current_user.id)
    db.add(task)
    commit_or_400(db)
    db.refresh(task)
    return {"success": True, "contract_id": contract.id, "new_version": new_version, "review_task_id": task.id, "message": "合同已重新提交审核"}


@router.get("/cycles/")
def list_cycles(request: Request, db: DbSession, _: CurrentUser):
    query = db.query(models.ReviewCycle).options(selectinload(models.ReviewCycle.contract), selectinload(models.ReviewCycle.submitted_by), selectinload(models.ReviewCycle.modified_by))
    query = apply_filters(
        query,
        models.ReviewCycle,
        request,
        filter_fields=["contract", "status"],
        ordering_fields=["cycle_no", "created_at"],
        default_ordering=["-cycle_no"],
        aliases=CYCLE_ALIASES,
    )
    return paginate(query, request, serialize_review_cycle)


@router.post("/cycles/", status_code=status.HTTP_201_CREATED)
def create_cycle(db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    return serialize_review_cycle(create_item(db, models.ReviewCycle, payload, aliases=CYCLE_ALIASES, readonly={"id", "created_at", "updated_at"}))


@router.get("/cycles/{item_id}/")
def retrieve_cycle(item_id: int, db: DbSession, _: CurrentUser):
    return serialize_review_cycle(get_or_404(db, models.ReviewCycle, item_id))


@router.patch("/cycles/{item_id}/")
@router.put("/cycles/{item_id}/")
def update_cycle(item_id: int, db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    return serialize_review_cycle(update_item(db, get_or_404(db, models.ReviewCycle, item_id), payload, aliases=CYCLE_ALIASES, readonly={"id", "created_at", "updated_at"}))


@router.delete("/cycles/{item_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_cycle(item_id: int, db: DbSession, _: CurrentUser):
    db.delete(get_or_404(db, models.ReviewCycle, item_id))
    commit_or_400(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/cycles/{item_id}/submit/")
def submit_cycle(item_id: int, db: DbSession, current_user: CurrentUser, payload: dict = Body(default={})):
    cycle = get_or_404(db, models.ReviewCycle, item_id)
    cycle.status = "reviewing"
    cycle.submitted_by_id = current_user.id
    cycle.submitted_at = datetime.now()
    cycle.opinion_summary = payload.get("opinion_summary", "")
    task = models.ReviewTask(contract_id=cycle.contract_id, task_type="auto", created_by_id=current_user.id)
    db.add(task)
    commit_or_400(db)
    db.refresh(task)
    return {"message": "已提交审核", "review_task_id": task.id}


@router.post("/cycles/{item_id}/modify/")
def modify_cycle(item_id: int, db: DbSession, current_user: CurrentUser, payload: dict = Body(default={})):
    cycle = get_or_404(db, models.ReviewCycle, item_id)
    cycle.status = "modifying"
    cycle.modified_by_id = current_user.id
    cycle.modified_at = datetime.now()
    cycle.modification_summary = payload.get("modification_summary", "")
    commit_or_400(db)
    return {"message": "已记录修改"}


@router.get("/focus-configs/by_level/")
def focus_by_level(request: Request, db: DbSession, _: CurrentUser):
    level = request.query_params.get("level")
    if not level:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请提供level参数")
    item = (
        db.query(models.ReviewFocusConfig)
        .filter(models.ReviewFocusConfig.level == level, models.ReviewFocusConfig.is_active.is_(True))
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="该层级的配置不存在")
    return serialize_review_focus_config(item)


@router.get("/focus-configs/")
def list_focus_configs(request: Request, db: DbSession, _: CurrentUser):
    query = db.query(models.ReviewFocusConfig).options(selectinload(models.ReviewFocusConfig.created_by), selectinload(models.ReviewFocusConfig.updated_by))
    query = apply_filters(
        query,
        models.ReviewFocusConfig,
        request,
        filter_fields=["level", "is_active"],
        ordering_fields=["level", "created_at"],
        default_ordering=["level"],
        aliases=FOCUS_ALIASES,
    )
    return paginate(query, request, serialize_review_focus_config)


@router.post("/focus-configs/", status_code=status.HTTP_201_CREATED)
def create_focus_config(db: DbSession, current_user: CurrentUser, payload: dict = Body(...)):
    item = create_item(
        db,
        models.ReviewFocusConfig,
        payload,
        aliases=FOCUS_ALIASES,
        readonly={"id", "created_at", "updated_at", "created_by_id", "updated_by_id"},
        extra={"created_by_id": current_user.id},
    )
    return serialize_review_focus_config(item)


@router.get("/focus-configs/{item_id}/")
def retrieve_focus_config(item_id: int, db: DbSession, _: CurrentUser):
    return serialize_review_focus_config(get_or_404(db, models.ReviewFocusConfig, item_id))


@router.patch("/focus-configs/{item_id}/")
@router.put("/focus-configs/{item_id}/")
def update_focus_config(item_id: int, db: DbSession, current_user: CurrentUser, payload: dict = Body(...)):
    item = update_item(
        db,
        get_or_404(db, models.ReviewFocusConfig, item_id),
        payload,
        aliases=FOCUS_ALIASES,
        readonly={"id", "created_at", "updated_at", "created_by_id", "updated_by_id"},
        extra={"updated_by_id": current_user.id},
    )
    return serialize_review_focus_config(item)


@router.delete("/focus-configs/{item_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_focus_config(item_id: int, db: DbSession, _: CurrentUser):
    db.delete(get_or_404(db, models.ReviewFocusConfig, item_id))
    commit_or_400(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/ai-suggestions/generate/")
def generate_ai_suggestions(db: DbSession, current_user: CurrentUser, payload: dict = Body(...)):
    contract_id = payload.get("contract_id")
    if not contract_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请提供contract_id")
    if current_user.role != "reviewer" or not current_user.reviewer_level:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前用户不是审核员或未设置审核员层级")
    contract = get_or_404(db, models.Contract, int(contract_id))
    task = None
    if payload.get("review_task_id"):
        task = get_or_404(db, models.ReviewTask, int(payload["review_task_id"]))
        task.reviewer_id = current_user.id
        task.reviewer_level = current_user.reviewer_level
    return generate_reviewer_suggestions(db, contract, current_user, task)


@router.get("/ai-suggestions/get_by_task/")
def get_suggestions_by_task(request: Request, db: DbSession, _: CurrentUser):
    review_task_id = request.query_params.get("review_task_id")
    if not review_task_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请提供review_task_id参数")
    task = get_or_404(db, models.ReviewTask, int(review_task_id))
    if not task.result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="该审核任务尚未生成审核结果")
    data = task.result.review_data or {}
    suggestions = data.get("ai_suggestions")
    if not suggestions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="该审核任务尚未生成AI建议")
    return {
        "review_task_id": task.id,
        "reviewer_level": data.get("reviewer_level"),
        "generated_at": data.get("generated_at"),
        "suggestions": suggestions,
    }


@router.get("/ai-model-configs/get_available_models/")
def get_available_models(request: Request, _: CurrentUser):
    provider = request.query_params.get("provider", "siliconflow")
    siliconflow_models = [
        {"value": "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B", "label": "DeepSeek-R1-0528-Qwen3-8B (推荐)"},
        {"value": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B", "label": "DeepSeek-R1-Distill-Qwen-7B"},
        {"value": "deepseek-ai/DeepSeek-V3", "label": "DeepSeek-V3"},
        {"value": "Qwen/Qwen2.5-72B-Instruct", "label": "Qwen2.5-72B-Instruct"},
        {"value": "Qwen/Qwen2.5-32B-Instruct", "label": "Qwen2.5-32B-Instruct"},
        {"value": "Qwen/Qwen2.5-14B-Instruct", "label": "Qwen2.5-14B-Instruct"},
        {"value": "Qwen/Qwen2.5-7B-Instruct", "label": "Qwen2.5-7B-Instruct"},
        {"value": "THUDM/glm-4-9b-chat", "label": "GLM-4-9B-Chat"},
        {"value": "meta-llama/Llama-3.1-70B-Instruct", "label": "Llama-3.1-70B-Instruct"},
    ]
    return {
        "provider": provider,
        "models": siliconflow_models if provider == "siliconflow" else [{"value": "deepseek-v4-pro", "label": "deepseek-v4-pro"}],
    }


@router.get("/ai-model-configs/get_default/")
def get_default_ai_config(db: DbSession, _: CurrentUser):
    item = db.query(models.AIModelConfig).filter(models.AIModelConfig.is_default.is_(True), models.AIModelConfig.is_active.is_(True)).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到系统默认配置")
    return serialize_ai_model_config(item)


@router.post("/ai-model-configs/chat/")
def ai_chat(db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    message = (payload.get("message") or "").strip()
    if not message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="消息内容不能为空")
    try:
        ai = AIService(db)
        response = ai.chat(message, payload.get("history") or [])
        return {"response": response, "model": ai.model if ai.enabled else None}
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"AI对话失败: {exc}")


@router.get("/ai-model-configs/")
def list_ai_configs(request: Request, db: DbSession, _: CurrentUser):
    query = db.query(models.AIModelConfig).options(selectinload(models.AIModelConfig.created_by), selectinload(models.AIModelConfig.updated_by))
    query = apply_filters(
        query,
        models.AIModelConfig,
        request,
        filter_fields=["provider", "is_active", "is_default"],
        ordering_fields=["is_default", "created_at"],
        default_ordering=["-is_default", "-created_at"],
        aliases=AI_CONFIG_ALIASES,
    )
    return paginate(query, request, serialize_ai_model_config)


@router.post("/ai-model-configs/", status_code=status.HTTP_201_CREATED)
def create_ai_config(db: DbSession, current_user: CurrentUser, payload: dict = Body(...)):
    validate_ai_config_payload(payload)
    if payload.get("is_default"):
        db.query(models.AIModelConfig).update({"is_default": False})
    item = create_item(
        db,
        models.AIModelConfig,
        payload,
        aliases=AI_CONFIG_ALIASES,
        readonly={"id", "created_at", "updated_at", "created_by_id", "updated_by_id"},
        extra={"created_by_id": current_user.id},
    )
    return serialize_ai_model_config(item)


@router.get("/ai-model-configs/{item_id}/")
def retrieve_ai_config(item_id: int, db: DbSession, _: CurrentUser):
    return serialize_ai_model_config(get_or_404(db, models.AIModelConfig, item_id))


@router.patch("/ai-model-configs/{item_id}/")
@router.put("/ai-model-configs/{item_id}/")
def update_ai_config(item_id: int, db: DbSession, current_user: CurrentUser, payload: dict = Body(...)):
    validate_ai_config_payload(payload)
    if payload.get("is_default"):
        db.query(models.AIModelConfig).filter(models.AIModelConfig.id != item_id).update({"is_default": False})
    item = update_item(
        db,
        get_or_404(db, models.AIModelConfig, item_id),
        payload,
        aliases=AI_CONFIG_ALIASES,
        readonly={"id", "created_at", "updated_at", "created_by_id", "updated_by_id"},
        extra={"updated_by_id": current_user.id},
    )
    return serialize_ai_model_config(item)


@router.delete("/ai-model-configs/{item_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_ai_config(item_id: int, db: DbSession, _: CurrentUser):
    db.delete(get_or_404(db, models.AIModelConfig, item_id))
    commit_or_400(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/ai-model-configs/{item_id}/set_default/")
def set_default_ai_config(item_id: int, db: DbSession, _: CurrentUser):
    item = get_or_404(db, models.AIModelConfig, item_id)
    db.query(models.AIModelConfig).filter(models.AIModelConfig.id != item.id).update({"is_default": False})
    item.is_default = True
    item.is_active = True
    commit_or_400(db)
    return {"message": "已设置为系统默认配置", "config": serialize_ai_model_config(item)}


@router.post("/ai-model-configs/{item_id}/test_connection/")
def test_ai_connection(item_id: int, db: DbSession, _: CurrentUser):
    item = get_or_404(db, models.AIModelConfig, item_id)
    if not item.api_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="API密钥未配置")
    try:
        result = AIService(db, item).test_connection()
        return result
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"API连接测试失败: {exc}")


def validate_ai_config_payload(payload: dict):
    available_models = payload.get("available_models") or []
    default_model = payload.get("default_model") or ""
    if default_model and available_models and default_model not in available_models:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="默认模型必须在可用模型列表中")

