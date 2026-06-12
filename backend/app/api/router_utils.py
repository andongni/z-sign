from datetime import date, datetime
from typing import Any, Callable

from fastapi import HTTPException, Request, status
from sqlalchemy import BigInteger, Boolean, Date, DateTime, Integer, String, Text, asc, desc, func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query, Session


Serializer = Callable[[Any], dict[str, Any]]


def parse_bool(raw: Any) -> bool:
    if isinstance(raw, bool):
        return raw
    return str(raw).lower() in {"1", "true", "yes", "y", "on"}


def convert_for_column(column: Any, raw: Any) -> Any:
    if raw == "" and column.nullable:
        return None

    column_type = column.type
    if isinstance(column_type, Boolean):
        return parse_bool(raw)
    if isinstance(column_type, (Integer, BigInteger)):
        if raw is None or raw == "":
            return None
        return int(raw)
    if isinstance(column_type, DateTime):
        if not raw:
            return None
        if isinstance(raw, datetime):
            return raw
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).replace(tzinfo=None)
    if isinstance(column_type, Date):
        if not raw:
            return None
        if isinstance(raw, date):
            return raw
        return date.fromisoformat(str(raw)[:10])
    return raw


def payload_to_columns(
    model: type,
    payload: dict[str, Any],
    aliases: dict[str, str] | None = None,
    readonly: set[str] | None = None,
) -> dict[str, Any]:
    aliases = aliases or {}
    readonly = readonly or set()
    columns = model.__table__.columns
    data: dict[str, Any] = {}
    for public_name, raw_value in payload.items():
        attr_name = aliases.get(public_name, public_name)
        if attr_name in readonly or attr_name not in columns:
            continue
        data[attr_name] = convert_for_column(columns[attr_name], raw_value)
    return data


def apply_filters(
    query: Query,
    model: type,
    request: Request,
    filter_fields: list[str] | None = None,
    search_fields: list[str] | None = None,
    ordering_fields: list[str] | None = None,
    default_ordering: list[str] | None = None,
    aliases: dict[str, str] | None = None,
) -> Query:
    aliases = aliases or {}
    filter_fields = filter_fields or []
    search_fields = search_fields or []
    ordering_fields = ordering_fields or []
    default_ordering = default_ordering or []

    if hasattr(model, "is_deleted"):
        query = query.filter(getattr(model, "is_deleted").is_(False))

    for field in filter_fields:
        raw = request.query_params.get(field)
        if raw is None or raw == "":
            continue
        attr_name = aliases.get(field, field)
        if not hasattr(model, attr_name):
            continue
        column = getattr(model, attr_name)
        table_column = model.__table__.columns[attr_name]
        if isinstance(table_column.type, (String, Text)):
            query = query.filter(column.ilike(f"%{raw}%"))
        else:
            query = query.filter(column == convert_for_column(table_column, raw))

    search = request.query_params.get("search")
    if search and search_fields:
        clauses = []
        for field in search_fields:
            attr_name = aliases.get(field, field)
            if not hasattr(model, attr_name):
                continue
            column = getattr(model, attr_name)
            if isinstance(model.__table__.columns[attr_name].type, (String, Text)):
                clauses.append(column.ilike(f"%{search}%"))
        if clauses:
            query = query.filter(or_(*clauses))

    ordering = request.query_params.get("ordering")
    order_specs = [ordering] if ordering else default_ordering
    for spec in order_specs:
        if not spec:
            continue
        direction = desc if spec.startswith("-") else asc
        field = spec[1:] if spec.startswith("-") else spec
        attr_name = aliases.get(field, field)
        if ordering_fields and field not in ordering_fields:
            continue
        if hasattr(model, attr_name):
            query = query.order_by(direction(getattr(model, attr_name)))

    return query


def paginate(query: Query, request: Request, serializer: Serializer) -> dict[str, Any]:
    page = max(int(request.query_params.get("page", 1) or 1), 1)
    page_size = min(max(int(request.query_params.get("page_size", 20) or 20), 1), 1000)

    count = query.order_by(None).count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    next_url = None
    previous_url = None
    if page * page_size < count:
        next_url = str(request.url.include_query_params(page=page + 1, page_size=page_size))
    if page > 1:
        previous_url = str(request.url.include_query_params(page=page - 1, page_size=page_size))

    return {
        "count": count,
        "next": next_url,
        "previous": previous_url,
        "results": [serializer(item) for item in items],
    }


def get_or_404(db: Session, model: type, item_id: int, *, include_deleted: bool = False) -> Any:
    query = db.query(model).filter(model.id == item_id)
    if not include_deleted and hasattr(model, "is_deleted"):
        query = query.filter(getattr(model, "is_deleted").is_(False))
    item = query.first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资源不存在")
    return item


def commit_or_400(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"数据约束错误: {exc.orig}")


def create_item(
    db: Session,
    model: type,
    payload: dict[str, Any],
    *,
    aliases: dict[str, str] | None = None,
    readonly: set[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> Any:
    data = payload_to_columns(model, payload, aliases=aliases, readonly=readonly)
    data.update(extra or {})
    item = model(**data)
    db.add(item)
    commit_or_400(db)
    db.refresh(item)
    return item


def update_item(
    db: Session,
    item: Any,
    payload: dict[str, Any],
    *,
    aliases: dict[str, str] | None = None,
    readonly: set[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> Any:
    data = payload_to_columns(type(item), payload, aliases=aliases, readonly=readonly)
    data.update(extra or {})
    for key, val in data.items():
        setattr(item, key, val)
    commit_or_400(db)
    db.refresh(item)
    return item


def delete_item(db: Session, item: Any) -> None:
    if hasattr(item, "is_deleted"):
        item.is_deleted = True
    else:
        db.delete(item)
    commit_or_400(db)


def count_for(db: Session, model: type, *conditions: Any) -> int:
    query = db.query(func.count(model.id))
    if conditions:
        query = query.filter(*conditions)
    return int(query.scalar() or 0)
