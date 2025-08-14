# ERP Compliance Framework for RBAC-RAG Systems

## Overview

This document provides a comprehensive compliance framework for implementing RBAC-RAG systems in ERP environments. It covers major regulatory requirements including SOX, GDPR, HIPAA, CCPA, and industry-specific compliance standards while ensuring data governance and regulatory reporting capabilities.

## Regulatory Compliance Matrix

### 1. Sarbanes-Oxley Act (SOX) Compliance

#### SOX Section 404 - Internal Controls

**Requirements:**
- Management assessment of internal control effectiveness
- Documentation of financial reporting controls
- Testing and monitoring of control effectiveness
- External auditor attestation

**Implementation:**

```python
# sox_compliance_service.py
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime

class ControlEffectiveness(Enum):
    EFFECTIVE = "effective"
    INEFFECTIVE = "ineffective"
    NOT_TESTED = "not_tested"

class DeficiencyLevel(Enum):
    DEFICIENCY = "deficiency"
    SIGNIFICANT_DEFICIENCY = "significant_deficiency"
    MATERIAL_WEAKNESS = "material_weakness"

@dataclass
class SOXControl:
    control_id: str
    control_name: str
    control_objective: str
    control_owner: str
    frequency: str  # daily, weekly, monthly, quarterly
    last_test_date: Optional[datetime]
    effectiveness: ControlEffectiveness
    deficiency_level: Optional[DeficiencyLevel]
    remediation_plan: Optional[str]

class SOXComplianceService:
    
    def __init__(self, cerbos_client, audit_logger):
        self.cerbos_client = cerbos_client
        self.audit_logger = audit_logger
        self.sox_controls = self._initialize_sox_controls()
    
    def _initialize_sox_controls(self) -> Dict[str, SOXControl]:
        """Initialize SOX-required controls for financial reporting"""
        return {
            "SOX-001": SOXControl(
                control_id="SOX-001",
                control_name="Financial Close Process Controls",
                control_objective="Ensure accurate and complete financial statement preparation",
                control_owner="CFO",
                frequency="monthly",
                effectiveness=ControlEffectiveness.EFFECTIVE
            ),
            "SOX-002": SOXControl(
                control_id="SOX-002",
                control_name="Revenue Recognition Controls", 
                control_objective="Ensure revenue is recognized in accordance with GAAP",
                control_owner="Controller",
                frequency="daily",
                effectiveness=ControlEffectiveness.EFFECTIVE
            ),
            "SOX-003": SOXControl(
                control_id="SOX-003",
                control_name="Access Controls for Financial Systems",
                control_objective="Ensure appropriate access to financial reporting systems",
                control_owner="IT Security",
                frequency="quarterly",
                effectiveness=ControlEffectiveness.EFFECTIVE
            ),
            "SOX-004": SOXControl(
                control_id="SOX-004",
                control_name="Management Review Controls",
                control_objective="Ensure management oversight of financial reporting process",
                control_owner="CFO",
                frequency="monthly",
                effectiveness=ControlEffectiveness.EFFECTIVE
            )
        }
    
    async def validate_sox_access(self, user_context: dict, resource_context: dict) -> dict:
        """Validate SOX compliance for financial data access"""
        
        # Check if resource is SOX-controlled
        if not resource_context.get('sox_controlled'):
            return {"sox_compliant": True, "restrictions": []}
        
        # Validate user authorization for SOX data
        authorization_result = await self.cerbos_client.check_resource(
            principal=user_context,
            resource={
                "kind": "erp:financial_report",
                "id": resource_context.get('resource_id'),
                "attr": {
                    "sox_controlled": True,
                    "classification_level": resource_context.get('classification'),
                    "fiscal_year": resource_context.get('fiscal_year')
                }
            },
            action="read"
        )
        
        if authorization_result.allowed:
            # Log SOX access for audit trail
            await self.audit_logger.log_sox_access({
                "user_id": user_context.get('user_id'),
                "resource_id": resource_context.get('resource_id'),
                "access_time": datetime.now(),
                "sox_control_tested": True,
                "compliance_notes": "Access granted under SOX controls"
            })
            
            return {
                "sox_compliant": True,
                "audit_trail_recorded": True,
                "restrictions": ["read_only", "no_export_without_approval"]
            }
        
        return {
            "sox_compliant": False,
            "access_denied_reason": "Insufficient privileges for SOX-controlled data"
        }
    
    async def generate_sox_compliance_report(self, period: str) -> dict:
        """Generate SOX compliance report for specified period"""
        
        tested_controls = []
        deficiencies = []
        
        for control in self.sox_controls.values():
            if control.effectiveness == ControlEffectiveness.INEFFECTIVE:
                deficiencies.append({
                    "control_id": control.control_id,
                    "deficiency_level": control.deficiency_level.value,
                    "remediation_plan": control.remediation_plan
                })
            tested_controls.append(control)
        
        return {
            "reporting_period": period,
            "total_controls": len(self.sox_controls),
            "controls_tested": len([c for c in tested_controls if c.last_test_date]),
            "effective_controls": len([c for c in tested_controls if c.effectiveness == ControlEffectiveness.EFFECTIVE]),
            "deficiencies_identified": len(deficiencies),
            "deficiency_details": deficiencies,
            "management_certification_required": len(deficiencies) == 0,
            "external_auditor_notification": len([d for d in deficiencies if d["deficiency_level"] in ["significant_deficiency", "material_weakness"]]) > 0
        }
```

