from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON

from app.core.database import Base


BigInt = BigInteger().with_variant(Integer, "sqlite")


def now() -> datetime:
    return datetime.now()


class TimestampMixin:
    created_at = Column(DateTime, default=now, nullable=False)
    updated_at = Column(DateTime, default=now, onupdate=now, nullable=False)


class Department(Base, TimestampMixin):
    __tablename__ = "users_department"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    parent_id = Column(BigInt, ForeignKey("users_department.id"), nullable=True)
    code = Column(String(50), unique=True, nullable=True)
    description = Column(Text, default="", nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    parent = relationship("Department", remote_side=[id])


class User(Base, TimestampMixin):
    __tablename__ = "users_user"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    password = Column(String(128), nullable=False)
    last_login = Column(DateTime, nullable=True)
    is_superuser = Column(Boolean, default=False, nullable=False)
    username = Column(String(150), unique=True, nullable=False)
    email = Column(String(254), unique=True, nullable=False)
    real_name = Column(String(100), default="", nullable=False)
    phone = Column(String(20), default="", nullable=False)
    avatar = Column(String(500), default="", nullable=False)
    department_id = Column(BigInt, ForeignKey("users_department.id"), nullable=True)
    role = Column(String(50), default="drafter", nullable=False)
    reviewer_level = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_staff = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    department = relationship("Department")
    user_roles = relationship("UserRole", cascade="all, delete-orphan", back_populates="user")


class Permission(Base, TimestampMixin):
    __tablename__ = "users_permission"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    code = Column(String(100), unique=True, nullable=False)
    resource = Column(String(100), default="", nullable=False)
    action = Column(String(50), default="", nullable=False)
    description = Column(Text, default="", nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)


class Role(Base, TimestampMixin):
    __tablename__ = "users_role"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text, default="", nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    role_permissions = relationship("RolePermission", cascade="all, delete-orphan", back_populates="role")


class RolePermission(Base):
    __tablename__ = "users_role_permission"
    __table_args__ = (UniqueConstraint("role_id", "permission_id"),)

    id = Column(BigInt, primary_key=True, autoincrement=True)
    role_id = Column(BigInt, ForeignKey("users_role.id"), nullable=False)
    permission_id = Column(BigInt, ForeignKey("users_permission.id"), nullable=False)
    created_at = Column(DateTime, default=now, nullable=False)

    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission")


class UserRole(Base):
    __tablename__ = "users_user_role"
    __table_args__ = (UniqueConstraint("user_id", "role_id"),)

    id = Column(BigInt, primary_key=True, autoincrement=True)
    user_id = Column(BigInt, ForeignKey("users_user.id"), nullable=False)
    role_id = Column(BigInt, ForeignKey("users_role.id"), nullable=False)
    created_at = Column(DateTime, default=now, nullable=False)

    user = relationship("User", back_populates="user_roles")
    role = relationship("Role")


class AuditLog(Base):
    __tablename__ = "users_audit_log"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    user_id = Column(BigInt, ForeignKey("users_user.id"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), default="", nullable=False)
    resource_id = Column(BigInt, nullable=True)
    ip_address = Column(String(39), nullable=True)
    user_agent = Column(String(500), default="", nullable=False)
    request_data = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)
    status = Column(String(20), default="", nullable=False)
    error_message = Column(Text, default="", nullable=False)
    created_at = Column(DateTime, default=now, nullable=False)

    user = relationship("User")


