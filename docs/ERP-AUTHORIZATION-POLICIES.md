# ERP Authorization Policies for Cerbos

## Overview

This document provides comprehensive Cerbos policies specifically designed for ERP systems. These policies implement fine-grained access control for financial, HR, operational, and compliance data while ensuring regulatory compliance and business security requirements.

## Policy Structure

### 1. Resource Policies
- Financial Report Policies
- HR Record Policies  
- Operational Data Policies
- Compliance Document Policies
- Procurement Data Policies
- Inventory Management Policies

### 2. Principal Policies
- Role-based access patterns
- Department-specific permissions
- Executive-level overrides
- External user policies

### 3. Derived Roles
- Dynamic role assignments
- Context-aware permissions
- Hierarchical role inheritance

## Resource Policies

### 1. Financial Report Policy

```yaml
# policies/resource_policies/erp_financial_report.yaml
apiVersion: "api.cerbos.dev/v1"
description: "Financial Report Access Control for ERP Systems"
resourcePolicy:
  resource: "erp:financial_report"
  version: "default"
  
  importDerivedRoles:
    - "financial_analyst"
    - "department_budget_manager"
    - "sox_auditor"
  
  variables:
    import:
      - aaa
    
    local:
      is_executive:
        expr: >
          "ceo" in request.principal.roles || 
          "cfo" in request.principal.roles ||
          "board_member" in request.principal.roles
      
      is_finance_team:
        expr: >
          request.principal.attr.department == "finance" ||
          request.principal.attr.department == "accounting" ||
          "finance_manager" in request.principal.roles
      
      report_fiscal_year:
        expr: request.resource.attr.fiscal_year
      
      current_fiscal_year:
        expr: request.principal.attr.current_fiscal_year
      
      is_current_or_recent:
        expr: >
          int(variables.report_fiscal_year) >= (int(variables.current_fiscal_year) - 2)
  
  rules:
    # Executive Level Access - Full Financial Data
    - actions: ["read", "analyze", "export"]
      effect: EFFECT_ALLOW
      condition:
        match:
          expr: variables.is_executive
      output:
        expr: >
          {
            "access_level": "executive",
            "restrictions": [],
            "audit_required": request.resource.attr.sox_controlled
          }
    
    # CFO Special Permissions - All Financial Data + Modification Rights
    - actions: ["read", "write", "approve", "analyze", "export"]
      effect: EFFECT_ALLOW
      roles: ["cfo"]
      output:
        expr: >
          {
            "access_level": "full_financial",
            "restrictions": [],
            "approval_rights": true,
            "sox_override": true
          }
    
    # Finance Managers - Department Financial Data
    - actions: ["read", "write", "analyze"]
      effect: EFFECT_ALLOW
      roles: ["finance_manager"]
      condition:
        match:
          expr: >
            variables.is_finance_team &&
            (request.resource.attr.classification_level == "internal" ||
             request.resource.attr.classification_level == "confidential") &&
            variables.is_current_or_recent
      output:
        expr: >
          {
            "access_level": "finance_management",
            "restrictions": ["no_historical_data_beyond_2_years"],
            "modification_rights": request.resource.attr.report_type != "audit_report"
          }
    
    # External Auditors - SOX Controlled Reports Only
    - actions: ["read", "analyze"]
      effect: EFFECT_ALLOW
      roles: ["external_auditor"]
      condition:
        match:
          expr: >
            request.resource.attr.sox_controlled == true &&
            request.resource.attr.external_auditor_accessible == true &&
            request.principal.attr.audit_engagement_active == true
      output:
        expr: >
          {
            "access_level": "audit_only",
            "restrictions": ["read_only", "audit_trail_required"],
            "engagement_id": request.principal.attr.current_engagement_id
          }
    
    # Financial Analysts - Analysis and Reporting
    - actions: ["read", "analyze"]
      effect: EFFECT_ALLOW
      derivedRoles: ["financial_analyst"]
      condition:
        match:
          expr: >
            request.resource.attr.classification_level != "restricted" &&
            request.principal.attr.clearance_level >= 2 &&
            variables.is_current_or_recent
    
    # Department Budget Managers - Budget Data for Their Department
    - actions: ["read", "write"]
      effect: EFFECT_ALLOW
      derivedRoles: ["department_budget_manager"]
      condition:
        match:
          expr: >
            request.resource.attr.report_type == "budget" &&
            request.resource.attr.department in request.principal.attr.managed_departments
    
    # SOX Compliance - Restrict Audit Report Modifications
    - actions: ["write", "delete", "modify"]
      effect: EFFECT_DENY
      condition:
        match:
          expr: >
            request.resource.attr.sox_controlled == true &&
            request.resource.attr.report_type == "audit_report" &&
            !variables.is_executive
    
    # Time-based Access Control - Historical Data Restrictions
    - actions: ["read"]
      effect: EFFECT_DENY
      roles: ["accountant", "junior_analyst"]
      condition:
        match:
          expr: >
            int(variables.report_fiscal_year) < (int(variables.current_fiscal_year) - 5) &&
            request.principal.attr.historical_data_access != true

schemas:
  principalSchema:
    ref: "cerbos://schemas/principal.json"
  resourceSchema:
    ref: "cerbos://schemas/financial_report.json"
```