### 2. GDPR Compliance (EU General Data Protection Regulation)

#### GDPR Requirements for HR Data

**Implementation:**

```python
# gdpr_compliance_service.py
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class ProcessingBasis(Enum):
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"

class DataCategory(Enum):
    PERSONAL_DATA = "personal_data"
    SENSITIVE_DATA = "sensitive_data"
    CRIMINAL_DATA = "criminal_data"

@dataclass
class GDPRDataProcessing:
    processing_id: str
    data_subject_id: str
    data_categories: List[DataCategory]
    processing_purposes: List[str]
    legal_basis: ProcessingBasis
    retention_period: timedelta
    processing_start: datetime
    consent_obtained: bool = False
    consent_date: Optional[datetime] = None

class GDPRComplianceService:
    
    def __init__(self, cerbos_client, data_retention_service):
        self.cerbos_client = cerbos_client
        self.data_retention_service = data_retention_service
        self.processing_records = {}
    
    async def validate_gdpr_processing(self, user_context: dict, hr_record_context: dict) -> dict:
        """Validate GDPR compliance for HR data processing"""
        
        if not hr_record_context.get('gdpr_applicable'):
            return {"gdpr_compliant": True}
        
        # Check processing basis
        processing_basis = self._determine_processing_basis(user_context, hr_record_context)
        
        if processing_basis == ProcessingBasis.CONSENT:
            consent_valid = await self._validate_consent(hr_record_context['employee_id'])
            if not consent_valid:
                return {
                    "gdpr_compliant": False,
                    "violation_reason": "No valid consent for data processing"
                }
        
        # Check data minimization principle
        requested_data_types = hr_record_context.get('requested_data_types', [])
        necessary_data = self._determine_necessary_data(user_context['role'], user_context['purpose'])
        
        if not set(requested_data_types).issubset(set(necessary_data)):
            return {
                "gdpr_compliant": False,
                "violation_reason": "Data minimization principle violated",
                "excessive_data": list(set(requested_data_types) - set(necessary_data))
            }
        
        # Record processing activity
        processing_record = GDPRDataProcessing(
            processing_id=f"PROC_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            data_subject_id=hr_record_context['employee_id'],
            data_categories=[DataCategory.PERSONAL_DATA],
            processing_purposes=[user_context.get('purpose', 'hr_administration')],
            legal_basis=processing_basis,
            retention_period=self._get_retention_period(user_context['role']),
            processing_start=datetime.now()
        )
        
        self.processing_records[processing_record.processing_id] = processing_record
        
        return {
            "gdpr_compliant": True,
            "processing_basis": processing_basis.value,
            "retention_period_days": processing_record.retention_period.days,
            "data_subject_rights_available": [
                "right_of_access", 
                "right_to_rectification",
                "right_to_erasure",
                "right_to_portability"
            ]
        }
    
    def _determine_processing_basis(self, user_context: dict, hr_context: dict) -> ProcessingBasis:
        """Determine legal basis for processing under GDPR"""
        
        user_role = user_context.get('role')
        purpose = user_context.get('purpose')
        
        if purpose == "employment_contract":
            return ProcessingBasis.CONTRACT
        elif purpose == "legal_compliance":
            return ProcessingBasis.LEGAL_OBLIGATION
        elif user_role in ["hr_manager", "payroll_admin"]:
            return ProcessingBasis.LEGITIMATE_INTERESTS
        else:
            return ProcessingBasis.CONSENT
    
    async def handle_subject_access_request(self, employee_id: str) -> dict:
        """Handle GDPR Article 15 - Right of Access request"""
        
        # Collect all personal data for the employee
        personal_data = await self._collect_employee_data(employee_id)
        
        # Get processing records
        employee_processing = [
            record for record in self.processing_records.values()
            if record.data_subject_id == employee_id
        ]
        
        return {
            "data_subject_id": employee_id,
            "request_processed_date": datetime.now(),
            "personal_data_categories": personal_data.keys(),
            "processing_purposes": list(set([
                purpose for record in employee_processing
                for purpose in record.processing_purposes
            ])),
            "data_recipients": ["internal_hr", "payroll_provider", "benefit_administrators"],
            "retention_periods": {
                category: self._get_retention_period_for_category(category)
                for category in personal_data.keys()
            },
            "data_sources": ["erp_system", "hris", "applicant_tracking_system"],
            "automated_decision_making": False,
            "data_transfer_outside_eu": False
        }
    
    async def handle_erasure_request(self, employee_id: str, reason: str = "withdrawal_of_consent") -> dict:
        """Handle GDPR Article 17 - Right to Erasure request"""
        
        # Check if erasure is legally required
        can_erase = await self._can_process_erasure(employee_id, reason)
        
        if not can_erase:
            return {
                "erasure_processed": False,
                "reason": "Legal obligation to retain data overrides right to erasure"
            }
        
        # Process erasure
        erased_data_categories = await self._process_data_erasure(employee_id)
        
        return {
            "erasure_processed": True,
            "employee_id": employee_id,
            "erasure_date": datetime.now(),
            "erased_data_categories": erased_data_categories,
            "retained_data_categories": ["legal_employment_records"],
            "retention_justification": "Legal obligation under employment law"
        }
```

