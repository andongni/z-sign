import os
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Body, File, HTTPException, Request, Response, UploadFile, status
from sqlalchemy.orm import selectinload

from app import models
from app.api.deps import CurrentUser, DbSession
from app.api.router_utils import (
    apply_filters,
    commit_or_400,
    create_item,
    delete_item,
    get_or_404,
    paginate,
    update_item,
)
from app.core.config import get_settings
from app.serializers import serialize_contract, serialize_contract_version, serialize_template, serialize_user_habit
from app.services import generate_contract_content


router = APIRouter(prefix="/contracts", tags=["contracts"])
settings = get_settings()

CONTRACT_ALIASES = {"template": "template_id", "drafter": "drafter_id"}
TEMPLATE_ALIASES = {"created_by": "created_by_id"}
HABIT_ALIASES = {"user": "user_id"}


def contract_query(db: DbSession):
    return db.query(models.Contract).options(
        selectinload(models.Contract.drafter),
        selectinload(models.Contract.template),
        selectinload(models.Contract.versions).selectinload(models.ContractVersion.changed_by),
    )


@router.post("/upload/")
async def upload_contract_file(_: CurrentUser, file: UploadFile = File(...)):
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="未找到文件")
    if len(raw) > settings.upload_max_size:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件大小不能超过10MB")

    file_ext = Path(file.filename or "").suffix.lower()
    if file_ext not in {".doc", ".docx", ".pdf"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不支持的文件类型，仅支持 .doc, .docx, .pdf")

    upload_dir = settings.media_root / "contracts" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{uuid.uuid4().hex}{file_ext}"
    file_path = upload_dir / file_name
    file_path.write_bytes(raw)
    relative_path = str(Path("contracts") / "uploads" / file_name)
    content = parse_contract_file(file_path, file_ext)
    return {"file_path": relative_path, "content": content, "message": "文件上传成功"}


def parse_contract_file(file_path: Path, file_ext: str) -> dict:
    content = {"text": "", "html": "", "title": "", "metadata": {}}
    try:
        if file_ext in {".doc", ".docx"}:
            from docx import Document

            doc = Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs]
            content["text"] = "\n".join(paragraphs)
            content["html"] = "<br>".join(f"<p>{p}</p>" for p in paragraphs)
            title = (doc.core_properties.title or "").strip()
            if not title:
                title = next((p.strip() for p in paragraphs if p.strip()), "")
            content["title"] = title[:200]
            content["metadata"] = {"paragraph_count": len(paragraphs), "word_count": len(content["text"].split())}
        elif file_ext == ".pdf":
            import fitz

            doc = fitz.open(file_path)
            text_parts = []
            html_parts = []
            for index in range(len(doc)):
                page_text = doc[index].get_text()
                text_parts.append(page_text)
                html_parts.append(f'<div class="page"><h3>第{index + 1}页</h3><p>{page_text.replace(chr(10), "<br>")}</p></div>')
            content["text"] = "\n\n".join(text_parts)
            content["html"] = "".join(html_parts)
            metadata_title = (doc.metadata or {}).get("title") or ""
            first_line = next((line.strip() for line in content["text"].splitlines() if line.strip()), "")
            content["title"] = (metadata_title.strip() or first_line)[:200]
            content["metadata"] = {"page_count": len(doc), "word_count": len(content["text"].split())}
            doc.close()
    except Exception as exc:
        content["error"] = f"解析文件时出错: {exc}"
    return content


@router.get("/contracts/")
def list_contracts(request: Request, db: DbSession, _: CurrentUser):
    query = contract_query(db)
    query = apply_filters(
        query,
        models.Contract,
        request,
        filter_fields=["contract_type", "industry", "status", "drafter", "title", "contract_no"],
        search_fields=["title", "contract_no"],
        ordering_fields=["created_at", "updated_at", "title"],
        default_ordering=["-created_at"],
        aliases=CONTRACT_ALIASES,
    )
    return paginate(query, request, serialize_contract)


@router.post("/contracts/", status_code=status.HTTP_201_CREATED)
def create_contract(db: DbSession, current_user: CurrentUser, payload: dict = Body(...)):
    contract_no = payload.get("contract_no") or f"CT{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"
    extra = {"contract_no": contract_no, "drafter_id": current_user.id}
    item = create_item(
        db,
        models.Contract,
        payload,
        aliases=CONTRACT_ALIASES,
        readonly={"id", "created_at", "updated_at", "current_version", "drafter_id"},
        extra=extra,
    )
    return serialize_contract(item)


