from fastapi import APIRouter, Body, Request, Response, status
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
from app.core.security import make_password
from app.serializers import (
    serialize_audit_log,
    serialize_department,
    serialize_permission,
    serialize_role,
    serialize_user,
)


router = APIRouter(prefix="/users", tags=["users"])

USER_ALIASES = {"department": "department_id"}
DEPT_ALIASES = {"parent": "parent_id"}
USER_READONLY = {"id", "created_at", "updated_at", "last_login", "is_superuser", "is_staff"}


@router.get("/departments/")
def list_departments(request: Request, db: DbSession, _: CurrentUser):
    query = db.query(models.Department)
    query = apply_filters(
        query,
        models.Department,
        request,
        filter_fields=["parent", "name", "code"],
        search_fields=["name", "code"],
        ordering_fields=["created_at", "name"],
        default_ordering=["created_at"],
        aliases=DEPT_ALIASES,
    )
    return paginate(query, request, serialize_department)


@router.post("/departments/", status_code=status.HTTP_201_CREATED)
def create_department(db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    item = create_item(db, models.Department, payload, aliases=DEPT_ALIASES, readonly={"id", "created_at", "updated_at"})
    return serialize_department(item)


@router.get("/departments/{item_id}/")
def retrieve_department(item_id: int, db: DbSession, _: CurrentUser):
    return serialize_department(get_or_404(db, models.Department, item_id))


@router.patch("/departments/{item_id}/")
@router.put("/departments/{item_id}/")
def update_department(item_id: int, db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    item = get_or_404(db, models.Department, item_id)
    item = update_item(db, item, payload, aliases=DEPT_ALIASES, readonly={"id", "created_at", "updated_at"})
    return serialize_department(item)


@router.delete("/departments/{item_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(item_id: int, db: DbSession, _: CurrentUser):
    delete_item(db, get_or_404(db, models.Department, item_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/users/me/")
def me(current_user: CurrentUser):
    return serialize_user(current_user)


@router.patch("/users/update_me/")
@router.put("/users/update_me/")
def update_me(db: DbSession, current_user: CurrentUser, payload: dict = Body(...)):
    extra = {}
    if password := payload.pop("password", None):
        extra["password"] = make_password(password)
    item = update_item(db, current_user, payload, aliases=USER_ALIASES, readonly=USER_READONLY, extra=extra)
    return serialize_user(item)


@router.get("/users/")
def list_users(request: Request, db: DbSession, _: CurrentUser):
    query = db.query(models.User).options(
        selectinload(models.User.department),
        selectinload(models.User.user_roles).selectinload(models.UserRole.role),
    )
    query = apply_filters(
        query,
        models.User,
        request,
        filter_fields=["role", "department", "is_active", "username", "email", "real_name"],
        search_fields=["username", "email", "real_name"],
        ordering_fields=["created_at", "username"],
        default_ordering=["created_at"],
        aliases=USER_ALIASES,
    )
    return paginate(query, request, serialize_user)


@router.post("/users/", status_code=status.HTTP_201_CREATED)
def create_user(db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    role_ids = payload.pop("role_ids", None)
    password = payload.pop("password", None)
    extra = {"password": make_password(password or "123456")}
    item = create_item(db, models.User, payload, aliases=USER_ALIASES, readonly=USER_READONLY, extra=extra)
    if role_ids:
        assign_user_roles(db, item, role_ids)
    db.refresh(item)
    return serialize_user(item)


@router.get("/users/{item_id}/")
def retrieve_user(item_id: int, db: DbSession, _: CurrentUser):
    item = (
        db.query(models.User)
        .options(selectinload(models.User.department), selectinload(models.User.user_roles).selectinload(models.UserRole.role))
        .filter(models.User.id == item_id, models.User.is_deleted.is_(False))
        .first()
    )
    if not item:
        item = get_or_404(db, models.User, item_id)
    return serialize_user(item)


@router.patch("/users/{item_id}/")
@router.put("/users/{item_id}/")
def update_user(item_id: int, db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    item = get_or_404(db, models.User, item_id)
    role_ids = payload.pop("role_ids", None)
    extra = {}
    if password := payload.pop("password", None):
        extra["password"] = make_password(password)
    item = update_item(db, item, payload, aliases=USER_ALIASES, readonly=USER_READONLY, extra=extra)
    if role_ids is not None:
        assign_user_roles(db, item, role_ids)
        db.refresh(item)
    return serialize_user(item)


@router.delete("/users/{item_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(item_id: int, db: DbSession, _: CurrentUser):
    delete_item(db, get_or_404(db, models.User, item_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/users/{item_id}/assign_roles/")
def assign_roles(item_id: int, db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    item = get_or_404(db, models.User, item_id)
    assign_user_roles(db, item, payload.get("role_ids", []))
    db.refresh(item)
    return serialize_user(item)


def assign_user_roles(db: DbSession, user: models.User, role_ids: list[int]) -> None:
    db.query(models.UserRole).filter(models.UserRole.user_id == user.id).delete()
    for role_id in role_ids:
        role = db.query(models.Role).filter(models.Role.id == role_id, models.Role.is_deleted.is_(False)).first()
        if role:
            db.add(models.UserRole(user_id=user.id, role_id=role.id))
    commit_or_400(db)


@router.get("/roles/")
def list_roles(request: Request, db: DbSession, _: CurrentUser):
    query = db.query(models.Role).options(selectinload(models.Role.role_permissions).selectinload(models.RolePermission.permission))
    query = apply_filters(
        query,
        models.Role,
        request,
        filter_fields=["name", "code"],
        search_fields=["name", "code"],
        ordering_fields=["created_at", "name"],
        default_ordering=["created_at"],
    )
    return paginate(query, request, serialize_role)


@router.post("/roles/", status_code=status.HTTP_201_CREATED)
def create_role(db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    permission_ids = payload.pop("permission_ids", [])
    item = create_item(db, models.Role, payload, readonly={"id", "created_at", "updated_at"})
    assign_role_permissions(db, item, permission_ids)
    db.refresh(item)
    return serialize_role(item)


@router.get("/roles/{item_id}/")
def retrieve_role(item_id: int, db: DbSession, _: CurrentUser):
    return serialize_role(get_or_404(db, models.Role, item_id))


@router.patch("/roles/{item_id}/")
@router.put("/roles/{item_id}/")
def update_role(item_id: int, db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    item = get_or_404(db, models.Role, item_id)
    permission_ids = payload.pop("permission_ids", None)
    item = update_item(db, item, payload, readonly={"id", "created_at", "updated_at"})
    if permission_ids is not None:
        assign_role_permissions(db, item, permission_ids)
        db.refresh(item)
    return serialize_role(item)


@router.delete("/roles/{item_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(item_id: int, db: DbSession, _: CurrentUser):
    delete_item(db, get_or_404(db, models.Role, item_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/roles/{item_id}/assign_permissions/")
def assign_permissions(item_id: int, db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    item = get_or_404(db, models.Role, item_id)
    assign_role_permissions(db, item, payload.get("permission_ids", []))
    db.refresh(item)
    return serialize_role(item)


def assign_role_permissions(db: DbSession, role: models.Role, permission_ids: list[int]) -> None:
    db.query(models.RolePermission).filter(models.RolePermission.role_id == role.id).delete()
    for permission_id in permission_ids:
        permission = (
            db.query(models.Permission)
            .filter(models.Permission.id == permission_id, models.Permission.is_deleted.is_(False))
            .first()
        )
        if permission:
            db.add(models.RolePermission(role_id=role.id, permission_id=permission.id))
    commit_or_400(db)


@router.get("/permissions/")
def list_permissions(request: Request, db: DbSession, _: CurrentUser):
    query = db.query(models.Permission)
    query = apply_filters(
        query,
        models.Permission,
        request,
        filter_fields=["name", "code", "resource", "action"],
        search_fields=["name", "code"],
        ordering_fields=["created_at", "name"],
        default_ordering=["created_at"],
    )
    return paginate(query, request, serialize_permission)


@router.post("/permissions/", status_code=status.HTTP_201_CREATED)
def create_permission(db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    item = create_item(db, models.Permission, payload, readonly={"id", "created_at", "updated_at"})
    return serialize_permission(item)


@router.get("/permissions/{item_id}/")
def retrieve_permission(item_id: int, db: DbSession, _: CurrentUser):
    return serialize_permission(get_or_404(db, models.Permission, item_id))


@router.patch("/permissions/{item_id}/")
@router.put("/permissions/{item_id}/")
def update_permission(item_id: int, db: DbSession, _: CurrentUser, payload: dict = Body(...)):
    item = get_or_404(db, models.Permission, item_id)
    item = update_item(db, item, payload, readonly={"id", "created_at", "updated_at"})
    return serialize_permission(item)


@router.delete("/permissions/{item_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_permission(item_id: int, db: DbSession, _: CurrentUser):
    delete_item(db, get_or_404(db, models.Permission, item_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/audit-logs/")
def list_audit_logs(request: Request, db: DbSession, _: CurrentUser):
    query = db.query(models.AuditLog).options(selectinload(models.AuditLog.user))
    query = apply_filters(
        query,
        models.AuditLog,
        request,
        filter_fields=["user", "action", "status", "resource_type"],
        ordering_fields=["created_at"],
        default_ordering=["-created_at"],
        aliases={"user": "user_id"},
    )
    return paginate(query, request, serialize_audit_log)


@router.get("/audit-logs/{item_id}/")
def retrieve_audit_log(item_id: int, db: DbSession, _: CurrentUser):
    return serialize_audit_log(get_or_404(db, models.AuditLog, item_id))