### 3. HIPAA Compliance (Healthcare Data)

#### HIPAA Requirements for Employee Health Data

```python
# hipaa_compliance_service.py
from enum import Enum
from typing import Dict, List, Optional

class HIPAAEntityType(Enum):
    COVERED_ENTITY = "covered_entity"
    BUSINESS_ASSOCIATE = "business_associate"
    
class PHIAccessType(Enum):
    MINIMUM_NECESSARY = "minimum_necessary"
    FULL_ACCESS = "full_access"
    EMERGENCY_ACCESS = "emergency_access"

class HIPAAComplianceService:
    
    def __init__(self, cerbos_client, encryption_service):
        self.cerbos_client = cerbos_client
        self.encryption_service = encryption_service
        self.authorized_personnel = self._load_authorized_personnel()
    
    async def validate_phi_access(self, user_context: dict, health_record_context: dict) -> dict:
        """Validate HIPAA compliance for PHI access"""
        
        if not health_record_context.get('contains_phi'):
            return {"hipaa_compliant": True}
        
        # Check if user is authorized to access PHI
        if not self._is_authorized_for_phi(user_context):
            return {
                "hipaa_compliant": False,
                "violation_reason": "User not authorized to access PHI"
            }
        
        # Apply minimum necessary standard
        necessary_data = self._determine_minimum_necessary(
            user_context['role'], 
            user_context.get('purpose', 'treatment')
        )
        
        requested_data = health_record_context.get('requested_fields', [])
        
        if not set(requested_data).issubset(set(necessary_data)):
            return {
                "hipaa_compliant": False,
                "violation_reason": "Minimum necessary standard violated",
                "excessive_fields": list(set(requested_data) - set(necessary_data))
            }
        
        # Log PHI access
        await self._log_phi_access({
            "user_id": user_context['user_id'],
            "employee_id": health_record_context['employee_id'],
            "access_time": datetime.now(),
            "purpose": user_context.get('purpose'),
            "data_accessed": necessary_data
        })
        
        return {
            "hipaa_compliant": True,
            "access_type": PHIAccessType.MINIMUM_NECESSARY.value,
            "permitted_fields": necessary_data,
            "audit_log_created": True
        }
    
    def _is_authorized_for_phi(self, user_context: dict) -> bool:
        """Check if user is authorized to access PHI"""
        
        authorized_roles = [
            "occupational_health_nurse",
            "company_doctor", 
            "hr_benefits_admin",
            "workers_comp_admin"
        ]
        
        user_roles = user_context.get('roles', [])
        return any(role in authorized_roles for role in user_roles) and \
               user_context.get('hipaa_training_completed', False)
    
    def _determine_minimum_necessary(self, user_role: str, purpose: str) -> List[str]:
        """Determine minimum necessary PHI based on role and purpose"""
        
        minimum_necessary_map = {
            ("occupational_health_nurse", "treatment"): [
                "medical_conditions", "medications", "treatment_history", 
                "work_restrictions", "accommodation_needs"
            ],
            ("hr_benefits_admin", "benefits_administration"): [
                "insurance_eligibility", "coverage_elections", "dependent_info"
            ],
            ("workers_comp_admin", "workers_compensation"): [
                "injury_details", "treatment_providers", "work_status", "restrictions"
            ]
        }
        
        return minimum_necessary_map.get((user_role, purpose), [])
```