@router.post("/contracts/generate_content/")
def generate_content(db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    contract_type = payload.get("contract_type")
    if not contract_type:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="合同类型不能为空")

    template = None
    template_id = payload.get("template_id")
    if template_id:
        template = (
            db.query(models.Template)
            .filter(models.Template.id == template_id, models.Template.is_deleted.is_(False))
            .first()
        )
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模板不存在")

    return generate_contract_content(
        db,
        contract_type=contract_type,
        industry=payload.get("industry", ""),
        template=template,
        basic_info=payload.get("basic_info") or {},
    )


@router.get("/contracts/{item_id}/")
def retrieve_contract(item_id: int, db: DbSession, _: CurrentUser):
    item = contract_query(db).filter(models.Contract.id == item_id, models.Contract.is_deleted.is_(False)).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资源不存在")
    return serialize_contract(item)


@router.patch("/contracts/{item_id}/")
@router.put("/contracts/{item_id}/")
def update_contract(item_id: int, db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    item = get_or_404(db, models.Contract, item_id)
    item = update_item(
        db,
        item,
        payload,
        aliases=CONTRACT_ALIASES,
        readonly={"id", "created_at", "updated_at", "contract_no", "current_version", "drafter_id"},
    )
    return serialize_contract(item)


@router.delete("/contracts/{item_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_contract(item_id: int, db: DbSession, _: CurrentUser):
    delete_item(db, get_or_404(db, models.Contract, item_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/contracts/{item_id}/create_version/", status_code=status.HTTP_201_CREATED)
def create_contract_version(item_id: int, db: DbSession, current_user: CurrentUser, payload: dict = Body(...)):
    contract = get_or_404(db, models.Contract, item_id)
    new_version = contract.current_version + 1
    version = models.ContractVersion(
        contract_id=contract.id,
        version=new_version,
        content=payload.get("content", contract.content),
        file_path=payload.get("file_path", contract.file_path),
        change_summary=payload.get("change_summary") or f"编辑合同内容 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        changed_by_id=current_user.id,
    )
    db.add(version)
    contract.current_version = new_version
    commit_or_400(db)
    db.refresh(version)
    return serialize_contract_version(version)


@router.get("/contracts/{item_id}/versions/")
def list_contract_versions(item_id: int, db: DbSession, _: CurrentUser):
    contract = get_or_404(db, models.Contract, item_id)
    versions = (
        db.query(models.ContractVersion)
        .options(selectinload(models.ContractVersion.changed_by))
        .filter(models.ContractVersion.contract_id == contract.id, models.ContractVersion.is_deleted.is_(False))
        .order_by(models.ContractVersion.version.desc())
        .all()
    )
    return [serialize_contract_version(version) for version in versions]


@router.post("/contracts/{item_id}/rollback/")
def rollback_contract(item_id: int, db: DbSession, current_user: CurrentUser, payload: dict = Body(...)):
    contract = get_or_404(db, models.Contract, item_id)
    version_num = payload.get("version")
    if not version_num:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请指定要回滚的版本号")
    version = (
        db.query(models.ContractVersion)
        .filter(
            models.ContractVersion.contract_id == contract.id,
            models.ContractVersion.version == int(version_num),
            models.ContractVersion.is_deleted.is_(False),
        )
        .first()
    )
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"版本 {version_num} 不存在")
    if contract.current_version == int(version_num):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该版本已经是当前版本，无需回滚")

    contract.content = version.content
    contract.file_path = version.file_path
    new_version = contract.current_version + 1
    reason = payload.get("reason") or ""
    summary = f"回滚到版本 {version_num}" + (f" - {reason}" if reason else f"（由 {current_user.username} 执行）")
    db.add(
        models.ContractVersion(
            contract_id=contract.id,
            version=new_version,
            content=version.content,
            file_path=version.file_path,
            change_summary=summary,
            changed_by_id=current_user.id,
        )
    )
    contract.current_version = new_version
    commit_or_400(db)
    return {"message": f"已成功回滚到版本 {version_num}", "new_version": new_version, "rolled_back_to": int(version_num)}


@router.get("/templates/")
def list_templates(request: Request, db: DbSession, _: CurrentUser):
    query = db.query(models.Template).options(selectinload(models.Template.created_by))
    query = apply_filters(
        query,
        models.Template,
        request,
        filter_fields=["contract_type", "industry", "is_public", "is_enterprise", "name"],
        search_fields=["name", "description"],
        ordering_fields=["usage_count", "created_at"],
        default_ordering=["-usage_count", "-created_at"],
        aliases=TEMPLATE_ALIASES,
    )
    return paginate(query, request, serialize_template)


@router.post("/templates/", status_code=status.HTTP_201_CREATED)
def create_template(db: DbSession, current_user: CurrentUser, payload: dict = Body(...)):
    item = create_item(
        db,
        models.Template,
        payload,
        aliases=TEMPLATE_ALIASES,
        readonly={"id", "created_at", "updated_at", "usage_count", "created_by_id"},
        extra={"created_by_id": current_user.id},
    )
    return serialize_template(item)


@router.get("/templates/{item_id}/")
def retrieve_template(item_id: int, db: DbSession, _: CurrentUser):
    return serialize_template(get_or_404(db, models.Template, item_id))


@router.patch("/templates/{item_id}/")
@router.put("/templates/{item_id}/")
def update_template(item_id: int, db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    item = get_or_404(db, models.Template, item_id)
    item = update_item(
        db,
        item,
        payload,
        aliases=TEMPLATE_ALIASES,
        readonly={"id", "created_at", "updated_at", "usage_count", "created_by_id"},
    )
    return serialize_template(item)


@router.delete("/templates/{item_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(item_id: int, db: DbSession, _: CurrentUser):
    delete_item(db, get_or_404(db, models.Template, item_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/templates/{item_id}/use/")
def use_template(item_id: int, db: DbSession, _: CurrentUser):
    item = get_or_404(db, models.Template, item_id)
    item.usage_count += 1
    commit_or_400(db)
    return {"message": "模板使用次数已更新"}


@router.get("/habits/")
def list_habits(request: Request, db: DbSession, current_user: CurrentUser):
    query = db.query(models.UserHabit).filter(models.UserHabit.user_id == current_user.id)
    query = apply_filters(
        query,
        models.UserHabit,
        request,
        filter_fields=["habit_type", "user"],
        default_ordering=["-updated_at"],
        aliases=HABIT_ALIASES,
    )
    return paginate(query, request, serialize_user_habit)


@router.post("/habits/", status_code=status.HTTP_201_CREATED)
def create_habit(db: DbSession, current_user: CurrentUser, payload: dict = Body(...)):
    item = create_item(
        db,
        models.UserHabit,
        payload,
        aliases=HABIT_ALIASES,
        readonly={"id", "created_at", "updated_at", "user_id"},
        extra={"user_id": current_user.id},
    )
    return serialize_user_habit(item)


@router.post("/habits/update_habit/")
def update_user_habit(db: DbSession, current_user: CurrentUser, payload: dict = Body(...)):
    habit_type = payload.get("habit_type")
    habit_key = payload.get("habit_key")
    if not habit_type or not habit_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="habit_type和habit_key不能为空")

    habit = (
        db.query(models.UserHabit)
        .filter(
            models.UserHabit.user_id == current_user.id,
            models.UserHabit.habit_type == habit_type,
            models.UserHabit.habit_key == habit_key,
        )
        .first()
    )
    if not habit:
        habit = models.UserHabit(
            user_id=current_user.id,
            habit_type=habit_type,
            habit_key=habit_key,
            habit_value=payload.get("habit_value"),
        )
        db.add(habit)
    else:
        habit.habit_value = payload.get("habit_value")
        habit.frequency += 1
        habit.last_used_at = datetime.now()
    commit_or_400(db)
    db.refresh(habit)
    return serialize_user_habit(habit)


@router.patch("/habits/{item_id}/")
@router.put("/habits/{item_id}/")
def update_habit(item_id: int, db: DbSession, current_user: CurrentUser, payload: dict = Body(...)):
    item = (
        db.query(models.UserHabit)
        .filter(models.UserHabit.id == item_id, models.UserHabit.user_id == current_user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资源不存在")
    item = update_item(db, item, payload, aliases=HABIT_ALIASES, readonly={"id", "created_at", "updated_at", "user_id"})
    return serialize_user_habit(item)


@router.delete("/habits/{item_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_habit(item_id: int, db: DbSession, current_user: CurrentUser):
    item = (
        db.query(models.UserHabit)
        .filter(models.UserHabit.id == item_id, models.UserHabit.user_id == current_user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资源不存在")
    db.delete(item)
    commit_or_400(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
