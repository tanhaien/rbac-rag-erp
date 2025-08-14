# ERP-RBAC-RAG Architecture with Cerbos Integration

## Executive Summary

This document presents the final architecture for a Role-Based Access Control (RBAC) integrated Retrieval Augmented Generation (RAG) system specifically designed for Enterprise Resource Planning (ERP) environments. The architecture leverages Cerbos as the primary authorization engine to provide secure, scalable, and compliant access to ERP data through intelligent query processing.

## Architecture Overview

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[Web Dashboard]
        API_GW[API Gateway]
    end
    
    subgraph "Authentication Layer"
        AUTH[JWT Auth Service]
        CERBOS[Cerbos Authorization Engine]
    end
    
    subgraph "ERP Integration Layer"
        SAP[SAP Connector]
        ORACLE[Oracle EBS Connector]
        DYNAMICS[Dynamics 365 Connector]
        NETSUITE[NetSuite Connector]
    end
    
    subgraph "RAG Processing Layer"
        QUERY[Query Processor]
        RETRIEVER[Context Retriever]
        LLM[Language Model]
        FILTER[Response Filter]
    end
    
    subgraph "Data Layer"
        POSTGRES[(PostgreSQL)]
        VECTOR[(ChromaDB)]
        CACHE[(Redis Cache)]
        ERP_DWH[(ERP Data Warehouse)]
    end
    
    subgraph "Security & Compliance"
        AUDIT[Audit Service]
        ENCRYPT[Encryption Service]
        COMPLIANCE[Compliance Monitor]
    end
    
    UI --> API_GW
    API_GW --> AUTH
    AUTH --> CERBOS
    CERBOS --> QUERY
    
    QUERY --> SAP
    QUERY --> ORACLE  
    QUERY --> DYNAMICS
    QUERY --> NETSUITE
    
    QUERY --> RETRIEVER
    RETRIEVER --> VECTOR
    RETRIEVER --> POSTGRES
    
    RETRIEVER --> LLM
    LLM --> FILTER
    FILTER --> CERBOS
    
    SAP --> ERP_DWH
    ORACLE --> ERP_DWH
    DYNAMICS --> ERP_DWH
    NETSUITE --> ERP_DWH
    
    FILTER --> AUDIT
    QUERY --> COMPLIANCE
```

## Core Components

### 1. Cerbos Authorization Engine

**Role**: Primary authorization decision point for all ERP data access

**Key Features:**
- Context-aware policy evaluation
- Multi-tenant support for different companies/subsidiaries
- Real-time authorization decisions (5-20ms latency)
- YAML-based policy definitions
- Audit trail for all authorization decisions

**ERP-Specific Capabilities:**
```yaml
# Example Cerbos policy for ERP financial data
apiVersion: "api.cerbos.dev/v1"
resourcePolicy:
  resource: "erp:financial_report"
  version: "default"
  rules:
    - actions: ["read"]
      effect: EFFECT_ALLOW
      roles: ["cfo", "finance_manager", "external_auditor"]
      condition:
        match:
          expr: >
            request.resource.attr.classification_level <= request.principal.attr.clearance_level &&
            request.resource.attr.department in request.principal.attr.accessible_departments
    
    - actions: ["read"]
      effect: EFFECT_ALLOW
      roles: ["ceo", "board_member"]
      # CEOs and board members can access all financial reports

    - actions: ["write", "delete"]
      effect: EFFECT_ALLOW
      roles: ["finance_manager"]
      condition:
        match:
          expr: >
            request.principal.attr.department == request.resource.attr.department &&
            request.resource.attr.report_type != "audit_report"
```

### 2. ERP Integration Layer

**Purpose**: Connect to various ERP systems and normalize data access

#### Supported ERP Systems:
- **SAP ECC/S4HANA**: Via RFC, OData, or REST APIs
- **Oracle EBS/Cloud**: Through Oracle Integration Cloud or direct DB access
- **Microsoft Dynamics 365**: Via Dataverse APIs and Power Platform
- **NetSuite**: Through RESTlets and SuiteTalk APIs
- **Custom ERP Systems**: Flexible connector framework

#### Data Synchronization Patterns:
```python
# ERP Connector Interface
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class ERPConnector(ABC):
    @abstractmethod
    async def connect(self, credentials: Dict[str, str]) -> bool:
        pass
    
    @abstractmethod
    async def fetch_financial_data(self, query: Dict[str, Any]) -> List[Dict]:
        pass
    
    @abstractmethod
    async def fetch_hr_data(self, user_context: Dict[str, Any]) -> List[Dict]:
        pass
    
    @abstractmethod
    async def fetch_operational_data(self, filters: Dict[str, Any]) -> List[Dict]:
        pass