### 4. CCPA Compliance (California Consumer Privacy Act)

```python
# ccpa_compliance_service.py
from enum import Enum
from typing import Dict, List, Optional

class CCPAConsumerRight(Enum):
    RIGHT_TO_KNOW = "right_to_know"
    RIGHT_TO_DELETE = "right_to_delete"
    RIGHT_TO_OPT_OUT = "right_to_opt_out"
    RIGHT_TO_NON_DISCRIMINATION = "right_to_non_discrimination"

class PersonalInformationCategory(Enum):
    IDENTIFIERS = "identifiers"
    FINANCIAL_INFO = "financial_info"
    EMPLOYMENT_INFO = "employment_info"
    BIOMETRIC_INFO = "biometric_info"

class CCPAComplianceService:
    
    def __init__(self, cerbos_client, privacy_service):
        self.cerbos_client = cerbos_client
        self.privacy_service = privacy_service
    
    async def handle_consumer_request(self, employee_id: str, request_type: CCPAConsumerRight) -> dict:
        """Handle CCPA consumer rights requests"""
        
        if request_type == CCPAConsumerRight.RIGHT_TO_KNOW:
            return await self._handle_right_to_know(employee_id)
        elif request_type == CCPAConsumerRight.RIGHT_TO_DELETE:
            return await self._handle_right_to_delete(employee_id)
        elif request_type == CCPAConsumerRight.RIGHT_TO_OPT_OUT:
            return await self._handle_opt_out(employee_id)
        
        return {"error": "Unsupported request type"}
    
    async def _handle_right_to_know(self, employee_id: str) -> dict:
        """Handle CCPA Right to Know request"""
        
        # Collect personal information categories
        pi_categories = await self._collect_pi_categories(employee_id)
        
        # Get business purposes for collection
        business_purposes = [
            "human_resources_management",
            "payroll_processing", 
            "benefits_administration",
            "compliance_with_employment_laws"
        ]
        
        # Get categories of third parties we share with
        third_party_categories = [
            "payroll_service_providers",
            "benefits_administrators", 
            "background_check_companies",
            "government_agencies"
        ]
        
        return {
            "consumer_id": employee_id,
            "personal_info_categories": [cat.value for cat in pi_categories],
            "business_purposes": business_purposes,
            "third_party_categories": third_party_categories,
            "sources_of_pi": ["employment_application", "hr_systems", "timekeeping_systems"],
            "sale_of_pi": False,  # Most employers don't sell employee PI
            "retention_periods": {
                "employment_records": "7_years_post_termination",
                "payroll_records": "4_years",
                "benefits_records": "duration_of_employment_plus_7_years"
            }
        }
```