### 2. HR Record Policy

```yaml
# policies/resource_policies/erp_hr_record.yaml
apiVersion: "api.cerbos.dev/v1"
description: "HR Record Access Control with GDPR Compliance"
resourcePolicy:
  resource: "erp:hr_record"
  version: "default"
  
  importDerivedRoles:
    - "people_manager"
    - "hr_specialist" 
    - "payroll_administrator"
  
  variables:
    local:
      is_self_access:
        expr: >
          request.resource.attr.employee_id == request.principal.attr.employee_id
      
      is_direct_report:
        expr: >
          request.resource.attr.manager_id == request.principal.attr.employee_id
      
      gdpr_applies:
        expr: >
          request.resource.attr.gdpr_applicable == true
      
      sensitive_hr_data:
        expr: >
          request.resource.attr.data_type in ["payroll", "medical", "disciplinary", "background_check"]
      
      manager_accessible_data:
        expr: >
          request.resource.attr.data_type in ["performance", "training", "basic_info", "job_details"]
  
  rules:
    # HR Leadership - Full HR Access
    - actions: ["*"]
      effect: EFFECT_ALLOW
      roles: ["chief_hr_officer", "hr_director"]
      condition:
        match:
          expr: >
            request.principal.attr.hr_clearance_level >= 4
      output:
        expr: >
          {
            "access_level": "full_hr_admin",
            "gdpr_processing_basis": "legitimate_interest_hr_administration",
            "data_minimization_required": false
          }
    
    # HR Managers - Department HR Data
    - actions: ["read", "write", "update"]
      effect: EFFECT_ALLOW
      roles: ["hr_manager"]
      condition:
        match:
          expr: >
            request.resource.attr.employee_department in request.principal.attr.managed_departments ||
            request.principal.attr.hr_scope == "global"
    
    # HR Specialists - Specific HR Functions
    - actions: ["read", "write"]
      effect: EFFECT_ALLOW
      derivedRoles: ["hr_specialist"]
      condition:
        match:
          expr: >
            request.resource.attr.data_type in request.principal.attr.hr_specializations &&
            !variables.sensitive_hr_data
    
    # Payroll Administration - Payroll Data Only
    - actions: ["read", "write", "process"]
      effect: EFFECT_ALLOW
      derivedRoles: ["payroll_administrator"]
      condition:
        match:
          expr: >
            request.resource.attr.data_type == "payroll" &&
            request.principal.attr.payroll_certification == true
      output:
        expr: >
          {
            "access_level": "payroll_processing",
            "encryption_required": true,
            "audit_trail_required": true
          }
    
    # People Managers - Direct Reports Data
    - actions: ["read", "review"]
      effect: EFFECT_ALLOW
      derivedRoles: ["people_manager"]
      condition:
        match:
          expr: >
            variables.is_direct_report &&
            variables.manager_accessible_data &&
            request.principal.attr.management_training_completed == true
    
    # Employee Self-Access - Own Records
    - actions: ["read"]
      effect: EFFECT_ALLOW
      roles: ["employee"]
      condition:
        match:
          expr: >
            variables.is_self_access &&
            request.resource.attr.employee_viewable == true &&
            request.resource.attr.data_type != "background_check"
      output:
        expr: >
          {
            "access_level": "self_service",
            "gdpr_processing_basis": "contract",
            "data_portability_available": true
          }
    
    # GDPR Right to Access - Enhanced Self Access
    - actions: ["read", "export"]
      effect: EFFECT_ALLOW
      roles: ["employee"]
      condition:
        match:
          expr: >
            variables.is_self_access &&
            variables.gdpr_applies &&
            request.action_reason == "gdpr_subject_access_request"
    
    # Medical Data - Healthcare Professionals Only
    - actions: ["read", "write"]
      effect: EFFECT_ALLOW
      roles: ["occupational_health_nurse", "company_doctor"]
      condition:
        match:
          expr: >
            request.resource.attr.data_type == "medical" &&
            request.principal.attr.medical_license_verified == true
    
    # Deny Sensitive Data to Managers
    - actions: ["read"]
      effect: EFFECT_DENY
      derivedRoles: ["people_manager"]
      condition:
        match:
          expr: >
            variables.sensitive_hr_data &&
            !request.principal.attr.hr_admin_rights
    
    # GDPR Data Minimization
    - actions: ["bulk_export", "analytics"]
      effect: EFFECT_DENY
      condition:
        match:
          expr: >
            variables.gdpr_applies &&
            request.principal.attr.gdpr_training_completed != true

schemas:
  principalSchema:
    ref: "cerbos://schemas/principal.json"
  resourceSchema:
    ref: "cerbos://schemas/hr_record.json"
```