class Template(Base, TimestampMixin):
    __tablename__ = "contracts_template"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    contract_type = Column(String(50), nullable=False)
    industry = Column(String(50), default="", nullable=False)
    category = Column(String(50), default="", nullable=False)
    content = Column(Text, nullable=False)
    description = Column(Text, default="", nullable=False)
    tags = Column(JSON, nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    is_enterprise = Column(Boolean, default=False, nullable=False)
    created_by_id = Column(BigInt, ForeignKey("users_user.id"), nullable=True)
    enterprise_id = Column(BigInt, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    created_by = relationship("User", foreign_keys=[created_by_id])


class Contract(Base, TimestampMixin):
    __tablename__ = "contracts_contract"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    contract_no = Column(String(100), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    contract_type = Column(String(50), nullable=False)
    industry = Column(String(50), default="", nullable=False)
    status = Column(String(50), default="draft", nullable=False)
    content = Column(JSON, nullable=True)
    file_path = Column(String(500), default="", nullable=False)
    file_format = Column(String(20), default="", nullable=False)
    template_id = Column(BigInt, ForeignKey("contracts_template.id"), nullable=True)
    drafter_id = Column(BigInt, ForeignKey("users_user.id"), nullable=False)
    current_version = Column(Integer, default=1, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    template = relationship("Template")
    drafter = relationship("User", foreign_keys=[drafter_id])
    versions = relationship("ContractVersion", cascade="all, delete-orphan", back_populates="contract")
    review_tasks = relationship("ReviewTask", cascade="all, delete-orphan", back_populates="contract")


class ContractVersion(Base):
    __tablename__ = "contracts_contract_version"
    __table_args__ = (UniqueConstraint("contract_id", "version"),)

    id = Column(BigInt, primary_key=True, autoincrement=True)
    contract_id = Column(BigInt, ForeignKey("contracts_contract.id"), nullable=False)
    version = Column(Integer, nullable=False)
    content = Column(JSON, nullable=True)
    file_path = Column(String(500), default="", nullable=False)
    change_summary = Column(Text, default="", nullable=False)
    changed_by_id = Column(BigInt, ForeignKey("users_user.id"), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=now, nullable=False)

    contract = relationship("Contract", back_populates="versions")
    changed_by = relationship("User", foreign_keys=[changed_by_id])


class UserHabit(Base, TimestampMixin):
    __tablename__ = "contracts_user_habit"
    __table_args__ = (UniqueConstraint("user_id", "habit_type", "habit_key"),)

    id = Column(BigInt, primary_key=True, autoincrement=True)
    user_id = Column(BigInt, ForeignKey("users_user.id"), nullable=False)
    habit_type = Column(String(50), nullable=False)
    habit_key = Column(String(200), nullable=False)
    habit_value = Column(JSON, nullable=True)
    frequency = Column(Integer, default=1, nullable=False)
    last_used_at = Column(DateTime, nullable=True)

    user = relationship("User")


class ReviewTask(Base, TimestampMixin):
    __tablename__ = "reviews_review_task"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    contract_id = Column(BigInt, ForeignKey("contracts_contract.id"), nullable=False)
    contract_version = Column(Integer, nullable=True)
    task_type = Column(String(50), default="auto", nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    priority = Column(Integer, default=0, nullable=False)
    reviewer_id = Column(BigInt, ForeignKey("users_user.id"), nullable=True)
    reviewer_level = Column(String(20), nullable=True)
    review_levels = Column(JSON, nullable=True)
    reviewer_assignments = Column(JSON, nullable=True)
    celery_task_id = Column(String(255), default="", nullable=False)
    progress = Column(JSON, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, default="", nullable=False)
    created_by_id = Column(BigInt, ForeignKey("users_user.id"), nullable=True)

    contract = relationship("Contract", back_populates="review_tasks")
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    result = relationship("ReviewResult", cascade="all, delete-orphan", back_populates="review_task", uselist=False)


class ReviewResult(Base):
    __tablename__ = "reviews_review_result"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    review_task_id = Column(BigInt, ForeignKey("reviews_review_task.id"), unique=True, nullable=False)
    contract_id = Column(BigInt, ForeignKey("contracts_contract.id"), nullable=False)
    overall_score = Column(Numeric(5, 2), nullable=True)
    risk_level = Column(String(20), default="", nullable=False)
    risk_count = Column(Integer, default=0, nullable=False)
    summary = Column(Text, default="", nullable=False)
    report_path = Column(String(500), default="", nullable=False)
    report_format = Column(String(20), default="", nullable=False)
    review_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=now, nullable=False)

    review_task = relationship("ReviewTask", back_populates="result")
    contract = relationship("Contract")
    opinions = relationship("ReviewOpinion", cascade="all, delete-orphan", back_populates="review_result")


class ReviewOpinion(Base, TimestampMixin):
    __tablename__ = "reviews_review_opinion"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    review_result_id = Column(BigInt, ForeignKey("reviews_review_result.id"), nullable=False)
    reviewer_id = Column(BigInt, ForeignKey("users_user.id"), nullable=True)
    clause_id = Column(String(100), default="", nullable=False)
    clause_content = Column(Text, default="", nullable=False)
    opinion_type = Column(String(50), default="", nullable=False)
    risk_level = Column(String(20), default="", nullable=False)
    opinion_content = Column(Text, nullable=False)
    legal_basis = Column(Text, default="", nullable=False)
    suggestion = Column(Text, default="", nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    review_result = relationship("ReviewResult", back_populates="opinions")
    reviewer = relationship("User")


class ReviewCycle(Base, TimestampMixin):
    __tablename__ = "reviews_review_cycle"
    __table_args__ = (UniqueConstraint("contract_id", "cycle_no"),)

    id = Column(BigInt, primary_key=True, autoincrement=True)
    contract_id = Column(BigInt, ForeignKey("contracts_contract.id"), nullable=False)
    cycle_no = Column(Integer, nullable=False)
    review_result_id = Column(BigInt, ForeignKey("reviews_review_result.id"), nullable=True)
    opinion_summary = Column(Text, default="", nullable=False)
    modification_summary = Column(Text, default="", nullable=False)
    status = Column(String(50), default="reviewing", nullable=False)
    submitted_by_id = Column(BigInt, ForeignKey("users_user.id"), nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    modified_by_id = Column(BigInt, ForeignKey("users_user.id"), nullable=True)
    modified_at = Column(DateTime, nullable=True)

    contract = relationship("Contract")
    review_result = relationship("ReviewResult")
    submitted_by = relationship("User", foreign_keys=[submitted_by_id])
    modified_by = relationship("User", foreign_keys=[modified_by_id])


class ReviewFocusConfig(Base, TimestampMixin):
    __tablename__ = "reviews_review_focus_config"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    level = Column(String(20), unique=True, nullable=False)
    level_name = Column(String(100), nullable=False)
    focus_points = Column(JSON, nullable=False)
    focus_description = Column(Text, nullable=False)
    review_standards = Column(Text, default="", nullable=False)
    attention_items = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by_id = Column(BigInt, ForeignKey("users_user.id"), nullable=True)
    updated_by_id = Column(BigInt, ForeignKey("users_user.id"), nullable=True)

    created_by = relationship("User", foreign_keys=[created_by_id])
    updated_by = relationship("User", foreign_keys=[updated_by_id])


class AIModelConfig(Base, TimestampMixin):
    __tablename__ = "reviews_ai_model_config"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    provider = Column(String(50), default="siliconflow", nullable=False)
    api_key = Column(String(500), nullable=False)
    api_base_url = Column(String(500), default="https://api.siliconflow.cn/v1", nullable=False)
    available_models = Column(JSON, nullable=False, default=list)
    default_model = Column(String(100), default="", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    description = Column(Text, default="", nullable=False)
    temperature = Column(Float, default=0.7, nullable=False)
    max_tokens = Column(Integer, default=2000, nullable=False)
    timeout = Column(Integer, default=30, nullable=False)
    created_by_id = Column(BigInt, ForeignKey("users_user.id"), nullable=True)
    updated_by_id = Column(BigInt, ForeignKey("users_user.id"), nullable=True)

    created_by = relationship("User", foreign_keys=[created_by_id])
    updated_by = relationship("User", foreign_keys=[updated_by_id])


class ReviewRule(Base, TimestampMixin):
    __tablename__ = "rules_review_rule"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    rule_code = Column(String(100), unique=True, nullable=False)
    rule_name = Column(String(200), nullable=False)
    rule_type = Column(String(50), nullable=False)
    industry = Column(String(50), default="", nullable=False)
    category = Column(String(50), default="", nullable=False)
    priority = Column(Integer, default=0, nullable=False)
    rule_content = Column(JSON, nullable=False)
    risk_level = Column(String(20), default="", nullable=False)
    legal_basis = Column(Text, default="", nullable=False)
    description = Column(Text, default="", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_by_id = Column(BigInt, ForeignKey("users_user.id"), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    created_by = relationship("User")


class RuleMatch(Base):
    __tablename__ = "rules_rule_match"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    review_task_id = Column(BigInt, ForeignKey("reviews_review_task.id"), nullable=False)
    rule_id = Column(BigInt, ForeignKey("rules_review_rule.id"), nullable=False)
    contract_id = Column(BigInt, nullable=False)
    matched_clause = Column(Text, default="", nullable=False)
    match_score = Column(Numeric(5, 2), nullable=True)
    match_result = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=now, nullable=False)

    rule = relationship("ReviewRule")
    review_task = relationship("ReviewTask")


class ContractClause(Base, TimestampMixin):
    __tablename__ = "clauses_contract_clause"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    contract_id = Column(BigInt, ForeignKey("contracts_contract.id"), nullable=False)
    contract_version = Column(Integer, nullable=True)
    clause_no = Column(String(50), default="", nullable=False)
    clause_type = Column(String(50), nullable=False)
    clause_title = Column(String(500), default="", nullable=False)
    clause_content = Column(Text, nullable=False)
    start_position = Column(Integer, nullable=True)
    end_position = Column(Integer, nullable=True)
    extracted_data = Column(JSON, nullable=True)
    confidence = Column(Numeric(5, 2), nullable=True)
    is_confirmed = Column(Boolean, default=False, nullable=False)
    confirmed_by_id = Column(BigInt, ForeignKey("users_user.id"), nullable=True)
    confirmed_at = Column(DateTime, nullable=True)

    contract = relationship("Contract")
    confirmed_by = relationship("User")


class RiskIdentification(Base):
    __tablename__ = "risks_risk_identification"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    review_result_id = Column(BigInt, ForeignKey("reviews_review_result.id"), nullable=False)
    contract_id = Column(BigInt, nullable=False)
    clause_id = Column(BigInt, ForeignKey("clauses_contract_clause.id"), nullable=True)
    risk_type = Column(String(50), nullable=False)
    risk_category = Column(String(50), default="", nullable=False)
    risk_level = Column(String(20), nullable=False)
    risk_description = Column(Text, nullable=False)
    risk_location = Column(String(200), default="", nullable=False)
    legal_basis = Column(Text, default="", nullable=False)
    suggestion = Column(Text, default="", nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    handled_by_id = Column(BigInt, ForeignKey("users_user.id"), nullable=True)
    handled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=now, nullable=False)

    review_result = relationship("ReviewResult")
    clause = relationship("ContractClause")
    handled_by = relationship("User")


class ComparisonTask(Base):
    __tablename__ = "comparisons_comparison_task"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    task_type = Column(String(50), nullable=False)
    source_contract_id = Column(BigInt, ForeignKey("contracts_contract.id"), nullable=True)
    target_contract_id = Column(BigInt, ForeignKey("contracts_contract.id"), nullable=True)
    source_version = Column(Integer, nullable=True)
    target_version = Column(Integer, nullable=True)
    template_id = Column(BigInt, ForeignKey("contracts_template.id"), nullable=True)
    status = Column(String(50), default="pending", nullable=False)
    result_data = Column(JSON, nullable=True)
    created_by_id = Column(BigInt, ForeignKey("users_user.id"), nullable=True)
    created_at = Column(DateTime, default=now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    source_contract = relationship("Contract", foreign_keys=[source_contract_id])
    target_contract = relationship("Contract", foreign_keys=[target_contract_id])
    template = relationship("Template")
    created_by = relationship("User")
    diffs = relationship("ComparisonDiff", cascade="all, delete-orphan", back_populates="comparison_task")


class ComparisonDiff(Base):
    __tablename__ = "comparisons_comparison_diff"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    comparison_task_id = Column(BigInt, ForeignKey("comparisons_comparison_task.id"), nullable=False)
    diff_type = Column(String(50), nullable=False)
    diff_level = Column(String(50), default="", nullable=False)
    source_content = Column(Text, default="", nullable=False)
    target_content = Column(Text, default="", nullable=False)
    clause_id = Column(String(100), default="", nullable=False)
    risk_level = Column(String(20), default="", nullable=False)
    created_at = Column(DateTime, default=now, nullable=False)

    comparison_task = relationship("ComparisonTask", back_populates="diffs")


class KnowledgeEntity(Base, TimestampMixin):
    __tablename__ = "knowledge_knowledge_entity"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False)
    entity_name = Column(String(500), nullable=False)
    entity_code = Column(String(200), unique=True, nullable=True)
    description = Column(Text, default="", nullable=False)
    properties = Column(JSON, nullable=True)
    source = Column(String(200), default="", nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)


class KnowledgeRelation(Base, TimestampMixin):
    __tablename__ = "knowledge_knowledge_relation"
    __table_args__ = (UniqueConstraint("source_entity_id", "target_entity_id", "relation_type"),)

    id = Column(BigInt, primary_key=True, autoincrement=True)
    source_entity_id = Column(BigInt, ForeignKey("knowledge_knowledge_entity.id"), nullable=False)
    target_entity_id = Column(BigInt, ForeignKey("knowledge_knowledge_entity.id"), nullable=False)
    relation_type = Column(String(50), nullable=False)
    relation_properties = Column(JSON, nullable=True)
    confidence = Column(Numeric(5, 2), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    source_entity = relationship("KnowledgeEntity", foreign_keys=[source_entity_id])
    target_entity = relationship("KnowledgeEntity", foreign_keys=[target_entity_id])


class Regulation(Base, TimestampMixin):
    __tablename__ = "knowledge_regulation"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    regulation_no = Column(String(100), default="", nullable=False)
    regulation_type = Column(String(50), default="", nullable=False)
    publish_date = Column(Date, nullable=True)
    effective_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    content = Column(Text, default="", nullable=False)
    source_url = Column(String(500), default="", nullable=False)
    entity_id = Column(BigInt, ForeignKey("knowledge_knowledge_entity.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    entity = relationship("KnowledgeEntity")


class LegalCase(Base, TimestampMixin):
    __tablename__ = "knowledge_case"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    case_no = Column(String(100), default="", nullable=False)
    case_title = Column(String(500), nullable=False)
    case_type = Column(String(50), default="", nullable=False)
    court = Column(String(200), default="", nullable=False)
    judge_date = Column(Date, nullable=True)
    case_summary = Column(Text, default="", nullable=False)
    case_content = Column(Text, default="", nullable=False)
    related_clauses = Column(JSON, nullable=True)
    entity_id = Column(BigInt, ForeignKey("knowledge_knowledge_entity.id"), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    entity = relationship("KnowledgeEntity")


class Recommendation(Base):
    __tablename__ = "recommendations_recommendation"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    user_id = Column(BigInt, ForeignKey("users_user.id"), nullable=False)
    contract_id = Column(BigInt, ForeignKey("contracts_contract.id"), nullable=True)
    recommendation_type = Column(String(50), nullable=False)
    recommendation_context = Column(String(50), default="", nullable=False)
    item_type = Column(String(50), default="", nullable=False)
    item_id = Column(BigInt, nullable=True)
    item_content = Column(Text, default="", nullable=False)
    score = Column(Numeric(5, 2), nullable=True)
    reason = Column(Text, default="", nullable=False)
    is_accepted = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=now, nullable=False)

    user = relationship("User")
    contract = relationship("Contract")