### 5. Industry-Specific Compliance

#### Financial Services (SOX + FFIEC)

```python
# financial_services_compliance.py
class FinancialServicesCompliance:
    
    def __init__(self, cerbos_client):
        self.cerbos_client = cerbos_client
        self.ffiec_requirements = self._load_ffiec_requirements()
    
    async def validate_financial_services_access(self, user_context: dict, resource_context: dict) -> dict:
        """Validate access according to financial services regulations"""
        
        # FFIEC IT Examination Handbook requirements
        if resource_context.get('contains_cii'):  # Customer Identifiable Information
            return await self._validate_cii_access(user_context, resource_context)
        
        # Bank Secrecy Act requirements
        if resource_context.get('bsa_sensitive'):
            return await self._validate_bsa_access(user_context, resource_context)
        
        return {"compliant": True}
```

#### Healthcare Industry (HIPAA + HITECH)

```python
# healthcare_compliance.py
class HealthcareCompliance:
    
    def __init__(self, cerbos_client, breach_notification_service):
        self.cerbos_client = cerbos_client
        self.breach_service = breach_notification_service
    
    async def validate_healthcare_access(self, user_context: dict, resource_context: dict) -> dict:
        """Validate access according to healthcare regulations"""
        
        # HITECH Act breach notification requirements
        if resource_context.get('unsecured_phi_breach_risk'):
            await self.breach_service.assess_breach_risk(resource_context)
        
        return await self.validate_phi_access(user_context, resource_context)
```

## Compliance Monitoring and Reporting

### 1. Real-time Compliance Monitoring

```python
# compliance_monitor.py
import asyncio
from typing import Dict, List
from datetime import datetime, timedelta

class ComplianceMonitor:
    
    def __init__(self, compliance_services: Dict[str, object]):
        self.compliance_services = compliance_services
        self.violation_queue = asyncio.Queue()
        self.monitoring_active = False
    
    async def start_monitoring(self):
        """Start real-time compliance monitoring"""
        self.monitoring_active = True
        
        # Start violation processor
        asyncio.create_task(self._process_violations())
        
        # Start periodic compliance checks
        asyncio.create_task(self._periodic_compliance_check())
    
    async def check_access_compliance(self, access_request: dict) -> dict:
        """Check compliance for access requests"""
        
        compliance_results = {}
        
        # Check SOX compliance
        if access_request.get('sox_applicable'):
            sox_result = await self.compliance_services['sox'].validate_sox_access(
                access_request['user_context'],
                access_request['resource_context']
            )
            compliance_results['sox'] = sox_result
        
        # Check GDPR compliance
        if access_request.get('gdpr_applicable'):
            gdpr_result = await self.compliance_services['gdpr'].validate_gdpr_processing(
                access_request['user_context'],
                access_request['resource_context']
            )
            compliance_results['gdpr'] = gdpr_result
        
        # Check HIPAA compliance
        if access_request.get('phi_data'):
            hipaa_result = await self.compliance_services['hipaa'].validate_phi_access(
                access_request['user_context'],
                access_request['resource_context']
            )
            compliance_results['hipaa'] = hipaa_result
        
        # Aggregate compliance status
        overall_compliant = all(
            result.get('compliant', True) or result.get('gdpr_compliant', True) or result.get('sox_compliant', True) or result.get('hipaa_compliant', True)
            for result in compliance_results.values()
        )
        
        if not overall_compliant:
            await self._report_violation({
                "timestamp": datetime.now(),
                "user_id": access_request['user_context']['user_id'],
                "resource_id": access_request['resource_context']['resource_id'],
                "compliance_results": compliance_results,
                "violation_severity": "high" if any(not result.get('compliant', True) for result in compliance_results.values()) else "medium"
            })
        
        return {
            "overall_compliant": overall_compliant,
            "compliance_details": compliance_results,
            "access_permitted": overall_compliant
        }
```

### 2. Compliance Dashboard