### 3. Operational Data Policy

```yaml
# policies/resource_policies/erp_operational_data.yaml
apiVersion: "api.cerbos.dev/v1"
description: "Operational Data Access Control for ERP Systems"
resourcePolicy:
  resource: "erp:operational_data"
  version: "default"
  
  importDerivedRoles:
    - "operations_manager"
    - "supply_chain_analyst"
    - "warehouse_supervisor"
  
  variables:
    local:
      is_operations_team:
        expr: >
          request.principal.attr.department in ["operations", "manufacturing", "supply_chain", "warehouse"]
      
      location_access:
        expr: >
          request.resource.attr.location in request.principal.attr.accessible_locations ||
          request.principal.attr.global_operations_access == true
      
      vendor_restricted:
        expr: >
          request.resource.attr.data_type == "vendor_pricing" ||
          request.resource.attr.data_type == "contract_terms"
      
      real_time_data:
        expr: >
          request.resource.attr.data_freshness == "real_time" ||
          request.resource.attr.data_freshness == "hourly"
  
  rules:
    # COO - Full Operational Oversight
    - actions: ["*"]
      effect: EFFECT_ALLOW
      roles: ["coo", "vp_operations"]
      output:
        expr: >
          {
            "access_level": "executive_operations",
            "global_access": true,
            "real_time_access": true
          }
    
    # Operations Managers - Location-based Access
    - actions: ["read", "write", "analyze", "optimize"]
      effect: EFFECT_ALLOW
      derivedRoles: ["operations_manager"]
      condition:
        match:
          expr: >
            variables.location_access &&
            variables.is_operations_team
    
    # Supply Chain Analysts - Supply Chain Data
    - actions: ["read", "analyze", "forecast"]
      effect: EFFECT_ALLOW
      derivedRoles: ["supply_chain_analyst"]
      condition:
        match:
          expr: >
            request.resource.attr.data_type in ["inventory", "demand_planning", "supplier_performance"] &&
            !variables.vendor_restricted
    
    # Warehouse Supervisors - Warehouse Operations
    - actions: ["read", "write", "update_status"]
      effect: EFFECT_ALLOW
      derivedRoles: ["warehouse_supervisor"]
      condition:
        match:
          expr: >
            request.resource.attr.data_type in ["inventory", "shipping", "receiving"] &&
            variables.location_access
    
    # Procurement Team - Vendor and Purchase Data
    - actions: ["read", "write", "negotiate"]
      effect: EFFECT_ALLOW
      roles: ["procurement_manager", "buyer"]
      condition:
        match:
          expr: >
            request.resource.attr.data_type in ["vendor_information", "purchase_orders", "rfq"] &&
            request.principal.attr.procurement_authority_limit >= request.resource.attr.transaction_value
    
    # Quality Team - Quality Data Access
    - actions: ["read", "write", "approve", "reject"]
      effect: EFFECT_ALLOW
      roles: ["quality_manager", "quality_inspector"]
      condition:
        match:
          expr: >
            request.resource.attr.data_type in ["quality_metrics", "inspection_results", "nonconformance"]
    
    # Production Team - Manufacturing Data
    - actions: ["read", "write", "schedule"]
      effect: EFFECT_ALLOW
      roles: ["production_manager", "production_scheduler"]
      condition:
        match:
          expr: >
            request.resource.attr.data_type in ["production_schedule", "work_orders", "machine_data"] &&
            variables.location_access
    
    # Real-time Data Access Control
    - actions: ["read"]
      effect: EFFECT_ALLOW
      condition:
        match:
          expr: >
            variables.real_time_data &&
            request.principal.attr.real_time_access == true &&
            variables.is_operations_team
    
    # Vendor Sensitive Data Protection
    - actions: ["read"]
      effect: EFFECT_DENY
      roles: ["warehouse_worker", "production_worker"]
      condition:
        match:
          expr: variables.vendor_restricted
    
    # Location-based Data Segregation
    - actions: ["read", "write"]
      effect: EFFECT_DENY
      condition:
        match:
          expr: >
            !variables.location_access &&
            request.resource.attr.location_sensitive == true

schemas:
  principalSchema:
    ref: "cerbos://schemas/principal.json"
  resourceSchema:
    ref: "cerbos://schemas/operational_data.json"
```