# SAP Implementation Example
class SAPConnector(ERPConnector):
    def __init__(self, rfc_config: Dict[str, str]):
        self.rfc_config = rfc_config
        self.connection = None
    
    async def connect(self, credentials: Dict[str, str]) -> bool:
        # SAP RFC connection logic
        from pyrfc import Connection
        self.connection = Connection(**self.rfc_config, **credentials)
        return self.connection.ping()
    
    async def fetch_financial_data(self, query: Dict[str, Any]) -> List[Dict]:
        # Call SAP BAPI or custom RFC function
        result = self.connection.call('BAPI_GL_ACC_BALANCE_GET', {
            'COMPANYCODE': query.get('company_code'),
            'FISCALYEAR': query.get('fiscal_year'),
            'KEYDATE': query.get('key_date')
        })
        return result.get('BALANCE_ITEMS', [])
```

### 3. ERP-Specific Role Hierarchy

```yaml
# ERP Role Definitions for Cerbos
roles:
  # Executive Level
  ceo:
    permissions: ["read:all", "analytics:executive"]
    inherits: []
    
  cfo:
    permissions: ["read:financial", "read:budget", "write:financial_planning"]
    inherits: ["senior_manager"]
    
  coo:
    permissions: ["read:operational", "read:supply_chain", "write:operations"]
    inherits: ["senior_manager"]
    
  # Management Level
  finance_manager:
    permissions: ["read:financial", "write:budget", "read:audit"]
    inherits: ["manager"]
    departments: ["finance", "accounting"]
    
  hr_manager:
    permissions: ["read:hr", "write:hr", "read:payroll"]
    inherits: ["manager"]
    departments: ["human_resources"]
    
  operations_manager:
    permissions: ["read:inventory", "write:procurement", "read:production"]
    inherits: ["manager"]
    departments: ["operations", "manufacturing"]
    
  # Operational Level
  accountant:
    permissions: ["read:financial", "write:journal_entries"]
    inherits: ["employee"]
    departments: ["finance", "accounting"]
    
  hr_specialist:
    permissions: ["read:hr", "write:employee_records"]
    inherits: ["employee"]
    departments: ["human_resources"]
    
  # External Roles
  external_auditor:
    permissions: ["read:financial", "read:audit_trail"]
    inherits: []
    restrictions: ["no_write", "audit_only"]
    
  consultant:
    permissions: ["read:project_data"]
    inherits: []
    restrictions: ["temporary_access", "project_scoped"]