```python
# compliance_dashboard.py
from fastapi import FastAPI, Depends
from typing import Dict, List

app = FastAPI()

class ComplianceDashboard:
    
    def __init__(self, compliance_monitor, reporting_service):
        self.monitor = compliance_monitor
        self.reporting = reporting_service
    
    async def get_compliance_summary(self, time_range: str = "30d") -> dict:
        """Get compliance summary for specified time range"""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=int(time_range.rstrip('d')))
        
        # Get violation counts by regulation
        violations = await self.reporting.get_violations(start_date, end_date)
        
        violation_counts = {
            "sox_violations": len([v for v in violations if 'sox' in v['regulations']]),
            "gdpr_violations": len([v for v in violations if 'gdpr' in v['regulations']]),
            "hipaa_violations": len([v for v in violations if 'hipaa' in v['regulations']]),
            "ccpa_violations": len([v for v in violations if 'ccpa' in v['regulations']])
        }
        
        # Get compliance score
        total_access_requests = await self.reporting.get_total_access_requests(start_date, end_date)
        total_violations = len(violations)
        compliance_score = ((total_access_requests - total_violations) / total_access_requests) * 100 if total_access_requests > 0 else 100
        
        return {
            "time_range": time_range,
            "compliance_score": compliance_score,
            "total_access_requests": total_access_requests,
            "violation_counts": violation_counts,
            "trending": await self._calculate_compliance_trend(start_date, end_date),
            "top_violation_types": await self._get_top_violation_types(violations),
            "remediation_status": await self._get_remediation_status(violations)
        }
    
    async def get_regulatory_report(self, regulation: str, period: str) -> dict:
        """Generate regulatory-specific compliance report"""
        
        if regulation == "sox":
            return await self.compliance_services['sox'].generate_sox_compliance_report(period)
        elif regulation == "gdpr":
            return await self._generate_gdpr_compliance_report(period)
        elif regulation == "hipaa":
            return await self._generate_hipaa_compliance_report(period)
        
        return {"error": f"Unknown regulation: {regulation}"}

# FastAPI endpoints
@app.get("/compliance/dashboard")
async def get_compliance_dashboard(
    time_range: str = "30d",
    dashboard: ComplianceDashboard = Depends()
):
    return await dashboard.get_compliance_summary(time_range)

@app.get("/compliance/report/{regulation}")
async def get_regulatory_report(
    regulation: str,
    period: str = "quarterly",
    dashboard: ComplianceDashboard = Depends()
):
    return await dashboard.get_regulatory_report(regulation, period)
```

### 3. Compliance Training and Certification

```python
# compliance_training.py
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta

class TrainingStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    EXPIRED = "expired"

@dataclass
class ComplianceTraining:
    training_id: str
    regulation: str
    employee_id: str
    completion_date: Optional[datetime]
    expiration_date: Optional[datetime]
    status: TrainingStatus
    score: Optional[int]
    certification_number: Optional[str]

class ComplianceTrainingService:
    
    def __init__(self, learning_management_system):
        self.lms = learning_management_system
        self.training_records = {}
    
    async def check_training_compliance(self, user_id: str, required_trainings: List[str]) -> dict:
        """Check if user has completed required compliance training"""
        
        user_trainings = await self._get_user_trainings(user_id)
        
        compliance_status = {}
        for training in required_trainings:
            training_record = user_trainings.get(training)
            
            if not training_record:
                compliance_status[training] = {
                    "status": "not_completed",
                    "required_by": datetime.now() + timedelta(days=30)
                }
            elif training_record.status == TrainingStatus.EXPIRED:
                compliance_status[training] = {
                    "status": "expired",
                    "expired_on": training_record.expiration_date,
                    "renewal_required": True
                }
            else:
                compliance_status[training] = {
                    "status": "current",
                    "completed_on": training_record.completion_date,
                    "expires_on": training_record.expiration_date
                }
        
        overall_compliant = all(
            status["status"] == "current" 
            for status in compliance_status.values()
        )
        
        return {
            "user_id": user_id,
            "overall_compliant": overall_compliant,
            "training_status": compliance_status,
            "required_actions": [
                f"Complete {training} training"
                for training, status in compliance_status.items()
                if status["status"] in ["not_completed", "expired"]
            ]
        }
```