### 4. Compliance Document Policy

```yaml
# policies/resource_policies/erp_compliance_document.yaml
apiVersion: "api.cerbos.dev/v1"
description: "Compliance Document Access Control"
resourcePolicy:
  resource: "erp:compliance_document"
  version: "default"
  
  variables:
    local:
      is_compliance_team:
        expr: >
          request.principal.attr.department == "compliance" ||
          request.principal.attr.department == "legal" ||
          "compliance_officer" in request.principal.roles
      
      is_audit_document:
        expr: >
          request.resource.attr.document_type in ["audit_report", "sox_documentation", "internal_audit"]
      
      regulatory_requirement:
        expr: request.resource.attr.regulatory_requirement
      
      document_classification:
        expr: request.resource.attr.classification_level
  
  rules:
    # Chief Compliance Officer - Full Access
    - actions: ["*"]
      effect: EFFECT_ALLOW
      roles: ["chief_compliance_officer"]
      output:
        expr: >
          {
            "access_level": "full_compliance_admin",
            "regulatory_authority": true,
            "modification_rights": true
          }
    
    # Compliance Officers - Compliance Document Access
    - actions: ["read", "write", "review", "approve"]
      effect: EFFECT_ALLOW
      roles: ["compliance_officer"]
      condition:
        match:
          expr: >
            variables.is_compliance_team &&
            request.principal.attr.compliance_certifications != null
    
    # Legal Team - Legal and Regulatory Documents
    - actions: ["read", "review", "legal_advice"]
      effect: EFFECT_ALLOW
      roles: ["general_counsel", "legal_counsel"]
      condition:
        match:
          expr: >
            request.resource.attr.legal_review_required == true ||
            variables.regulatory_requirement in ["SOX", "GDPR", "HIPAA"]
    
    # External Auditors - Audit Documents
    - actions: ["read", "review"]
      effect: EFFECT_ALLOW
      roles: ["external_auditor"]
      condition:
        match:
          expr: >
            variables.is_audit_document &&
            request.resource.attr.external_auditor_accessible == true &&
            request.principal.attr.audit_firm == request.resource.attr.authorized_audit_firm
    
    # Internal Auditors - Internal Audit Access
    - actions: ["read", "write", "audit"]
      effect: EFFECT_ALLOW
      roles: ["internal_auditor", "audit_manager"]
      condition:
        match:
          expr: >
            request.resource.attr.document_type == "internal_audit" ||
            (variables.is_audit_document && request.principal.attr.internal_audit_certified == true)
    
    # Risk Management - Risk-related Compliance
    - actions: ["read", "assess"]
      effect: EFFECT_ALLOW
      roles: ["risk_manager", "chief_risk_officer"]
      condition:
        match:
          expr: >
            request.resource.attr.risk_related == true &&
            variables.document_classification != "restricted"
    
    # Department Heads - Department-specific Compliance
    - actions: ["read"]
      effect: EFFECT_ALLOW
      roles: ["department_head"]
      condition:
        match:
          expr: >
            request.resource.attr.applicable_departments != null &&
            request.principal.attr.department in request.resource.attr.applicable_departments
    
    # SOX Documentation Protection
    - actions: ["write", "delete", "modify"]
      effect: EFFECT_DENY
      condition:
        match:
          expr: >
            variables.regulatory_requirement == "SOX" &&
            request.resource.attr.sox_immutable == true &&
            !"compliance_officer" in request.principal.roles
    
    # Restricted Document Access
    - actions: ["read"]
      effect: EFFECT_DENY
      condition:
        match:
          expr: >
            variables.document_classification == "restricted" &&
            request.principal.attr.clearance_level < 4 &&
            !variables.is_compliance_team

schemas:
  principalSchema:
    ref: "cerbos://schemas/principal.json"
  resourceSchema:
    ref: "cerbos://schemas/compliance_document.json"
```

