from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from enum import Enum
import json


class DocumentType(Enum):
    PROBLEM_DEFINITION = "problem_definition"
    PROJECT_PLAN = "project_plan"
    DATA_SPECIFICATION = "data_specification"
    DATA_QUALITY_REPORT = "data_quality_report"
    ARCHITECTURE_DESIGN = "architecture_design"
    API_SPECIFICATION = "api_specification"
    TECH_STACK = "tech_stack"
    TRAINING_LOG = "training_log"
    HYPERPARAMETER_CONFIG = "hyperparameter_config"
    MODEL_EVALUATION = "model_evaluation"
    DEPLOYMENT_GUIDE = "deployment_guide"
    OPERATIONS_MANUAL = "operations_manual"
    INCIDENT_RESPONSE = "incident_response"
    CHANGE_LOG = "change_log"
    WORK_SUMMARY = "work_summary"


@dataclass
class DocumentTemplate:
    document_type: DocumentType
    title: str
    description: str
    required_sections: List[str]
    optional_sections: List[str] = field(default_factory=list)
    metadata_fields: List[str] = field(default_factory=list)


@dataclass
class Document:
    document_id: str
    document_type: DocumentType
    work_id: str
    agent_id: str
    title: str
    content: str
    sections: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    status: str = "draft"


DOCUMENT_TEMPLATES: Dict[DocumentType, DocumentTemplate] = {
    DocumentType.PROBLEM_DEFINITION: DocumentTemplate(
        document_type=DocumentType.PROBLEM_DEFINITION,
        title="Problem Definition",
        description="문제 정의 및 범위 설정 문서",
        required_sections=["problem_statement", "objectives", "constraints", "success_criteria"],
        optional_sections=["stakeholders", "assumptions", "risks"],
        metadata_fields=["project_name", "priority", "deadline"]
    ),
    DocumentType.PROJECT_PLAN: DocumentTemplate(
        document_type=DocumentType.PROJECT_PLAN,
        title="Project Plan",
        description="프로젝트 계획서",
        required_sections=["phases", "timeline", "resources", "milestones"],
        optional_sections=["dependencies", "risks", "contingency_plans"],
        metadata_fields=["project_name", "start_date", "end_date"]
    ),
    DocumentType.DATA_SPECIFICATION: DocumentTemplate(
        document_type=DocumentType.DATA_SPECIFICATION,
        title="Data Specification",
        description="데이터 명세서",
        required_sections=["data_sources", "schema", "volume", "quality_requirements"],
        optional_sections=["sample_data", "transformations", "validation_rules"],
        metadata_fields=["data_version", "owner", "last_updated"]
    ),
    DocumentType.ARCHITECTURE_DESIGN: DocumentTemplate(
        document_type=DocumentType.ARCHITECTURE_DESIGN,
        title="Architecture Design",
        description="아키텍처 설계서",
        required_sections=["overview", "components", "data_flow", "interfaces"],
        optional_sections=["diagrams", "scalability", "security"],
        metadata_fields=["version", "author", "review_status"]
    ),
    DocumentType.MODEL_EVALUATION: DocumentTemplate(
        document_type=DocumentType.MODEL_EVALUATION,
        title="Model Evaluation Report",
        description="모델 평가 보고서",
        required_sections=["metrics", "confusion_matrix", "conclusions"],
        optional_sections=["cross_validation", "feature_importance", "comparison"],
        metadata_fields=["model_version", "dataset_version", "evaluated_at"]
    ),
    DocumentType.DEPLOYMENT_GUIDE: DocumentTemplate(
        document_type=DocumentType.DEPLOYMENT_GUIDE,
        title="Deployment Guide",
        description="배포 가이드",
        required_sections=["prerequisites", "steps", "verification", "rollback"],
        optional_sections=["troubleshooting", "configuration", "monitoring"],
        metadata_fields=["target_environment", "version", "approved_by"]
    ),
    DocumentType.WORK_SUMMARY: DocumentTemplate(
        document_type=DocumentType.WORK_SUMMARY,
        title="Work Summary",
        description="작업 요약 문서",
        required_sections=["summary", "inputs", "outputs", "metrics"],
        optional_sections=["issues", "lessons_learned", "next_steps"],
        metadata_fields=["work_id", "agent_id", "duration"]
    ),
}