## Data Retention and Disposition

### 1. Regulatory Retention Schedule

```python
# data_retention.py
from enum import Enum
from datetime import datetime, timedelta
from typing import Dict, List

class RetentionTrigger(Enum):
    CREATION_DATE = "creation_date"
    TERMINATION_DATE = "termination_date"
    LAST_ACCESS_DATE = "last_access_date"
    LEGAL_HOLD = "legal_hold"

class DispositionMethod(Enum):
    SECURE_DELETE = "secure_delete"
    ARCHIVE = "archive"
    TRANSFER_TO_RECORDS_MANAGEMENT = "transfer_to_records"

@dataclass
class RetentionRule:
    rule_id: str
    data_category: str
    retention_period: timedelta
    trigger: RetentionTrigger
    disposition_method: DispositionMethod
    legal_basis: str
    applicable_regulations: List[str]

class DataRetentionService:
    
    def __init__(self):
        self.retention_rules = self._initialize_retention_rules()
    
    def _initialize_retention_rules(self) -> Dict[str, RetentionRule]:
        """Initialize regulatory data retention rules"""
        return {
            "personnel_files": RetentionRule(
                rule_id="RET-001",
                data_category="personnel_files",
                retention_period=timedelta(days=7*365),  # 7 years
                trigger=RetentionTrigger.TERMINATION_DATE,
                disposition_method=DispositionMethod.SECURE_DELETE,
                legal_basis="Employment law requirements",
                applicable_regulations=["SOX", "EEOC", "State Employment Laws"]
            ),
            "payroll_records": RetentionRule(
                rule_id="RET-002", 
                data_category="payroll_records",
                retention_period=timedelta(days=4*365),  # 4 years
                trigger=RetentionTrigger.CREATION_DATE,
                disposition_method=DispositionMethod.ARCHIVE,
                legal_basis="IRS requirements",
                applicable_regulations=["IRS", "Department of Labor"]
            ),
            "medical_records": RetentionRule(
                rule_id="RET-003",
                data_category="medical_records", 
                retention_period=timedelta(days=30*365),  # 30 years
                trigger=RetentionTrigger.TERMINATION_DATE,
                disposition_method=DispositionMethod.TRANSFER_TO_RECORDS_MANAGEMENT,
                legal_basis="OSHA requirements",
                applicable_regulations=["OSHA", "HIPAA"]
            ),
            "financial_records": RetentionRule(
                rule_id="RET-004",
                data_category="financial_records",
                retention_period=timedelta(days=7*365),  # 7 years
                trigger=RetentionTrigger.CREATION_DATE,
                disposition_method=DispositionMethod.ARCHIVE,
                legal_basis="SOX requirements",
                applicable_regulations=["SOX", "SEC"]
            )
        }
    
    async def check_retention_compliance(self, data_record: dict) -> dict:
        """Check if data record complies with retention requirements"""
        
        data_category = data_record.get('category')
        retention_rule = self.retention_rules.get(data_category)
        
        if not retention_rule:
            return {"retention_compliant": True, "reason": "No specific retention rule"}
        
        # Calculate retention expiration date
        trigger_date = self._get_trigger_date(data_record, retention_rule.trigger)
        expiration_date = trigger_date + retention_rule.retention_period
        
        current_date = datetime.now()
        
        if current_date > expiration_date:
            return {
                "retention_compliant": False,
                "expired": True,
                "expiration_date": expiration_date,
                "disposition_required": True,
                "disposition_method": retention_rule.disposition_method.value,
                "applicable_regulations": retention_rule.applicable_regulations
            }
        
        return {
            "retention_compliant": True,
            "expires_on": expiration_date,
            "days_until_expiration": (expiration_date - current_date).days,
            "applicable_regulations": retention_rule.applicable_regulations
        }
```

This comprehensive compliance framework ensures that ERP RBAC-RAG systems meet all major regulatory requirements while maintaining operational efficiency and data governance standards. The framework provides automated compliance checking, violation monitoring, and reporting capabilities essential for enterprise deployments.