## Derived Roles

### 1. Management Derived Roles

```yaml
# policies/derived_roles/management_roles.yaml
apiVersion: "api.cerbos.dev/v1"
description: "Management Derived Roles for ERP Systems"
derivedRoles:
  name: "management_roles"
  definitions:
    - name: "financial_analyst"
      parentRoles: ["employee"]
      condition:
        match:
          expr: >
            request.principal.attr.department == "finance" &&
            "financial_analysis" in request.principal.attr.certifications &&
            request.principal.attr.clearance_level >= 2
    
    - name: "department_budget_manager"
      parentRoles: ["manager"]
      condition:
        match:
          expr: >
            size(request.principal.attr.managed_departments) > 0 &&
            request.principal.attr.budget_authority > 0 &&
            request.principal.attr.management_level >= 2
    
    - name: "sox_auditor"
      parentRoles: ["auditor"]
      condition:
        match:
          expr: >
            "sox_certification" in request.principal.attr.certifications &&
            request.principal.attr.audit_firm_authorized == true
    
    - name: "people_manager"
      parentRoles: ["manager"]
      condition:
        match:
          expr: >
            request.principal.attr.direct_reports_count > 0 &&
            request.principal.attr.management_training_completed == true
    
    - name: "hr_specialist"
      parentRoles: ["employee"]
      condition:
        match:
          expr: >
            request.principal.attr.department == "human_resources" &&
            size(request.principal.attr.hr_specializations) > 0 &&
            request.principal.attr.hr_clearance_level >= 2
    
    - name: "payroll_administrator"
      parentRoles: ["hr_specialist"]
      condition:
        match:
          expr: >
            "payroll" in request.principal.attr.hr_specializations &&
            request.principal.attr.payroll_certification == true &&
            request.principal.attr.background_check_cleared == true
    
    - name: "operations_manager"
      parentRoles: ["manager"]
      condition:
        match:
          expr: >
            request.principal.attr.department in ["operations", "manufacturing", "supply_chain"] &&
            size(request.principal.attr.accessible_locations) > 0 &&
            request.principal.attr.operations_experience_years >= 3
    
    - name: "supply_chain_analyst"
      parentRoles: ["employee"]
      condition:
        match:
          expr: >
            request.principal.attr.department == "supply_chain" &&
            "supply_chain_analysis" in request.principal.attr.skills &&
            request.principal.attr.analytics_access_certified == true
    
    - name: "warehouse_supervisor"
      parentRoles: ["supervisor"]
      condition:
        match:
          expr: >
            request.principal.attr.department == "warehouse" &&
            size(request.principal.attr.accessible_locations) > 0 &&
            request.principal.attr.warehouse_management_certified == true
```

