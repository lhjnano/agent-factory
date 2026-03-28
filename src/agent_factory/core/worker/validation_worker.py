from typing import TYPE_CHECKING, Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
import asyncio

from .base_worker import BaseWorker, WorkerType, WorkerResult, WorkerConfig

if TYPE_CHECKING:
    from ..work import Work
    from ..agent_pool import AgentInstance


@dataclass
class ValidationRule:
    name: str
    validator: Callable[[Any], bool]
    error_message: str = "Validation failed"


@dataclass
class ValidationWorkerConfig(WorkerConfig):
    strict_mode: bool = False
    fail_fast: bool = True
    collect_all_errors: bool = False
    custom_validators: Dict[str, Callable] = field(default_factory=dict)


class ValidationWorker(BaseWorker):
    def __init__(
        self,
        agent: "AgentInstance",
        config: Optional[ValidationWorkerConfig] = None
    ):
        super().__init__(WorkerType.VALIDATION, agent, config or ValidationWorkerConfig())
        self._validation_count: int = 0
        self._passed_count: int = 0
        self._failed_count: int = 0
        self._validators: Dict[str, List[ValidationRule]] = {}
        self._register_default_validators()
    
    def _register_default_validators(self):
        self._validators["output"] = [
            ValidationRule(
                name="not_empty",
                validator=lambda x: x is not None and x != "",
                error_message="Output is empty"
            ),
            ValidationRule(
                name="is_dict_or_list",
                validator=lambda x: isinstance(x, (dict, list)),
                error_message="Output must be dict or list"
            )
        ]
        
        self._validators["type"] = [
            ValidationRule(
                name="valid_type",
                validator=lambda x: x in ["problem_definition", "data_collection", "design_development", "training_optimization", "evaluation_validation", "deployment_monitoring"],
                error_message="Invalid work type"
            )
        ]
    
    def register_validator(self, category: str, rule: ValidationRule):
        if category not in self._validators:
            self._validators[category] = []
        self._validators[category].append(rule)
    
    def register_custom_validator(self, name: str, validator: Callable):
        self.config.custom_validators[name] = validator
    
    async def execute(self, work: "Work") -> WorkerResult:
        started_at = datetime.now()
        
        try:
            if work.inputs.get("validation_type") == "output":
                result = await self._validate_output(work)
            elif work.inputs.get("validation_type") == "schema":
                result = await self._validate_schema(work)
            elif work.inputs.get("validation_type") == "custom":
                result = await self._validate_custom(work)
            else:
                result = await self._validate_work(work)
            
            self._validation_count += 1
            if result["valid"]:
                self._passed_count += 1
            else:
                self._failed_count += 1
            
            return WorkerResult(
                success=result["valid"],
                output=result,
                metrics={
                    "validation_count": self._validation_count,
                    "passed": self._passed_count,
                    "failed": self._failed_count
                },
                started_at=started_at,
                completed_at=datetime.now()
            )
            
        except Exception as e:
            self._validation_count += 1
            self._failed_count += 1
            
            return WorkerResult(
                success=False,
                error=f"Validation error: {str(e)}",
                started_at=started_at,
                completed_at=datetime.now()
            )
    
    async def _validate_work(self, work: "Work") -> Dict[str, Any]:
        errors = []
        warnings = []
        
        if not work.name or len(work.name.strip()) == 0:
            errors.append("Work name is empty")
        
        if not work.description or len(work.description.strip()) == 0:
            if self.config.strict_mode:
                errors.append("Work description is empty")
            else:
                warnings.append("Work description is empty")
        
        if work.estimated_tokens <= 0:
            errors.append("Invalid estimated tokens")
        
        if work.timeout_seconds <= 0:
            errors.append("Invalid timeout")
        
        if work.dependencies:
            for dep_id in work.dependencies:
                if not isinstance(dep_id, str) or len(dep_id) == 0:
                    errors.append(f"Invalid dependency: {dep_id}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "work_id": work.work_id
        }
    
    async def _validate_output(self, work: "Work") -> Dict[str, Any]:
        output = work.inputs.get("output")
        rules = self._validators.get("output", [])
        
        errors = []
        for rule in rules:
            try:
                if not rule.validator(output):
                    errors.append(f"{rule.name}: {rule.error_message}")
                    if self.config.fail_fast:
                        break
            except Exception as e:
                errors.append(f"{rule.name}: Validator error - {str(e)}")
                if self.config.fail_fast:
                    break
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "output_type": type(output).__name__
        }
    
    async def _validate_schema(self, work: "Work") -> Dict[str, Any]:
        data = work.inputs.get("data", {})
        schema = work.inputs.get("schema", {})
        
        errors = []
        
        for field_name, field_schema in schema.items():
            if field_schema.get("required", False) and field_name not in data:
                errors.append(f"Missing required field: {field_name}")
                if self.config.fail_fast:
                    break
            
            if field_name in data:
                value = data[field_name]
                expected_type = field_schema.get("type")
                
                if expected_type and not isinstance(value, expected_type):
                    errors.append(f"Field {field_name} has wrong type: expected {expected_type}, got {type(value)}")
                    if self.config.fail_fast:
                        break
                
                min_value = field_schema.get("min")
                max_value = field_schema.get("max")
                
                if min_value is not None and value < min_value:
                    errors.append(f"Field {field_name} is below minimum: {value} < {min_value}")
                
                if max_value is not None and value > max_value:
                    errors.append(f"Field {field_name} exceeds maximum: {value} > {max_value}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "fields_checked": len(schema)
        }
    
    async def _validate_custom(self, work: "Work") -> Dict[str, Any]:
        validator_name = work.inputs.get("validator_name")
        data = work.inputs.get("data")
        
        if validator_name not in self.config.custom_validators:
            return {
                "valid": False,
                "errors": [f"Unknown validator: {validator_name}"]
            }
        
        validator = self.config.custom_validators[validator_name]
        
        try:
            if asyncio.iscoroutinefunction(validator):
                is_valid = await validator(data)
            else:
                is_valid = validator(data)
            
            return {
                "valid": bool(is_valid),
                "validator": validator_name
            }
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Validator {validator_name} failed: {str(e)}"]
            }
    
    def get_validation_stats(self) -> dict:
        return {
            **self.get_stats(),
            "validation_count": self._validation_count,
            "passed_count": self._passed_count,
            "failed_count": self._failed_count,
            "pass_rate": self._passed_count / self._validation_count if self._validation_count > 0 else 0,
            "registered_validators": list(self._validators.keys())
        }