class DocumentationManager:
    def __init__(self, output_dir: Optional[Path] = None):
        self._documents: Dict[str, Document] = {}
        self._work_documents: Dict[str, List[str]] = {}
        self._output_dir = output_dir or Path.home() / "docs"
    
    def create_document(
        self,
        document_type: DocumentType,
        work_id: str,
        agent_id: str,
        sections: Dict[str, str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        template = DOCUMENT_TEMPLATES.get(document_type)
        if not template:
            raise ValueError(f"Unknown document type: {document_type}")
        
        missing_sections = set(template.required_sections) - set(sections.keys())
        if missing_sections:
            raise ValueError(f"Missing required sections: {missing_sections}")
        
        document_id = f"{work_id}_{document_type.value}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        content = self._generate_content(template, sections)
        
        document = Document(
            document_id=document_id,
            document_type=document_type,
            work_id=work_id,
            agent_id=agent_id,
            title=template.title,
            content=content,
            sections=sections,
            metadata=metadata or {}
        )
        
        self._documents[document_id] = document
        
        if work_id not in self._work_documents:
            self._work_documents[work_id] = []
        self._work_documents[work_id].append(document_id)
        
        return document
    
    def _generate_content(self, template: DocumentTemplate, sections: Dict[str, str]) -> str:
        lines = [f"# {template.title}", "", f"*{template.description}*", ""]
        
        for section_name in template.required_sections + template.optional_sections:
            if section_name in sections:
                lines.append(f"## {section_name.replace('_', ' ').title()}")
                lines.append("")
                lines.append(sections[section_name])
                lines.append("")
        
        return "\n".join(lines)
    
    def update_document(self, document_id: str, sections: Dict[str, str]) -> Document:
        document = self._documents.get(document_id)
        if not document:
            raise ValueError(f"Document not found: {document_id}")
        
        document.sections.update(sections)
        document.content = self._generate_content(
            DOCUMENT_TEMPLATES[document.document_type],
            document.sections
        )
        document.updated_at = datetime.now()
        document.version += 1
        
        return document
    
    def get_document(self, document_id: str) -> Optional[Document]:
        return self._documents.get(document_id)
    
    def get_work_documents(self, work_id: str) -> List[Document]:
        doc_ids = self._work_documents.get(work_id, [])
        return [self._documents[doc_id] for doc_id in doc_ids if doc_id in self._documents]
    
    def save_document(self, document_id: str, output_path: Optional[Path] = None) -> Path:
        document = self._documents.get(document_id)
        if not document:
            raise ValueError(f"Document not found: {document_id}")
        
        output_dir = output_path or self._output_dir / document.document_type.value
        output_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = output_dir / f"{document.document_id}.md"
        file_path.write_text(document.content, encoding="utf-8")
        
        return file_path
    
    def generate_work_documentation(self, work_id: str, work_data: Dict[str, Any], agent_id: str) -> Document:
        sections = {
            "summary": f"Work: {work_data.get('name', 'Unknown')}\n\n{work_data.get('description', '')}",
            "inputs": self._format_dict(work_data.get("inputs", {})),
            "outputs": self._format_dict(work_data.get("outputs", {})),
            "metrics": self._format_dict(work_data.get("metrics", {}))
        }
        
        if work_data.get("issues"):
            sections["issues"] = work_data["issues"]
        
        if work_data.get("lessons_learned"):
            sections["lessons_learned"] = work_data["lessons_learned"]
        
        metadata = {
            "work_id": work_id,
            "agent_id": agent_id,
            "duration": work_data.get("actual_duration_seconds", 0),
            "tokens_used": work_data.get("actual_tokens", 0)
        }
        
        return self.create_document(
            document_type=DocumentType.WORK_SUMMARY,
            work_id=work_id,
            agent_id=agent_id,
            sections=sections,
            metadata=metadata
        )
    
    def _format_dict(self, data: Dict[str, Any]) -> str:
        if not data:
            return "No data"
        lines = []
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"- **{key}:**")
                for k, v in value.items():
                    lines.append(f"  - {k}: {v}")
            elif isinstance(value, list):
                lines.append(f"- **{key}:** {', '.join(str(v) for v in value)}")
            else:
                lines.append(f"- **{key}:** {value}")
        return "\n".join(lines)
    
    def get_documentation_summary(self) -> Dict[str, Any]:
        by_type: Dict[DocumentType, int] = {}
        for doc in self._documents.values():
            by_type[doc.document_type] = by_type.get(doc.document_type, 0) + 1
        
        return {
            "total_documents": len(self._documents),
            "by_type": {dt.value: count for dt, count in by_type.items()},
            "work_with_docs": len(self._work_documents)
        }
