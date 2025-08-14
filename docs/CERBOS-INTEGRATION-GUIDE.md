# Cerbos Integration Guide for ERP RBAC-RAG System

## Overview

This guide provides comprehensive instructions for integrating Cerbos as the primary authorization engine in your ERP RBAC-RAG system. Cerbos will handle all authorization decisions for ERP data access, document retrieval, and RAG query processing.

## Table of Contents

1. [Cerbos Setup and Configuration](#cerbos-setup-and-configuration)
2. [FastAPI Integration](#fastapi-integration)
3. [Policy Development](#policy-development)
4. [ERP-Specific Implementation](#erp-specific-implementation)
5. [Testing and Validation](#testing-and-validation)
6. [Performance Optimization](#performance-optimization)
7. [Monitoring and Debugging](#monitoring-and-debugging)

## Cerbos Setup and Configuration

### 1. Installation and Deployment

#### Docker Deployment (Recommended for Development):
```yaml
# docker-compose.cerbos.yml
version: '3.8'
services:
  cerbos:
    image: ghcr.io/cerbos/cerbos:0.33.0
    container_name: cerbos
    ports:
      - "3592:3592"  # HTTP port
      - "3593:3593"  # gRPC port
    volumes:
      - ./cerbos/policies:/policies:ro
      - ./cerbos/config:/config:ro
    command: ["server", "--config=/config/config.yaml"]
    environment:
      - CERBOS_LOG_LEVEL=INFO
    networks:
      - erp-rag-network

networks:
  erp-rag-network:
    driver: bridge
```

#### Cerbos Configuration:
```yaml
# cerbos/config/config.yaml
server:
  httpListenAddr: ":3592"
  grpcListenAddr: ":3593"
  requestLimits:
    maxRequestSizeBytes: 4194304

storage:
  driver: "disk"
  disk:
    directory: "/policies"
    watchForChanges: true

audit:
  enabled: true
  backend: local
  local:
    storagePath: /tmp/audit.log

telemetry:
  disabled: false

compile:
  cacheSize: 1024
```

### 2. Directory Structure

```
cerbos/
├── config/
│   └── config.yaml
├── policies/
│   ├── resource_policies/
│   │   ├── erp_financial_report.yaml
│   │   ├── erp_hr_record.yaml
│   │   ├── erp_operational_data.yaml
│   │   └── erp_compliance_doc.yaml
│   ├── principal_policies/
│   │   ├── erp_roles.yaml
│   │   └── erp_departments.yaml
│   └── derived_roles/
│       ├── department_manager.yaml
│       └── cross_functional_roles.yaml
└── schemas/
    ├── principal.json
    └── resource.json
```

## FastAPI Integration

### 1. Cerbos Client Setup

```python
# app/auth/cerbos_client.py
from cerbos.sdk.grpc.client import CerbosClient
from cerbos.sdk.model import CheckResourcesRequest, Principal, Resource
from typing import Dict, List, Any, Optional
import asyncio
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class ERPCerbosClient:
    def __init__(self, host: str = "localhost", port: int = 3593):
        self.host = host
        self.port = port
        self.client: Optional[CerbosClient] = None
    
    async def connect(self):
        """Establish connection to Cerbos server"""
        try:
            self.client = CerbosClient(f"{self.host}:{self.port}")
            logger.info(f"Connected to Cerbos server at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Cerbos: {e}")
            raise
    
    async def disconnect(self):
        """Close connection to Cerbos server"""
        if self.client:
            await self.client.close()
            self.client = None
    
    @asynccontextmanager
    async def get_client(self):
        """Context manager for Cerbos client"""
        if not self.client:
            await self.connect()
        
        try:
            yield self.client
        finally:
            # Keep connection open for reuse
            pass
    
    async def check_resource_access(
        self,
        user_id: str,
        user_roles: List[str],
        user_attributes: Dict[str, Any],
        resource_kind: str,
        resource_id: str,
        resource_attributes: Dict[str, Any],
        action: str
    ) -> bool:
        """Check if user has access to specific resource"""
        
        try:
            async with self.get_client() as client:
                # Create principal (user)
                principal = Principal(
                    id=user_id,
                    roles=user_roles,
                    attr=user_attributes
                )
                
                # Create resource
                resource = Resource(
                    kind=resource_kind,
                    id=resource_id,
                    attr=resource_attributes
                )
                
                # Check access
                request = CheckResourcesRequest(
                    principal=principal,
                    resources=[resource],
                    actions=[action]
                )
                
                response = await client.check_resources(request)
                
                # Get result
                if response.results:
                    result = response.results[0]
                    is_allowed = result.actions[action].effect == "ALLOW"
                    
                    # Log authorization decision
                    logger.info(
                        f"Authorization check: user={user_id}, "
                        f"resource={resource_kind}:{resource_id}, "
                        f"action={action}, allowed={is_allowed}"
                    )
                    
                    return is_allowed
                
                return False
                
        except Exception as e:
            logger.error(f"Cerbos authorization check failed: {e}")
            # Fail secure - deny access on error
            return False
    
    async def check_multiple_resources(
        self,
        user_id: str,
        user_roles: List[str],
        user_attributes: Dict[str, Any],
        resource_checks: List[Dict[str, Any]]
    ) -> Dict[str, bool]:
        """Check access to multiple resources in single request"""
        
        try:
            async with self.get_client() as client:
                principal = Principal(
                    id=user_id,
                    roles=user_roles,
                    attr=user_attributes
                )
                
                resources = []
                actions = []
                
                for check in resource_checks:
                    resource = Resource(
                        kind=check['resource_kind'],
                        id=check['resource_id'],
                        attr=check.get('resource_attributes', {})
                    )
                    resources.append(resource)
                    actions.append(check['action'])
                
                request = CheckResourcesRequest(
                    principal=principal,
                    resources=resources,
                    actions=actions
                )
                
                response = await client.check_resources(request)
                
                # Process results
                results = {}
                for i, result in enumerate(response.results):
                    resource_key = f"{resource_checks[i]['resource_kind']}:{resource_checks[i]['resource_id']}"
                    action = resource_checks[i]['action']
                    results[resource_key] = result.actions[action].effect == "ALLOW"
                
                return results
                
        except Exception as e:
            logger.error(f"Cerbos bulk authorization check failed: {e}")
            # Fail secure - deny all access on error
            return {f"{check['resource_kind']}:{check['resource_id']}": False 
                    for check in resource_checks}

# Global Cerbos client instance
cerbos_client = ERPCerbosClient()
```

### 2. FastAPI Dependencies and Middleware

```python
# app/auth/dependencies.py
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, List
import jwt
from .cerbos_client import cerbos_client

security = HTTPBearer()

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Extract user information from JWT token"""
    
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token, 
            request.app.state.secret_key, 
            algorithms=["HS256"]
        )
        
        # Validate token
        if payload.get("type") == "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "username": payload.get("username"),
            "roles": payload.get("roles", []),
            "department": payload.get("department"),
            "clearance_level": payload.get("clearance_level", "internal"),
            "accessible_departments": payload.get("accessible_departments", []),
            "company_code": payload.get("company_code"),
            "employee_id": payload.get("employee_id")
        }
        
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_resource_access(resource_kind: str, action: str = "read"):
    """Decorator factory for resource-level authorization"""
    
    def decorator(resource_id_param: str = "resource_id"):
        async def dependency(
            request: Request,
            current_user: Dict[str, Any] = Depends(get_current_user)
        ):
            # Get resource ID from path parameters
            resource_id = request.path_params.get(resource_id_param)
            
            if not resource_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing {resource_id_param} parameter"
                )
            
            # Get resource attributes from request or database
            resource_attributes = await _get_resource_attributes(resource_kind, resource_id)
            
            # Check authorization with Cerbos
            is_allowed = await cerbos_client.check_resource_access(
                user_id=current_user["user_id"],
                user_roles=current_user["roles"],
                user_attributes={
                    "department": current_user["department"],
                    "clearance_level": current_user["clearance_level"],
                    "accessible_departments": current_user["accessible_departments"],
                    "company_code": current_user["company_code"],
                    "employee_id": current_user["employee_id"]
                },
                resource_kind=resource_kind,
                resource_id=resource_id,
                resource_attributes=resource_attributes,
                action=action
            )
            
            if not is_allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied to {resource_kind}:{resource_id}"
                )
            
            return {
                "user": current_user,
                "resource_id": resource_id,
                "resource_attributes": resource_attributes
            }
        
        return dependency
    
    return decorator

async def _get_resource_attributes(resource_kind: str, resource_id: str) -> Dict[str, Any]:
    """Get resource attributes from database or cache"""
    
    # This would typically fetch from database
    # For now, return default attributes based on resource kind
    
    if resource_kind == "erp:financial_report":
        return {
            "classification_level": "confidential",
            "department": "finance",
            "report_type": "quarterly",
            "fiscal_year": "2024"
        }
    elif resource_kind == "erp:hr_record":
        return {
            "classification_level": "restricted",
            "department": "human_resources",
            "employee_department": "engineering",
            "data_type": "personal_info"
        }
    else:
        return {
            "classification_level": "internal",
            "department": "general"
        }
```

### 3. ERP-Specific Authorization Service

```python
# app/auth/erp_authorization.py
from typing import Dict, List, Any, Optional
from .cerbos_client import cerbos_client
import logging

logger = logging.getLogger(__name__)

class ERPAuthorizationService:
    def __init__(self):
        self.cerbos = cerbos_client
    
    async def authorize_financial_query(
        self, 
        user_context: Dict[str, Any], 
        query_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Authorize financial data query with detailed permissions"""
        
        financial_resources = [
            "profit_loss_statement",
            "balance_sheet", 
            "cash_flow_statement",
            "budget_data",
            "audit_reports"
        ]
        
        authorized_resources = []
        
        for resource in financial_resources:
            resource_attrs = await self._get_financial_resource_attributes(
                resource, query_context
            )
            
            is_allowed = await self.cerbos.check_resource_access(
                user_id=user_context["user_id"],
                user_roles=user_context["roles"],
                user_attributes=self._build_user_attributes(user_context),
                resource_kind="erp:financial_report",
                resource_id=resource,
                resource_attributes=resource_attrs,
                action="read"
            )
            
            if is_allowed:
                authorized_resources.append({
                    "resource": resource,
                    "attributes": resource_attrs
                })
        
        return {
            "authorized_resources": authorized_resources,
            "query_filters": self._build_financial_filters(authorized_resources),
            "compliance_requirements": self._get_compliance_requirements(user_context)
        }
    
    async def authorize_hr_query(
        self,
        user_context: Dict[str, Any],
        query_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Authorize HR data query with privacy controls"""
        
        hr_resources = [
            "employee_records",
            "payroll_data", 
            "performance_reviews",
            "training_records",
            "disciplinary_records"
        ]
        
        authorized_resources = []
        
        for resource in hr_resources:
            resource_attrs = await self._get_hr_resource_attributes(
                resource, query_context, user_context
            )
            
            is_allowed = await self.cerbos.check_resource_access(
                user_id=user_context["user_id"],
                user_roles=user_context["roles"], 
                user_attributes=self._build_user_attributes(user_context),
                resource_kind="erp:hr_record",
                resource_id=resource,
                resource_attributes=resource_attrs,
                action="read"
            )
            
            if is_allowed:
                # Apply GDPR data minimization
                minimized_attrs = await self._apply_gdpr_minimization(
                    resource_attrs, user_context, query_context
                )
                
                authorized_resources.append({
                    "resource": resource,
                    "attributes": minimized_attrs
                })
        
        return {
            "authorized_resources": authorized_resources,
            "privacy_controls": self._get_privacy_controls(user_context),
            "data_retention_policy": self._get_data_retention_policy()
        }
    
    async def authorize_operational_query(
        self,
        user_context: Dict[str, Any],
        query_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Authorize operational data query"""
        
        operational_resources = [
            "inventory_data",
            "procurement_records",
            "vendor_information",
            "production_metrics",
            "quality_reports"
        ]
        
        authorized_resources = []
        
        for resource in operational_resources:
            resource_attrs = await self._get_operational_resource_attributes(
                resource, query_context
            )
            
            is_allowed = await self.cerbos.check_resource_access(
                user_id=user_context["user_id"],
                user_roles=user_context["roles"],
                user_attributes=self._build_user_attributes(user_context),
                resource_kind="erp:operational_data",
                resource_id=resource,
                resource_attributes=resource_attrs,
                action="read"
            )
            
            if is_allowed:
                authorized_resources.append({
                    "resource": resource,
                    "attributes": resource_attrs
                })
        
        return {
            "authorized_resources": authorized_resources,
            "location_filters": self._build_location_filters(user_context),
            "time_range_limits": self._get_time_range_limits(user_context)
        }
    
    async def authorize_document_access(
        self,
        user_context: Dict[str, Any],
        document_ids: List[str]
    ) -> List[str]:
        """Bulk authorize document access"""
        
        # Prepare bulk authorization request
        resource_checks = []
        for doc_id in document_ids:
            doc_attrs = await self._get_document_attributes(doc_id)
            resource_checks.append({
                "resource_kind": self._get_document_resource_kind(doc_attrs),
                "resource_id": doc_id,
                "resource_attributes": doc_attrs,
                "action": "read"
            })
        
        # Bulk check with Cerbos
        results = await self.cerbos.check_multiple_resources(
            user_id=user_context["user_id"],
            user_roles=user_context["roles"],
            user_attributes=self._build_user_attributes(user_context),
            resource_checks=resource_checks
        )
        
        # Return list of authorized document IDs
        authorized_docs = []
        for doc_id in document_ids:
            resource_key = f"{self._get_document_resource_kind_by_id(doc_id)}:{doc_id}"
            if results.get(resource_key, False):
                authorized_docs.append(doc_id)
        
        return authorized_docs
    
    def _build_user_attributes(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Build user attributes for Cerbos principal"""
        return {
            "department": user_context.get("department"),
            "clearance_level": user_context.get("clearance_level", "internal"),
            "accessible_departments": user_context.get("accessible_departments", []),
            "company_code": user_context.get("company_code"),
            "employee_id": user_context.get("employee_id"),
            "location": user_context.get("location", "headquarters"),
            "cost_center": user_context.get("cost_center"),
            "manager_id": user_context.get("manager_id")
        }
    
    async def _get_financial_resource_attributes(
        self, 
        resource: str, 
        query_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get financial resource attributes"""
        
        base_attrs = {
            "classification_level": "confidential",
            "department": "finance",
            "data_sensitivity": "high",
            "sox_controlled": True
        }
        
        # Resource-specific attributes
        if resource == "audit_reports":
            base_attrs.update({
                "classification_level": "restricted",
                "sox_controlled": True,
                "external_auditor_accessible": True
            })
        elif resource == "budget_data":
            base_attrs.update({
                "classification_level": "internal",
                "planning_only": True
            })
        
        # Add query context
        if "fiscal_year" in query_context:
            base_attrs["fiscal_year"] = query_context["fiscal_year"]
        
        if "quarter" in query_context:
            base_attrs["quarter"] = query_context["quarter"]
        
        return base_attrs
    
    async def _get_hr_resource_attributes(
        self,
        resource: str,
        query_context: Dict[str, Any],
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get HR resource attributes with privacy considerations"""
        
        base_attrs = {
            "classification_level": "restricted",
            "department": "human_resources",
            "data_sensitivity": "personal",
            "gdpr_applicable": True
        }
        
        # Resource-specific attributes
        if resource == "payroll_data":
            base_attrs.update({
                "classification_level": "restricted",
                "financial_data": True,
                "encryption_required": True
            })
        elif resource == "performance_reviews":
            base_attrs.update({
                "classification_level": "confidential",
                "manager_accessible": True,
                "employee_self_access": True
            })
        
        # Add employee-specific context if querying specific employee
        if "employee_id" in query_context:
            base_attrs.update({
                "target_employee_id": query_context["employee_id"],
                "target_employee_department": query_context.get("employee_department")
            })
        
        return base_attrs

# Global authorization service instance
erp_auth_service = ERPAuthorizationService()
```

### 4. API Route Integration

```python
# app/api/erp_routes.py
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Dict, Any, List, Optional
from ..auth.dependencies import get_current_user, require_resource_access
from ..auth.erp_authorization import erp_auth_service
from ..services.rag_service import rag_service

router = APIRouter(prefix="/api/erp", tags=["ERP"])

@router.post("/query/financial")
async def query_financial_data(
    query: str,
    fiscal_year: Optional[str] = Query(None),
    quarter: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Query financial ERP data with authorization"""
    
    query_context = {
        "query": query,
        "fiscal_year": fiscal_year or "2024",
        "quarter": quarter,
        "query_type": "financial"
    }
    
    # Authorize financial query
    auth_result = await erp_auth_service.authorize_financial_query(
        current_user, query_context
    )
    
    if not auth_result["authorized_resources"]:
        raise HTTPException(
            status_code=403,
            detail="No access to requested financial data"
        )
    
    # Process RAG query with authorized resources
    rag_response = await rag_service.process_financial_query(
        query=query,
        user_context=current_user,
        authorized_resources=auth_result["authorized_resources"],
        query_filters=auth_result["query_filters"]
    )
    
    return {
        "response": rag_response["text"],
        "sources": rag_response["sources"],
        "authorized_resources": [r["resource"] for r in auth_result["authorized_resources"]],
        "compliance_notes": auth_result["compliance_requirements"]
    }

@router.post("/query/hr") 
async def query_hr_data(
    query: str,
    employee_id: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Query HR ERP data with privacy controls"""
    
    query_context = {
        "query": query,
        "employee_id": employee_id,
        "department": department,
        "query_type": "hr"
    }
    
    # Authorize HR query
    auth_result = await erp_auth_service.authorize_hr_query(
        current_user, query_context
    )
    
    if not auth_result["authorized_resources"]:
        raise HTTPException(
            status_code=403,
            detail="No access to requested HR data"
        )
    
    # Process RAG query with privacy controls
    rag_response = await rag_service.process_hr_query(
        query=query,
        user_context=current_user,
        authorized_resources=auth_result["authorized_resources"],
        privacy_controls=auth_result["privacy_controls"]
    )
    
    return {
        "response": rag_response["text"],
        "sources": rag_response["sources"],
        "privacy_applied": True,
        "data_retention_notice": auth_result["data_retention_policy"]
    }

@router.get("/documents/{document_id}")
async def get_document(
    document_access: Dict[str, Any] = Depends(
        require_resource_access("erp:document", "read")("document_id")
    )
):
    """Get specific ERP document with authorization"""
    
    # Document access already authorized by dependency
    document_id = document_access["resource_id"]
    user_context = document_access["user"]
    
    # Fetch document content
    document = await document_service.get_document(document_id)
    
    # Apply content filtering based on user clearance
    filtered_document = await apply_content_filtering(
        document, user_context["clearance_level"]
    )
    
    return {
        "document": filtered_document,
        "access_level": user_context["clearance_level"],
        "document_classification": document_access["resource_attributes"]["classification_level"]
    }

@router.post("/documents/bulk-authorize")
async def bulk_authorize_documents(
    document_ids: List[str],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Bulk authorize access to multiple documents"""
    
    authorized_docs = await erp_auth_service.authorize_document_access(
        current_user, document_ids
    )
    
    return {
        "requested_documents": len(document_ids),
        "authorized_documents": len(authorized_docs),
        "authorized_document_ids": authorized_docs,
        "denied_document_ids": list(set(document_ids) - set(authorized_docs))
    }
```

## Policy Development

### 1. Financial Report Policies

```yaml
# cerbos/policies/resource_policies/erp_financial_report.yaml
apiVersion: "api.cerbos.dev/v1"
description: "ERP Financial Report Access Policy"
resourcePolicy:
  resource: "erp:financial_report"
  version: "default"
  
  importDerivedRoles:
    - "department_manager"
    - "financial_analyst"
  
  rules:
    # CEO and CFO have unrestricted access
    - actions: ["*"]
      effect: EFFECT_ALLOW
      roles: ["ceo", "cfo"]
    
    # Finance managers can access department financial data
    - actions: ["read", "analyze"]
      effect: EFFECT_ALLOW
      roles: ["finance_manager"]
      condition:
        match:
          expr: >
            request.resource.attr.department == "finance" ||
            request.resource.attr.classification_level == "internal"
    
    # External auditors have read-only access to audit reports
    - actions: ["read"]
      effect: EFFECT_ALLOW
      roles: ["external_auditor"]
      condition:
        match:
          expr: >
            request.resource.attr.sox_controlled == true &&
            request.resource.attr.external_auditor_accessible == true
    
    # Department managers can access their department's budget data
    - actions: ["read"]
      effect: EFFECT_ALLOW
      derivedRoles: ["department_manager"]
      condition:
        match:
          expr: >
            request.resource.attr.report_type == "budget" &&
            request.resource.attr.department in request.principal.attr.accessible_departments
    
    # Financial analysts can read financial reports for analysis
    - actions: ["read", "analyze"]
      effect: EFFECT_ALLOW
      derivedRoles: ["financial_analyst"]
      condition:
        match:
          expr: >
            request.resource.attr.classification_level != "restricted" &&
            request.principal.attr.clearance_level >= request.resource.attr.min_clearance_level
    
    # Deny access to highly sensitive audit reports for non-executive roles
    - actions: ["*"]
      effect: EFFECT_DENY
      roles: ["accountant", "financial_analyst"]
      condition:
        match:
          expr: >
            request.resource.attr.report_type == "audit_report" &&
            request.resource.attr.classification_level == "restricted"

  variables:
    import:
      - aaa

    local:
      min_clearance_level:
        expr: >
          request.resource.attr.classification_level == "restricted" ? 4 :
          request.resource.attr.classification_level == "confidential" ? 3 :
          request.resource.attr.classification_level == "internal" ? 2 : 1
```

### 2. HR Record Policies

```yaml
# cerbos/policies/resource_policies/erp_hr_record.yaml
apiVersion: "api.cerbos.dev/v1"
description: "ERP HR Record Access Policy with GDPR Compliance"
resourcePolicy:
  resource: "erp:hr_record"
  version: "default"
  
  rules:
    # HR managers have full access to HR records
    - actions: ["read", "write", "delete"]
      effect: EFFECT_ALLOW
      roles: ["hr_manager"]
      condition:
        match:
          expr: >
            request.resource.attr.department == "human_resources" ||
            request.principal.attr.department == "human_resources"
    
    # Employees can access their own records
    - actions: ["read"]
      effect: EFFECT_ALLOW
      roles: ["employee"]
      condition:
        match:
          expr: >
            request.resource.attr.target_employee_id == request.principal.attr.employee_id &&
            request.resource.attr.data_type != "payroll"
    
    # Managers can access their direct reports' performance data
    - actions: ["read"]
      effect: EFFECT_ALLOW
      roles: ["manager"]
      condition:
        match:
          expr: >
            request.resource.attr.manager_accessible == true &&
            request.resource.attr.target_employee_department in request.principal.attr.accessible_departments
    
    # Payroll specialists can access payroll data
    - actions: ["read", "write"]
      effect: EFFECT_ALLOW
      roles: ["payroll_specialist"]
      condition:
        match:
          expr: >
            request.resource.attr.data_type == "payroll" &&
            request.principal.attr.clearance_level >= 3
    
    # CEO can access all HR records for executive decisions
    - actions: ["read"]
      effect: EFFECT_ALLOW
      roles: ["ceo"]
      condition:
        match:
          expr: >
            request.resource.attr.classification_level != "restricted" ||
            request.principal.attr.executive_override == true
    
    # Deny access to highly sensitive disciplinary records
    - actions: ["read"]
      effect: EFFECT_DENY
      roles: ["employee", "manager"]
      condition:
        match:
          expr: >
            request.resource.attr.data_type == "disciplinary" &&
            request.resource.attr.classification_level == "restricted" &&
            request.resource.attr.target_employee_id != request.principal.attr.employee_id

  variables:
    local:
      gdpr_compliant:
        expr: >
          request.resource.attr.gdpr_applicable == true &&
          request.principal.attr.gdpr_training_completed == true
```

### 3. Derived Roles

```yaml
# cerbos/policies/derived_roles/department_manager.yaml
apiVersion: "api.cerbos.dev/v1"
description: "Department Manager Derived Role"
derivedRoles:
  name: "department_manager"
  definitions:
    - name: "department_manager"
      parentRoles: ["manager"]
      condition:
        match:
          expr: >
            size(request.principal.attr.accessible_departments) > 0 &&
            request.principal.attr.management_level >= 2
    
    - name: "financial_analyst"
      parentRoles: ["employee"]
      condition:
        match:
          expr: >
            request.principal.attr.department == "finance" &&
            "financial_analysis" in request.principal.attr.specializations
```

## Testing and Validation

### 1. Unit Tests

```python
# tests/test_cerbos_integration.py
import pytest
from app.auth.cerbos_client import ERPCerbosClient
from app.auth.erp_authorization import ERPAuthorizationService

class TestCerbosIntegration:
    
    @pytest.fixture
    async def cerbos_client(self):
        client = ERPCerbosClient(host="localhost", port=3593)
        await client.connect()
        yield client
        await client.disconnect()
    
    @pytest.fixture
    def auth_service(self, cerbos_client):
        service = ERPAuthorizationService()
        service.cerbos = cerbos_client
        return service
    
    async def test_cfo_financial_access(self, cerbos_client):
        """Test CFO access to financial reports"""
        
        is_allowed = await cerbos_client.check_resource_access(
            user_id="cfo_001",
            user_roles=["cfo"],
            user_attributes={
                "department": "finance",
                "clearance_level": "executive",
                "accessible_departments": ["finance", "accounting"]
            },
            resource_kind="erp:financial_report",
            resource_id="quarterly_financials_q3_2024",
            resource_attributes={
                "classification_level": "confidential",
                "department": "finance",
                "report_type": "quarterly",
                "sox_controlled": True
            },
            action="read"
        )
        
        assert is_allowed == True
    
    async def test_employee_hr_self_access(self, cerbos_client):
        """Test employee access to their own HR records"""
        
        is_allowed = await cerbos_client.check_resource_access(
            user_id="emp_12345",
            user_roles=["employee"],
            user_attributes={
                "department": "engineering",
                "clearance_level": "internal",
                "employee_id": "12345"
            },
            resource_kind="erp:hr_record",
            resource_id="employee_record_12345",
            resource_attributes={
                "classification_level": "confidential",
                "department": "human_resources",
                "data_type": "personal_info",
                "target_employee_id": "12345"
            },
            action="read"
        )
        
        assert is_allowed == True
    
    async def test_unauthorized_financial_access(self, cerbos_client):
        """Test unauthorized access to financial reports"""
        
        is_allowed = await cerbos_client.check_resource_access(
            user_id="emp_67890",
            user_roles=["employee"],
            user_attributes={
                "department": "engineering",
                "clearance_level": "internal",
                "employee_id": "67890"
            },
            resource_kind="erp:financial_report",
            resource_id="audit_report_2024",
            resource_attributes={
                "classification_level": "restricted",
                "department": "finance",
                "report_type": "audit_report",
                "sox_controlled": True
            },
            action="read"
        )
        
        assert is_allowed == False
    
    async def test_bulk_authorization(self, auth_service):
        """Test bulk document authorization"""
        
        user_context = {
            "user_id": "manager_001",
            "roles": ["finance_manager"],
            "department": "finance",
            "clearance_level": "confidential",
            "accessible_departments": ["finance", "accounting"],
            "employee_id": "manager_001"
        }
        
        document_ids = [
            "financial_report_001",
            "hr_record_002",
            "operational_data_003"
        ]
        
        authorized_docs = await auth_service.authorize_document_access(
            user_context, document_ids
        )
        
        # Finance manager should have access to financial report
        assert "financial_report_001" in authorized_docs
        # But not to HR records
        assert "hr_record_002" not in authorized_docs
```

### 2. Integration Tests

```python
# tests/test_erp_authorization_integration.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestERPAuthorizationIntegration:
    
    def test_financial_query_authorized(self):
        """Test authorized financial query"""
        
        # Mock JWT token for CFO
        headers = {"Authorization": "Bearer <cfo_jwt_token>"}
        
        response = client.post(
            "/api/erp/query/financial",
            json={"query": "Show me Q3 2024 revenue by department"},
            headers=headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "response" in result
        assert "authorized_resources" in result
        assert len(result["authorized_resources"]) > 0
    
    def test_financial_query_unauthorized(self):
        """Test unauthorized financial query"""
        
        # Mock JWT token for regular employee
        headers = {"Authorization": "Bearer <employee_jwt_token>"}
        
        response = client.post(
            "/api/erp/query/financial",
            json={"query": "Show me company profit margins"},
            headers=headers
        )
        
        assert response.status_code == 403
        assert "No access to requested financial data" in response.json()["detail"]
    
    def test_document_access_with_authorization(self):
        """Test document access with proper authorization"""
        
        headers = {"Authorization": "Bearer <finance_manager_jwt_token>"}
        
        response = client.get(
            "/api/erp/documents/financial_report_001",
            headers=headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "document" in result
        assert "access_level" in result
```

## Performance Optimization

### 1. Connection Pooling

```python
# app/auth/cerbos_pool.py
import asyncio
from typing import List
from .cerbos_client import ERPCerbosClient

class CerbosConnectionPool:
    def __init__(self, host: str, port: int, pool_size: int = 10):
        self.host = host
        self.port = port
        self.pool_size = pool_size
        self.pool: List[ERPCerbosClient] = []
        self.available: asyncio.Queue = asyncio.Queue(maxsize=pool_size)
        
    async def initialize(self):
        """Initialize connection pool"""
        for _ in range(self.pool_size):
            client = ERPCerbosClient(self.host, self.port)
            await client.connect()
            self.pool.append(client)
            await self.available.put(client)
    
    async def get_client(self) -> ERPCerbosClient:
        """Get client from pool"""
        return await self.available.get()
    
    async def return_client(self, client: ERPCerbosClient):
        """Return client to pool"""
        await self.available.put(client)
    
    async def close_all(self):
        """Close all connections"""
        while not self.available.empty():
            client = await self.available.get()
            await client.disconnect()

# Global connection pool
cerbos_pool = CerbosConnectionPool("localhost", 3593, pool_size=10)
```

### 2. Response Caching

```python
# app/auth/cerbos_cache.py
import json
import hashlib
from typing import Dict, Any, Optional
from app.core.cache import CacheService

class CerbosResponseCache:
    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
        self.default_ttl = 300  # 5 minutes
    
    def _generate_cache_key(self, user_id: str, resource_kind: str, 
                           resource_id: str, action: str) -> str:
        """Generate cache key for authorization decision"""
        key_data = f"{user_id}:{resource_kind}:{resource_id}:{action}"
        return f"cerbos_auth:{hashlib.md5(key_data.encode()).hexdigest()}"
    
    async def get_cached_decision(self, user_id: str, resource_kind: str,
                                resource_id: str, action: str) -> Optional[bool]:
        """Get cached authorization decision"""
        cache_key = self._generate_cache_key(user_id, resource_kind, resource_id, action)
        result = await self.cache.get(cache_key)
        return result
    
    async def cache_decision(self, user_id: str, resource_kind: str,
                           resource_id: str, action: str, decision: bool, ttl: int = None):
        """Cache authorization decision"""
        cache_key = self._generate_cache_key(user_id, resource_kind, resource_id, action)
        ttl = ttl or self.default_ttl
        await self.cache.set(cache_key, decision, ttl)
```

This comprehensive Cerbos integration guide provides everything needed to implement robust authorization in your ERP RBAC-RAG system. The next documents will cover specific ERP policies, database connectors, and use cases.