### 2. Cross-Functional Derived Roles

```yaml
# policies/derived_roles/cross_functional_roles.yaml
apiVersion: "api.cerbos.dev/v1"
description: "Cross-Functional Derived Roles"
derivedRoles:
  name: "cross_functional_roles"
  definitions:
    - name: "business_analyst"
      parentRoles: ["employee"]
      condition:
        match:
          expr: >
            "business_analysis" in request.principal.attr.skills &&
            request.principal.attr.cross_functional_access == true &&
            request.principal.attr.clearance_level >= 2
    
    - name: "project_manager"
      parentRoles: ["manager"]
      condition:
        match:
          expr: >
            "project_management" in request.principal.attr.certifications &&
            size(request.principal.attr.active_projects) > 0 &&
            request.principal.attr.pmp_certified == true
    
    - name: "data_steward"
      parentRoles: ["employee"]
      condition:
        match:
          expr: >
            request.principal.attr.data_governance_role == true &&
            "data_stewardship" in request.principal.attr.training_completed &&
            request.principal.attr.department in ["it", "finance", "hr", "operations"]
    
    - name: "security_officer"
      parentRoles: ["officer"]
      condition:
        match:
          expr: >
            request.principal.attr.department in ["security", "it_security", "compliance"] &&
            "security_clearance" in request.principal.attr.certifications &&
            request.principal.attr.security_clearance_level >= 3
```

## Principal Policies

### 1. Executive Principal Policy

```yaml
# policies/principal_policies/executive_principals.yaml
apiVersion: "api.cerbos.dev/v1"
description: "Executive Principal Policies"
principalPolicy:
  principal: "executive"
  version: "default"
  
  rules:
    # CEO - Ultimate Authority
    - resource: "*"
      actions:
        read: EFFECT_ALLOW
        analyze: EFFECT_ALLOW
        strategic_decision: EFFECT_ALLOW
      condition:
        match:
          expr: >
            "ceo" in request.principal.roles &&
            request.principal.attr.executive_override_authorized == true
      output:
        expr: >
          {
            "access_level": "unrestricted",
            "override_available": true,
            "audit_required": true
          }
    
    # C-Suite Officers - Department Oversight
    - resource: "erp:*"
      actions:
        read: EFFECT_ALLOW
        oversight: EFFECT_ALLOW
      condition:
        match:
          expr: >
            request.principal.roles intersect ["cfo", "coo", "cto", "chro"] != [] &&
            request.resource.attr.executive_visibility == true
    
    # Board Members - Governance Access
    - resource: "erp:compliance_document"
      actions:
        read: EFFECT_ALLOW
        governance_review: EFFECT_ALLOW
      condition:
        match:
          expr: >
            "board_member" in request.principal.roles &&
            request.resource.attr.board_visibility == true
```

### 2. Department Principal Policy

```yaml
# policies/principal_policies/department_principals.yaml
apiVersion: "api.cerbos.dev/v1"
description: "Department-based Principal Policies"
principalPolicy:
  principal: "department_member"
  version: "default"
  
  rules:
    # Finance Department
    - resource: "erp:financial_report"
      actions:
        read: EFFECT_ALLOW
        analyze: EFFECT_ALLOW
      condition:
        match:
          expr: >
            request.principal.attr.department == "finance" &&
            request.resource.attr.department in ["finance", "general"] &&
            request.principal.attr.clearance_level >= 2
    
    # HR Department
    - resource: "erp:hr_record"
      actions:
        read: EFFECT_ALLOW
        process: EFFECT_ALLOW
      condition:
        match:
          expr: >
            request.principal.attr.department == "human_resources" &&
            request.principal.attr.hr_clearance_level >= 1
    
    # Operations Department
    - resource: "erp:operational_data"
      actions:
        read: EFFECT_ALLOW
        optimize: EFFECT_ALLOW
      condition:
        match:
          expr: >
            request.principal.attr.department in ["operations", "manufacturing", "supply_chain"] &&
            request.resource.attr.operational_scope in request.principal.attr.operational_access_scope
```

