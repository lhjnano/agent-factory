import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from pathlib import Path

from .work import Work, WorkStatus, WorkPriority, WorkResult, WorkQueue, PlanStatus
from .raci import RACI, RACIRole
from .documentation import DocumentationManager, DocumentType
from .agent_pool import AgentPool, AgentInstance, AgentStatus
from .toc_supervisor import TOCSupervisor, BottleneckAnalysis


@dataclass
class WorkflowConfig:
    max_concurrent_works: int = 10
    default_timeout: float = 300.0
    auto_scale: bool = True
    auto_document: bool = True
    enable_toc: bool = True
    optimization_interval: float = 60.0
    token_budget: int = 1000000


@dataclass
class WorkflowResult:
    workflow_id: str
    status: str
    works_total: int
    works_completed: int
    works_failed: int
    total_tokens: int
    total_duration_seconds: float
    results: Dict[str, WorkResult] = field(default_factory=dict)
    bottlenecks: List[Dict[str, Any]] = field(default_factory=list)
    documents: List[str] = field(default_factory=list)


class MultiAgentOrchestrator:
    def __init__(self, config: Optional[WorkflowConfig] = None):
        self.config = config or WorkflowConfig()
        
        self.work_queue = WorkQueue()
        self.agent_pool = AgentPool()
        self.raci = RACI()
        self.doc_manager = DocumentationManager()
        self.toc_supervisor = TOCSupervisor(
            agent_pool=self.agent_pool,
            work_queue=self.work_queue,
            raci=self.raci
        )
        
        self._works: Dict[str, Work] = {}
        self._results: Dict[str, WorkResult] = {}
        self._running = False
        self._agent_factories: Dict[str, Callable] = {}
        self._work_handlers: Dict[str, Callable] = {}
        self._memory_storage = None
        self._filesystem_storage = None
    
    def set_mcp_sessions(self, memory_session=None, filesystem_session=None):
        self._memory_storage = memory_session
        self._filesystem_storage = filesystem_session
        
        self.toc_supervisor.set_mcp_sessions(memory_session, filesystem_session)
    
    def register_agent_factory(self, agent_type: str, factory: Callable[[], AgentInstance]):
        self._agent_factories[agent_type] = factory
    
    def register_work_handler(self, work_type: str, handler: Callable):
        self._work_handlers[work_type] = handler
    
    def register_agent(self, agent: AgentInstance):
        self.agent_pool.register_agent(agent)
    
    def create_work(
        self,
        name: str,
        description: str,
        work_type: str,
        agent_type: str,
        inputs: Dict[str, Any],
        dependencies: Optional[List[str]] = None,
        priority: WorkPriority = WorkPriority.MEDIUM,
        estimated_tokens: int = 1000,
        raci_roles: Optional[Dict[str, str]] = None
    ) -> Work:
        work_id = f"{work_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self._works)}"
        
        work = Work(
            work_id=work_id,
            name=name,
            description=description,
            work_type=work_type,
            agent_type=agent_type,
            priority=priority,
            dependencies=dependencies or [],
            inputs=inputs,
            estimated_tokens=estimated_tokens,
            timeout_seconds=self.config.default_timeout
        )
        
        if raci_roles:
            for agent_id, role_str in raci_roles.items():
                role = RACIRole(role_str.upper())
                self.raci.assign(work_id, agent_id, role)
            work.raci_roles = raci_roles
        
        self._works[work_id] = work
        return work
    
    async def submit_work(self, work: Work) -> str:
        await self.work_queue.enqueue(work)
        return work.work_id
    
    async def create_workflow_from_template(
        self,
        template_name: str,
        parameters: Dict[str, Any]
    ) -> List[str]:
        work_ids = []
        
        templates = {
            "ml_pipeline": self._create_ml_pipeline,
            "data_processing": self._create_data_pipeline,
            "web_development": self._create_web_dev_pipeline,
            "api_development": self._create_api_pipeline
        }
        
        template_func = templates.get(template_name)
        if template_func:
            works = await template_func(parameters)
            for work in works:
                work_id = await self.submit_work(work)
                work_ids.append(work_id)
        
        return work_ids
    
    async def _create_ml_pipeline(self, params: Dict[str, Any]) -> List[Work]:
        works = []
        
        work1 = self.create_work(
            name="Define Problem",
            description="문제 정의 및 프로젝트 계획",
            work_type="problem_definition",
            agent_type="problem_definition",
            inputs={"requirements": params.get("requirements", "")},
            priority=WorkPriority.HIGH
        )
        works.append(work1)
        
        work2 = self.create_work(
            name="Collect Data",
            description="데이터 수집 및 전처리",
            work_type="data_collection",
            agent_type="data_collection",
            inputs={"sources": params.get("data_sources", [])},
            dependencies=[work1.work_id],
            priority=WorkPriority.HIGH
        )
        works.append(work2)
        
        work3 = self.create_work(
            name="Design Architecture",
            description="모델 아키텍처 설계",
            work_type="design_development",
            agent_type="design_development",
            inputs={"problem_def": work1.work_id},
            dependencies=[work2.work_id],
            estimated_tokens=2000
        )
        works.append(work3)
        
        work4 = self.create_work(
            name="Train Model",
            description="모델 학습 및 최적화",
            work_type="training_optimization",
            agent_type="training_optimization",
            inputs={"architecture": work3.work_id},
            dependencies=[work3.work_id],
            estimated_tokens=5000
        )
        works.append(work4)
        
        work5 = self.create_work(
            name="Evaluate Model",
            description="모델 성능 평가",
            work_type="evaluation_validation",
            agent_type="evaluation_validation",
            inputs={"model": work4.work_id},
            dependencies=[work4.work_id]
        )
        works.append(work5)
        
        work6 = self.create_work(
            name="Deploy Model",
            description="모델 배포 및 모니터링 설정",
            work_type="deployment_monitoring",
            agent_type="deployment_monitoring",
            inputs={"model_path": work4.work_id},
            dependencies=[work5.work_id]
        )
        works.append(work6)
        
        return works
    
    async def _create_data_pipeline(self, params: Dict[str, Any]) -> List[Work]:
        works = []
        
        work1 = self.create_work(
            name="Extract Data",
            description="데이터 추출",
            work_type="data_collection",
            agent_type="data_collection",
            inputs={"sources": params.get("sources", [])}
        )
        works.append(work1)
        
        work2 = self.create_work(
            name="Transform Data",
            description="데이터 변환",
            work_type="data_collection",
            agent_type="data_collection",
            inputs={"data": work1.work_id},
            dependencies=[work1.work_id]
        )
        works.append(work2)
        
        work3 = self.create_work(
            name="Load Data",
            description="데이터 로드",
            work_type="deployment_monitoring",
            agent_type="deployment_monitoring",
            inputs={"data": work2.work_id},
            dependencies=[work2.work_id]
        )
        works.append(work3)
        
        return works
    
    async def _create_web_dev_pipeline(self, params: Dict[str, Any]) -> List[Work]:
        works = []
        
        work1 = self.create_work(
            name="Define Requirements",
            description="요구사항 정의",
            work_type="problem_definition",
            agent_type="problem_definition",
            inputs={"requirements": params.get("requirements", "")}
        )
        works.append(work1)
        
        work2 = self.create_work(
            name="Design Architecture",
            description="웹 아키텍처 설계",
            work_type="design_development",
            agent_type="design_development",
            inputs={"requirements": work1.work_id},
            dependencies=[work1.work_id],
            estimated_tokens=3000
        )
        works.append(work2)
        
        work3 = self.create_work(
            name="Implement Backend",
            description="백엔드 구현",
            work_type="design_development",
            agent_type="design_development",
            inputs={"architecture": work2.work_id},
            dependencies=[work2.work_id],
            estimated_tokens=5000
        )
        works.append(work3)
        
        work4 = self.create_work(
            name="Implement Frontend",
            description="프론트엔드 구현",
            work_type="design_development",
            agent_type="design_development",
            inputs={"architecture": work2.work_id},
            dependencies=[work2.work_id],
            estimated_tokens=4000
        )
        works.append(work4)
        
        work5 = self.create_work(
            name="Deploy",
            description="배포",
            work_type="deployment_monitoring",
            agent_type="deployment_monitoring",
            inputs={"backend": work3.work_id, "frontend": work4.work_id},
            dependencies=[work3.work_id, work4.work_id]
        )
        works.append(work5)
        
        return works
    
    async def _create_api_pipeline(self, params: Dict[str, Any]) -> List[Work]:
        works = []
        
        work1 = self.create_work(
            name="Design API",
            description="API 설계",
            work_type="design_development",
            agent_type="design_development",
            inputs={"spec": params.get("api_spec", "")}
        )
        works.append(work1)
        
        work2 = self.create_work(
            name="Implement API",
            description="API 구현",
            work_type="design_development",
            agent_type="design_development",
            inputs={"design": work1.work_id},
            dependencies=[work1.work_id],
            estimated_tokens=4000
        )
        works.append(work2)
        
        work3 = self.create_work(
            name="Test API",
            description="API 테스트",
            work_type="evaluation_validation",
            agent_type="evaluation_validation",
            inputs={"api": work2.work_id},
            dependencies=[work2.work_id]
        )
        works.append(work3)
        
        work4 = self.create_work(
            name="Deploy API",
            description="API 배포",
            work_type="deployment_monitoring",
            agent_type="deployment_monitoring",
            inputs={"api": work2.work_id},
            dependencies=[work3.work_id]
        )
        works.append(work4)
        
        return works
    
    async def start(self):
        self._running = True
        
        tasks = [
            asyncio.create_task(self._process_works()),
            asyncio.create_task(self._run_optimization_loop())
        ]
        
        await asyncio.gather(*tasks)
    
    async def stop(self):
        self._running = False
    
    async def _process_works(self):
        while self._running:
            try:
                completed_ids = {
                    wid for wid, work in self._works.items()
                    if work.status == WorkStatus.COMPLETED
                }
                
                for agent_type in self.agent_pool._type_index.keys():
                    agent = await self.agent_pool.select_agent(agent_type, "least_loaded")
                    if not agent:
                        continue
                    
                    work = await self.work_queue.dequeue([agent_type], completed_ids)
                    if not work:
                        continue
                    
                    asyncio.create_task(self._execute_work(work, agent))
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"Error processing works: {e}")
                await asyncio.sleep(1)
    
    async def _execute_work(self, work: Work, agent: AgentInstance):
        work.start(agent.agent_id)
        agent.assign_work(work.work_id)
        
        result = WorkResult(
            work_id=work.work_id,
            status=WorkStatus.RUNNING,
            started_at=datetime.now()
        )
        
        try:
            if work.require_plan_approval and not work.has_approved_plan():
                responsible_agents = self.raci.get_responsible_agents_for_plan_submission(work.work_id)
                accountable_agent = self.raci.get_accountable_agent_for_plan_approval(work.work_id)
                
                if agent.agent_id in responsible_agents:
                    print(f"[PLAN] Work '{work.name}' requires plan approval by RESPONSIBLE agent {agent.agent_id}")
                    print(f"[PLAN] Waiting for plan submission... (ACCOUNTABLE: {accountable_agent})")
                    
                    while work.needs_plan_approval():
                        await asyncio.sleep(1)
                    
                    if work.plan and work.plan.status == PlanStatus.APPROVED:
                        print(f"[PLAN] Plan approved for work '{work.name}'")
                    else:
                        raise Exception("Plan was rejected or not approved")
            
            handler = self._work_handlers.get(work.work_type)
            
            if handler:
                output = await asyncio.wait_for(
                    handler(work.inputs, agent),
                    timeout=work.timeout_seconds
                )
                result.output = output
                result.status = WorkStatus.COMPLETED
            else:
                output = await self._default_handler(work)
                result.output = output
                result.status = WorkStatus.COMPLETED
            
            result.completed_at = datetime.now()
            result.metrics = {
                "tokens_used": work.estimated_tokens,
                "duration_seconds": result.duration_seconds or 0
            }
            
            work.complete(result)
            
            if self.config.auto_document:
                doc = self.doc_manager.generate_work_documentation(
                    work_id=work.work_id,
                    work_data=work.to_dict(),
                    agent_id=agent.agent_id
                )
                result.documentation = doc.document_id
            
        except asyncio.TimeoutError:
            result.status = WorkStatus.FAILED
            result.error = "Timeout exceeded"
            work.fail("Timeout exceeded")
            
        except Exception as e:
            result.status = WorkStatus.FAILED
            result.error = str(e)
            work.fail(str(e))
            
            if work.can_retry():
                work.status = WorkStatus.PENDING
                await self.work_queue.enqueue(work)
        
        finally:
            agent.complete_work(
                tokens_used=result.metrics.get("tokens_used", 0),
                duration_seconds=result.duration_seconds or 0,
                success=result.status == WorkStatus.COMPLETED
            )
            
            self._results[work.work_id] = result
    
    async def _default_handler(self, work: Work) -> Dict[str, Any]:
        return {
            "work_id": work.work_id,
            "type": work.work_type,
            "status": "completed",
            "message": f"Work {work.name} completed successfully"
        }
    
    async def _run_optimization_loop(self):
        while self._running and self.config.enable_toc:
            try:
                await asyncio.sleep(self.config.optimization_interval)
                
                optimization_result = await self.toc_supervisor.optimize()
                
                if optimization_result.get("optimizations_applied"):
                    print(f"Applied optimizations: {len(optimization_result['optimizations_applied'])}")
                
            except Exception as e:
                print(f"Error in optimization loop: {e}")
    
    async def execute_workflow(
        self,
        works: Optional[List[Work]] = None,
        template: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> WorkflowResult:
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        if template:
            work_ids = await self.create_workflow_from_template(template, parameters or {})
            works = [self._works[wid] for wid in work_ids]
        
        if not works:
            return WorkflowResult(
                workflow_id=workflow_id,
                status="no_works",
                works_total=0,
                works_completed=0,
                works_failed=0,
                total_tokens=0,
                total_duration_seconds=0
            )
        
        for work in works:
            if work.work_id not in self._works:
                self._works[work.work_id] = work
            if work.status == WorkStatus.PENDING:
                await self.submit_work(work)
        
        self._running = True
        process_task = asyncio.create_task(self._process_works())
        
        try:
            while True:
                all_done = all(
                    w.status in [WorkStatus.COMPLETED, WorkStatus.FAILED, WorkStatus.CANCELLED]
                    for w in works
                )
                
                if all_done:
                    break
                
                await asyncio.sleep(0.1)
        finally:
            self._running = False
            process_task.cancel()
            try:
                await process_task
            except asyncio.CancelledError:
                pass
        
        for work in works:
            if work.status == WorkStatus.COMPLETED:
                result = self._results.get(work.work_id)
                if result:
                    self.toc_supervisor.record_work_completion(work, result)
        
        if self.config.enable_toc:
            final_analysis = await self.toc_supervisor.generate_final_analysis(works)
            
            await self.toc_supervisor.save_final_analysis(final_analysis)
            
            print("\n" + "=" * 80)
            print("TOC 최종 분석 보고서")
            print("=" * 80)
            print(f"\n## 작업 요약")
            print(f"  전체: {final_analysis['work_summary']['total']}")
            print(f"  완료: {final_analysis['work_summary']['completed']}")
            print(f"  실패: {final_analysis['work_summary']['failed']}")
            print(f"  성공률: {final_analysis['work_summary']['success_rate']:.1%}")
            
            token_analysis = final_analysis.get("token_analysis", {})
            if token_analysis.get("status") != "no_data":
                print(f"\n## Token 효율")
                print(f"  전체 효율: {token_analysis['overall_efficiency']:.1f}%")
                if token_analysis.get("potential_savings", 0) > 0:
                    savings_pct = token_analysis['potential_savings'] / token_analysis['total_actual'] * 100
                    print(f"  절감 가능: {token_analysis['potential_savings']:,} 토큰 ({savings_pct:.1f}%)")
            
            bottleneck_analysis = final_analysis.get("bottleneck_analysis", [])
            if bottleneck_analysis:
                print(f"\n## 병목 현상 ({len(bottleneck_analysis)}개 발견)")
                for bn in bottleneck_analysis:
                    print(f"  [{bn['severity'].upper()}] {bn['agent_type']}: {bn['recommendation']}")
            
            comparison = await self.toc_supervisor.compare_with_baselines()
            if comparison.get("status") == "success":
                print(f"\n## 기준 대비 비교")
                if comparison.get("improvements"):
                    print(f"  개선된 지표 ({len(comparison['improvements'])}개):")
                    for imp in comparison["improvements"][:3]:
                        print(f"    + {imp['metric']}: {imp['change_pct']:+.1f}%")
                if comparison.get("degradations"):
                    print(f"  저하된 지표 ({len(comparison['degradations'])}개):")
                    for deg in comparison["degradations"][:3]:
                        print(f"    - {deg['metric']}: {deg['change_pct']:+.1f}%")
            
            recommendations = final_analysis.get("recommendations", [])
            if recommendations:
                print(f"\n## 개선 제안 ({len(recommendations)}개)")
                for i, rec in enumerate(recommendations[:5], 1):
                    print(f"  {i}. [{rec['priority'].upper()}] {rec['title']}")
                    print(f"     {rec['expected_benefit']}")
            
            print(f"\n## 데이터 저장 위치")
            print(f"  Memory: toc_baselines, toc_bottleneck_history, toc_optimization_log, toc_work_history")
            print(f"  Filesystem: ~/.agents_toc/ (toc_baselines.json, etc.)")
            
            print("\n" + self.toc_supervisor.format_final_report(final_analysis))
        
        completed = sum(1 for w in works if w.status == WorkStatus.COMPLETED)
        failed = sum(1 for w in works if w.status == WorkStatus.FAILED)
        total_tokens = sum(w.actual_tokens for w in works)
        total_duration = sum(w.actual_duration_seconds for w in works)
        
        bottlenecks = [
            self.toc_supervisor._bottleneck_to_dict(b)
            for b in self.toc_supervisor._bottlenecks
        ]
        
        documents = []
        for work in works:
            if work.status == WorkStatus.COMPLETED:
                docs = self.doc_manager.get_work_documents(work.work_id)
                documents.extend([d.document_id for d in docs])
        
        return WorkflowResult(
            workflow_id=workflow_id,
            status="completed" if failed == 0 else "partial_failure",
            works_total=len(works),
            works_completed=completed,
            works_failed=failed,
            total_tokens=total_tokens,
            total_duration_seconds=total_duration,
            results=self._results,
            bottlenecks=bottlenecks,
            documents=documents
        )
    
    def get_status(self) -> Dict[str, Any]:
        pool_status = self.agent_pool.get_pool_status()
        toc_report = self.toc_supervisor.get_optimization_report()
        
        return {
            "pool_status": pool_status,
            "works": {
                "total": len(self._works),
                "pending": sum(1 for w in self._works.values() if w.status == WorkStatus.PENDING),
                "running": sum(1 for w in self._works.values() if w.status == WorkStatus.RUNNING),
                "completed": sum(1 for w in self._works.values() if w.status == WorkStatus.COMPLETED),
                "failed": sum(1 for w in self._works.values() if w.status == WorkStatus.FAILED)
            },
            "toc_report": toc_report,
            "raci_validation": self.raci.validate_all(),
            "documentation": self.doc_manager.get_documentation_summary()
        }
    
    def assign_raci(
        self,
        work_id: str,
        responsible: List[str],
        accountable: str,
        consulted: Optional[List[str]] = None,
        informed: Optional[List[str]] = None
    ):
        for agent_id in responsible:
            self.raci.assign(work_id, agent_id, RACIRole.RESPONSIBLE)
        
        self.raci.assign(work_id, accountable, RACIRole.ACCOUNTABLE)
        
        for agent_id in (consulted or []):
            self.raci.assign(work_id, agent_id, RACIRole.CONSULTED)
        
        for agent_id in (informed or []):
            self.raci.assign(work_id, agent_id, RACIRole.INFORMED)
    
    def generate_documentation(
        self,
        work_id: str,
        document_type: DocumentType,
        sections: Dict[str, str],
        metadata: Optional[Dict[str, Any]] = None
    ):
        work = self._works.get(work_id)
        if not work:
            raise ValueError(f"Work not found: {work_id}")
        
        return self.doc_manager.create_document(
            document_type=document_type,
            work_id=work_id,
            agent_id=work.assigned_agent or "unknown",
            sections=sections,
            metadata=metadata
        )

    def submit_work_plan(
        self,
        work_id: str,
        plan_content: Dict[str, Any],
        proposed_by: str
    ) -> Dict[str, Any]:
        work = self._works.get(work_id)
        if not work:
            raise ValueError(f"Work not found: {work_id}")
        
        responsible_agents = self.raci.get_responsible_agents_for_plan_submission(work_id)
        if proposed_by not in responsible_agents:
            raise ValueError(f"Agent {proposed_by} is not a RESPONSIBLE agent for this work")
        
        plan = work.submit_plan(plan_content, proposed_by)
        
        return {
            "work_id": work_id,
            "plan_id": plan.plan_id,
            "status": plan.status.value,
            "submitted_at": plan.submitted_at.isoformat() if plan.submitted_at else None,
            "message": "Plan submitted successfully. Waiting for ACCOUNTABLE agent approval."
        }

    def approve_work_plan(
        self,
        work_id: str,
        approved_by: str
    ) -> Dict[str, Any]:
        work = self._works.get(work_id)
        if not work:
            raise ValueError(f"Work not found: {work_id}")
        
        accountable_agent = self.raci.get_accountable_agent_for_plan_approval(work_id)
        if approved_by != accountable_agent:
            raise ValueError(f"Agent {approved_by} is not the ACCOUNTABLE agent for this work")
        
        if work.plan is None:
            raise ValueError("No plan has been submitted for this work")
        
        success = work.approve_plan(approved_by)
        
        if success:
            return {
                "work_id": work_id,
                "plan_id": work.plan.plan_id,
                "status": work.plan.status.value,
                "approved_at": work.plan.approved_at.isoformat() if work.plan.approved_at else None,
                "message": "Plan approved. Work can now proceed."
            }
        else:
            return {
                "work_id": work_id,
                "status": "error",
                "message": "Failed to approve plan"
            }

    def reject_work_plan(
        self,
        work_id: str,
        rejected_by: str,
        reason: str
    ) -> Dict[str, Any]:
        work = self._works.get(work_id)
        if not work:
            raise ValueError(f"Work not found: {work_id}")
        
        accountable_agent = self.raci.get_accountable_agent_for_plan_approval(work_id)
        if rejected_by != accountable_agent:
            raise ValueError(f"Agent {rejected_by} is not the ACCOUNTABLE agent for this work")
        
        if work.plan is None:
            raise ValueError("No plan has been submitted for this work")
        
        success = work.reject_plan(rejected_by, reason)
        
        if success:
            return {
                "work_id": work_id,
                "plan_id": work.plan.plan_id,
                "status": work.plan.status.value,
                "rejected_at": work.plan.approved_at.isoformat() if work.plan.approved_at else None,
                "rejection_reason": reason,
                "message": "Plan rejected. RESPONSIBLE agent should resubmit."
            }
        else:
            return {
                "work_id": work_id,
                "status": "error",
                "message": "Failed to reject plan"
            }

    def set_work_plan_approval_required(self, work_id: str, required: bool):
        work = self._works.get(work_id)
        if work:
            work.require_plan_approval = required

    def get_work_plan_status(self, work_id: str) -> Dict[str, Any]:
        work = self._works.get(work_id)
        if not work:
            raise ValueError(f"Work not found: {work_id}")
        
        result = {
            "work_id": work_id,
            "require_plan_approval": work.require_plan_approval,
            "plan": None
        }
        
        if work.plan:
            result["plan"] = {
                "plan_id": work.plan.plan_id,
                "proposed_by": work.plan.proposed_by,
                "content": work.plan.content,
                "submitted_at": work.plan.submitted_at.isoformat() if work.plan.submitted_at else None,
                "approved_by": work.plan.approved_by,
                "approved_at": work.plan.approved_at.isoformat() if work.plan.approved_at else None,
                "rejection_reason": work.plan.rejection_reason,
                "status": work.plan.status.value
            }
        
        responsible = self.raci.get_responsible_agents_for_plan_submission(work_id)
        accountable = self.raci.get_accountable_agent_for_plan_approval(work_id)
        
        result["responsible_agents"] = responsible
        result["accountable_agent"] = accountable
        
        return result