```

### 4. ERP Document Classification System

```python
# ERP Document Classification
ERP_DOCUMENT_TYPES = {
    "financial": {
        "profit_loss": {
            "classification": "confidential",
            "required_roles": ["cfo", "finance_manager", "accountant", "external_auditor"],
            "retention_period": "7_years"
        },
        "balance_sheet": {
            "classification": "confidential", 
            "required_roles": ["cfo", "finance_manager", "external_auditor"],
            "retention_period": "7_years"
        },
        "cash_flow": {
            "classification": "restricted",
            "required_roles": ["cfo", "ceo"],
            "retention_period": "10_years"
        },
        "budget_planning": {
            "classification": "internal",
            "required_roles": ["cfo", "finance_manager", "department_heads"],
            "retention_period": "5_years"
        }
    },
    
    "human_resources": {
        "employee_records": {
            "classification": "restricted",
            "required_roles": ["hr_manager", "hr_specialist"],
            "data_subject_rights": True,  # GDPR compliance
            "retention_period": "employee_lifetime_plus_7_years"
        },
        "payroll_data": {
            "classification": "restricted",
            "required_roles": ["hr_manager", "payroll_specialist"],
            "encryption_required": True,
            "retention_period": "7_years"
        },
        "performance_reviews": {
            "classification": "confidential",
            "required_roles": ["hr_manager", "direct_manager", "employee_self"],
            "retention_period": "3_years"
        }
    },
    
    "operational": {
        "inventory_reports": {
            "classification": "internal",
            "required_roles": ["operations_manager", "warehouse_manager", "inventory_analyst"],
            "retention_period": "2_years"
        },
        "vendor_contracts": {
            "classification": "confidential",
            "required_roles": ["operations_manager", "procurement_manager", "legal"],
            "retention_period": "contract_term_plus_7_years"
        },
        "quality_reports": {
            "classification": "internal",
            "required_roles": ["quality_manager", "operations_manager", "compliance_officer"],
            "retention_period": "5_years"
        }
    },
    
    "compliance": {
        "audit_reports": {
            "classification": "restricted",
            "required_roles": ["ceo", "cfo", "compliance_officer", "external_auditor"],
            "immutable": True,
            "retention_period": "permanent"
        },
        "sox_documentation": {
            "classification": "restricted",
            "required_roles": ["cfo", "compliance_officer", "external_auditor"],
            "regulatory_requirement": "SOX_404",
            "retention_period": "7_years"
        }
    }
}
```

### 5. RAG Query Processing with ERP Context

```python
class ERPRAGProcessor:
    def __init__(self, cerbos_client, erp_connectors, vector_db):
        self.cerbos = cerbos_client
        self.erp_connectors = erp_connectors
        self.vector_db = vector_db
    
    async def process_erp_query(self, query: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process ERP-specific RAG query with authorization"""
        
        # Step 1: Analyze query intent and extract ERP entities
        erp_entities = await self._extract_erp_entities(query)
        
        # Step 2: Check authorization for each entity type
        authorized_entities = []
        for entity in erp_entities:
            if await self._check_entity_access(entity, user_context):
                authorized_entities.append(entity)
        
        # Step 3: Retrieve relevant documents from authorized sources
        documents = await self._retrieve_authorized_documents(
            query, authorized_entities, user_context
        )
        
        # Step 4: Fetch real-time ERP data if needed
        erp_data = await self._fetch_erp_data(authorized_entities, user_context)
        
        # Step 5: Generate response with ERP context
        response = await self._generate_erp_response(
            query, documents, erp_data, user_context
        )
        
        # Step 6: Apply final authorization filters
        filtered_response = await self._apply_response_filters(response, user_context)
        
        return filtered_response
    
    async def _extract_erp_entities(self, query: str) -> List[Dict[str, Any]]:
        """Extract ERP-specific entities from query"""
        
        # ERP entity patterns
        patterns = {
            'financial': ['revenue', 'profit', 'budget', 'expense', 'cost', 'financial'],
            'hr': ['employee', 'staff', 'headcount', 'payroll', 'performance'],
            'operational': ['inventory', 'stock', 'vendor', 'supplier', 'production'],
            'time_period': ['Q1', 'Q2', 'Q3', 'Q4', 'monthly', 'yearly', 'YTD'],
            'departments': ['engineering', 'sales', 'marketing', 'finance', 'hr']
        }
        
        entities = []
        query_lower = query.lower()
        
        for entity_type, keywords in patterns.items():
            for keyword in keywords:
                if keyword in query_lower:
                    entities.append({
                        'type': entity_type,
                        'keyword': keyword,
                        'context': 'erp_query'
                    })
        
        return entities
    
    async def _check_entity_access(self, entity: Dict[str, Any], user_context: Dict[str, Any]) -> bool:
        """Check if user has access to specific ERP entity type"""
        
        resource_type = f"erp:{entity['type']}"
        
        check_result = await self.cerbos.check_resource(
            principal=user_context,
            resource={
                "kind": resource_type,
                "id": entity['keyword'],
                "attr": {"entity_type": entity['type']}
            },
            action="read"
        )
        
        return check_result.is_allowed
    
    async def _retrieve_authorized_documents(self, query: str, entities: List[Dict], 
                                           user_context: Dict[str, Any]) -> List[Dict]:
        """Retrieve documents with ERP entity-based filtering"""
        
        # Build search filters based on authorized entities
        entity_types = [e['type'] for e in entities]
        
        search_filters = {
            'document_types': entity_types,
            'user_roles': user_context['roles'],
            'user_department': user_context.get('department'),
            'classification_clearance': user_context.get('clearance_level', 'internal')
        }
        
        # Vector search with authorization
        results = await self.vector_db.search_with_filters(
            query=query,
            filters=search_filters,
            limit=10
        )
        
        # Additional Cerbos validation for each document
        authorized_docs = []
        for doc in results:
            if await self._validate_document_access(doc, user_context):
                authorized_docs.append(doc)
        
        return authorized_docs
    
    async def _fetch_erp_data(self, entities: List[Dict], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch real-time ERP data based on entities and user context"""
        
        erp_data = {}
        
        for entity in entities:
            if entity['type'] == 'financial':
                # Fetch financial data from ERP
                financial_data = await self.erp_connectors['sap'].fetch_financial_data({
                    'company_code': user_context.get('company_code'),
                    'fiscal_year': '2024',
                    'user_department': user_context.get('department')
                })
                erp_data['financial'] = financial_data
                
            elif entity['type'] == 'hr':
                # Fetch HR data with privacy controls
                hr_data = await self.erp_connectors['hr_system'].fetch_hr_data({
                    'user_clearance': user_context.get('clearance_level'),
                    'accessible_departments': user_context.get('accessible_departments', [])
                })
                erp_data['hr'] = hr_data
                
            elif entity['type'] == 'operational':
                # Fetch operational data
                ops_data = await self.erp_connectors['erp'].fetch_operational_data({
                    'user_roles': user_context['roles'],
                    'location_access': user_context.get('accessible_locations', [])
                })
                erp_data['operational'] = ops_data
        
        return erp_data
```

### 6. Security and Compliance Framework

#### SOX Compliance Implementation:
```python
class SOXComplianceService:
    def __init__(self, audit_service):
        self.audit_service = audit_service
    
    async def validate_financial_access(self, user_context: Dict, document_id: str) -> bool:
        """Validate SOX compliance for financial document access"""
        
        # SOX Section 404 - Internal Controls
        controls_check = await self._check_internal_controls(user_context, document_id)
        
        # Segregation of duties
        segregation_check = await self._check_segregation_of_duties(user_context)
        
        # Access approval workflow
        approval_check = await self._check_access_approval(user_context, document_id)
        
        # Log compliance check
        await self.audit_service.log_compliance_check(
            user_id=user_context['user_id'],
            document_id=document_id,
            compliance_type='SOX_404',
            checks={
                'internal_controls': controls_check,
                'segregation_of_duties': segregation_check,
                'access_approval': approval_check
            }
        )
        
        return all([controls_check, segregation_check, approval_check])
```

#### GDPR Compliance for HR Data:
```python
class GDPRComplianceService:
    async def handle_hr_data_access(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle HR data access with GDPR compliance"""
        
        # Data minimization - only return necessary fields
        filtered_data = await self._apply_data_minimization(request)
        
        # Pseudonymization for analytics
        if request.get('purpose') == 'analytics':
            filtered_data = await self._pseudonymize_data(filtered_data)
        
        # Log data processing activity
        await self._log_gdpr_processing(request, filtered_data)
        
        return filtered_data
```

### 7. Performance Optimization for ERP Scale

#### Query Caching Strategy:
```python
class ERPQueryCache:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.cache_ttl = {
            'financial_reports': 3600,  # 1 hour - financial data changes less frequently
            'hr_analytics': 7200,       # 2 hours - HR data is relatively stable
            'inventory_data': 300,      # 5 minutes - inventory changes frequently
            'real_time_metrics': 60     # 1 minute - operational metrics
        }
    
    async def get_cached_query(self, query_hash: str, data_type: str) -> Optional[Dict]:
        """Get cached query result with data-type specific TTL"""
        
        cache_key = f"erp_query:{data_type}:{query_hash}"
        cached_result = await self.redis.get(cache_key)
        
        if cached_result:
            return json.loads(cached_result)
        
        return None
    
    async def cache_query_result(self, query_hash: str, data_type: str, result: Dict):
        """Cache query result with appropriate TTL"""
        
        ttl = self.cache_ttl.get(data_type, 1800)  # Default 30 minutes
        cache_key = f"erp_query:{data_type}:{query_hash}"
        
        await self.redis.setex(
            cache_key,
            ttl,
            json.dumps(result, default=str)
        )
```

## Deployment Architecture

### Production Environment:
```yaml
# docker-compose.erp-prod.yml
version: '3.8'
services:
  # Core Services
  erp-rag-api:
    image: erp-rag:latest
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres-primary:5432/erp_rag
      - CERBOS_URL=http://cerbos:3593
      - REDIS_URL=redis://redis-cluster:6379
    depends_on:
      - postgres-primary
      - cerbos
      - redis-cluster
  
  # Authorization Engine
  cerbos:
    image: ghcr.io/cerbos/cerbos:latest
    volumes:
      - ./cerbos-policies:/policies
    environment:
      - CERBOS_CONFIG=/config/config.yaml
  
  # ERP Connectors
  sap-connector:
    image: erp-sap-connector:latest
    environment:
      - SAP_ASHOST=${SAP_HOST}
      - SAP_CLIENT=${SAP_CLIENT}
      - SAP_SYSNR=${SAP_SYSTEM_NUMBER}
    secrets:
      - sap-credentials
  
  oracle-connector:
    image: erp-oracle-connector:latest
    environment:
      - ORACLE_HOST=${ORACLE_HOST}
      - ORACLE_PORT=${ORACLE_PORT}
      - ORACLE_SERVICE=${ORACLE_SERVICE}
    secrets:
      - oracle-credentials
  
  # Data Layer
  postgres-primary:
    image: postgres:14
    environment:
      - POSTGRES_DB=erp_rag
      - POSTGRES_REPLICATION_MODE=master
    volumes:
      - postgres-primary-data:/var/lib/postgresql/data
  
  postgres-replica:
    image: postgres:14
    environment:
      - POSTGRES_REPLICATION_MODE=slave
      - POSTGRES_MASTER_HOST=postgres-primary
    volumes:
      - postgres-replica-data:/var/lib/postgresql/data
  
  chromadb:
    image: chromadb/chroma:latest
    environment:
      - CHROMA_SERVER_AUTH_CREDENTIALS_PROVIDER=chromadb.auth.token.TokenAuthCredentialsProvider
      - CHROMA_SERVER_AUTH_TOKEN_TRANSPORT_HEADER=Authorization
    volumes:
      - chromadb-data:/chroma/chroma
  
  redis-cluster:
    image: redis:7-alpine
    command: redis-server --appendonly yes --cluster-enabled yes
    volumes:
      - redis-data:/data

volumes:
  postgres-primary-data:
  postgres-replica-data:
  chromadb-data:
  redis-data:

secrets:
  sap-credentials:
    file: ./secrets/sap-credentials.json
  oracle-credentials:
    file: ./secrets/oracle-credentials.json
```

## Monitoring and Observability

### Key Metrics:
- **Authorization Performance**: Cerbos decision latency (target < 20ms)
- **ERP Query Performance**: End-to-end query processing time
- **Cache Hit Rates**: For different ERP data types
- **Compliance Violations**: SOX, GDPR violation alerts
- **User Access Patterns**: Unusual access pattern detection

### Alerting Rules:
```yaml
# Prometheus alerting rules
groups:
  - name: erp-rag-alerts
    rules:
      - alert: HighAuthorizationLatency
        expr: cerbos_decision_latency_p95 > 0.05  # 50ms
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High Cerbos authorization latency"
      
      - alert: ComplianceViolation
        expr: increase(compliance_violations_total[5m]) > 0
        for: 0s
        labels:
          severity: critical
        annotations:
          summary: "Compliance violation detected"
      
      - alert: ERPConnectionFailure
        expr: up{job="erp-connectors"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "ERP system connection failure"
```

## Success Metrics

### Technical KPIs:
- Query response time < 2 seconds (90th percentile)
- Authorization decision time < 20ms (95th percentile)
- System availability > 99.9%
- Cache hit rate > 80% for financial queries

### Business KPIs:
- User adoption rate across different ERP modules
- Reduction in manual report generation time
- Compliance audit success rate
- User satisfaction scores for query accuracy

## Conclusion

This ERP-RBAC-RAG architecture with Cerbos integration provides a robust, secure, and scalable solution for intelligent access to enterprise data. The design ensures compliance with regulatory requirements while delivering excellent user experience through context-aware authorization and optimized query processing.

Key advantages:
- **Security-First**: Multi-layered authorization with audit trails
- **ERP-Native**: Purpose-built for enterprise resource planning systems
- **Compliance-Ready**: SOX, GDPR, and industry-specific regulations
- **High-Performance**: Sub-second query responses with intelligent caching
- **Scalable**: Designed to handle enterprise-scale data volumes