## Schema Definitions

### 1. Principal Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "cerbos://schemas/principal.json",
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "description": "Unique principal identifier"
    },
    "attr": {
      "type": "object",
      "properties": {
        "department": {
          "type": "string",
          "enum": ["finance", "human_resources", "operations", "manufacturing", "supply_chain", "it", "legal", "compliance", "sales", "marketing"]
        },
        "clearance_level": {
          "type": "integer",
          "minimum": 1,
          "maximum": 5,
          "description": "Security clearance level (1=basic, 5=top_secret)"
        },
        "employee_id": {
          "type": "string"
        },
        "manager_id": {
          "type": "string"
        },
        "accessible_departments": {
          "type": "array",
          "items": {"type": "string"}
        },
        "managed_departments": {
          "type": "array", 
          "items": {"type": "string"}
        },
        "accessible_locations": {
          "type": "array",
          "items": {"type": "string"}
        },
        "certifications": {
          "type": "array",
          "items": {"type": "string"}
        },
        "hr_specializations": {
          "type": "array",
          "items": {"type": "string"}
        },
        "management_level": {
          "type": "integer",
          "minimum": 1,
          "maximum": 5
        },
        "budget_authority": {
          "type": "number",
          "minimum": 0
        },
        "sox_certified": {
          "type": "boolean"
        },
        "gdpr_training_completed": {
          "type": "boolean"
        },
        "audit_engagement_active": {
          "type": "boolean"
        },
        "current_engagement_id": {
          "type": "string"
        }
      },
      "required": ["department", "clearance_level", "employee_id"]
    }
  },
  "required": ["id", "attr"]
}
```

### 2. Financial Report Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "cerbos://schemas/financial_report.json",
  "type": "object",
  "properties": {
    "id": {
      "type": "string"
    },
    "attr": {
      "type": "object",
      "properties": {
        "classification_level": {
          "type": "string",
          "enum": ["public", "internal", "confidential", "restricted"]
        },
        "department": {
          "type": "string"
        },
        "report_type": {
          "type": "string",
          "enum": ["budget", "actual", "forecast", "audit_report", "management_report"]
        },
        "fiscal_year": {
          "type": "string",
          "pattern": "^[0-9]{4}$"
        },
        "quarter": {
          "type": "string",
          "enum": ["Q1", "Q2", "Q3", "Q4"]
        },
        "sox_controlled": {
          "type": "boolean"
        },
        "external_auditor_accessible": {
          "type": "boolean"
        },
        "board_visibility": {
          "type": "boolean"
        }
      },
      "required": ["classification_level", "department", "report_type", "fiscal_year"]
    }
  },
  "required": ["id", "attr"]
}
```

### 3. HR Record Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "cerbos://schemas/hr_record.json", 
  "type": "object",
  "properties": {
    "id": {
      "type": "string"
    },
    "attr": {
      "type": "object",
      "properties": {
        "employee_id": {
          "type": "string"
        },
        "manager_id": {
          "type": "string"
        },
        "employee_department": {
          "type": "string"
        },
        "data_type": {
          "type": "string",
          "enum": ["basic_info", "job_details", "performance", "training", "payroll", "medical", "disciplinary", "background_check"]
        },
        "classification_level": {
          "type": "string",
          "enum": ["internal", "confidential", "restricted"]
        },
        "gdpr_applicable": {
          "type": "boolean"
        },
        "employee_viewable": {
          "type": "boolean"
        },
        "manager_accessible": {
          "type": "boolean"
        }
      },
      "required": ["employee_id", "data_type", "classification_level"]
    }
  },
  "required": ["id", "attr"]
}
```

## Policy Testing Framework

### 1. Test Suite Configuration

```yaml
# tests/policy_test_suite.yaml
name: "ERP Authorization Policy Tests"
description: "Comprehensive test suite for ERP Cerbos policies"

tests:
  - name: "Financial Report Access Tests"
    principals:
      - cfo:
          id: "cfo_001"
          roles: ["cfo"]
          attr:
            department: "finance"
            clearance_level: 5
            employee_id: "E001"
    
    resources:
      - quarterly_financials:
          kind: "erp:financial_report"
          id: "Q3_2024_financials"
          attr:
            classification_level: "confidential"
            department: "finance"
            report_type: "quarterly"
            fiscal_year: "2024"
            sox_controlled: true
    
    actions: ["read", "analyze", "export"]
    expected: EFFECT_ALLOW

  - name: "HR Self-Access Tests"
    principals:
      - employee:
          id: "emp_12345"
          roles: ["employee"]
          attr:
            department: "engineering"
            clearance_level: 2
            employee_id: "12345"
    
    resources:
      - own_hr_record:
          kind: "erp:hr_record"
          id: "hr_record_12345"
          attr:
            employee_id: "12345"
            data_type: "basic_info"
            classification_level: "internal"
            employee_viewable: true
    
    actions: ["read"]
    expected: EFFECT_ALLOW

  - name: "Unauthorized Financial Access Tests"
    principals:
      - regular_employee:
          id: "emp_67890"
          roles: ["employee"]
          attr:
            department: "engineering"
            clearance_level: 1
            employee_id: "67890"
    
    resources:
      - audit_report:
          kind: "erp:financial_report"
          id: "audit_2024"
          attr:
            classification_level: "restricted"
            report_type: "audit_report"
            sox_controlled: true
    
    actions: ["read"]
    expected: EFFECT_DENY
```

### 2. Automated Policy Validation

```python
# tests/test_erp_policies.py
import pytest
from cerbos.sdk.grpc.client import CerbosClient
from cerbos.sdk.model import CheckResourcesRequest, Principal, Resource

class TestERPPolicies:
    
    @pytest.fixture
    async def cerbos_client(self):
        client = CerbosClient("localhost:3593")
        yield client
        await client.close()
    
    async def test_cfo_financial_access(self, cerbos_client):
        """Test CFO access to financial reports"""
        
        principal = Principal(
            id="cfo_001",
            roles=["cfo"],
            attr={
                "department": "finance",
                "clearance_level": 5,
                "employee_id": "E001"
            }
        )
        
        resource = Resource(
            kind="erp:financial_report", 
            id="Q3_2024_financials",
            attr={
                "classification_level": "confidential",
                "department": "finance",
                "report_type": "quarterly",
                "fiscal_year": "2024",
                "sox_controlled": True
            }
        )
        
        request = CheckResourcesRequest(
            principal=principal,
            resources=[resource],
            actions=["read", "analyze", "export"]
        )
        
        response = await cerbos_client.check_resources(request)
        
        assert response.results[0].actions["read"].effect == "ALLOW"
        assert response.results[0].actions["analyze"].effect == "ALLOW"
        assert response.results[0].actions["export"].effect == "ALLOW"
    
    async def test_hr_gdpr_compliance(self, cerbos_client):
        """Test GDPR compliance for HR data access"""
        
        principal = Principal(
            id="hr_manager_001",
            roles=["hr_manager"],
            attr={
                "department": "human_resources",
                "hr_clearance_level": 4,
                "gdpr_training_completed": True
            }
        )
        
        resource = Resource(
            kind="erp:hr_record",
            id="employee_data_eu",
            attr={
                "employee_id": "E12345",
                "data_type": "personal_info", 
                "classification_level": "confidential",
                "gdpr_applicable": True
            }
        )
        
        request = CheckResourcesRequest(
            principal=principal,
            resources=[resource],
            actions=["read", "process"]
        )
        
        response = await cerbos_client.check_resources(request)
        
        assert response.results[0].actions["read"].effect == "ALLOW"
        assert response.results[0].actions["process"].effect == "ALLOW"
        
        # Check output contains GDPR compliance information
        output = response.results[0].outputs[0]
        assert "gdpr_processing_basis" in output
```

This comprehensive policy framework provides robust, compliant, and granular access control for ERP systems using Cerbos. The policies are designed to meet regulatory requirements while maintaining operational efficiency.