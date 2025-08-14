# ERP Database Connectors for RBAC-RAG System

## Overview

This document provides comprehensive implementation details for connecting to major ERP systems including SAP, Oracle EBS, Microsoft Dynamics 365, NetSuite, and other enterprise systems. The connectors are designed with security, performance, and scalability in mind while maintaining proper authorization controls.

## Connector Architecture

### 1. Base Connector Interface

```python
# app/erp/connectors/base_connector.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ConnectionStatus(Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    CONNECTING = "connecting"

class DataCategory(Enum):
    FINANCIAL = "financial"
    HR = "hr"
    OPERATIONAL = "operational"
    INVENTORY = "inventory"
    PROCUREMENT = "procurement"
    SALES = "sales"
    COMPLIANCE = "compliance"

@dataclass
class ERPQuery:
    category: DataCategory
    filters: Dict[str, Any]
    user_context: Dict[str, Any]
    limit: Optional[int] = 1000
    offset: Optional[int] = 0

@dataclass
class ERPResult:
    data: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    total_count: int
    has_more: bool
    execution_time: float

class BaseERPConnector(ABC):
    """Base class for all ERP connectors"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None
        self.status = ConnectionStatus.DISCONNECTED
        self.last_error = None
        
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to ERP system"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Close connection to ERP system"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if connection is alive"""
        pass
    
    @abstractmethod
    async def query_financial_data(self, query: ERPQuery) -> ERPResult:
        """Query financial data with user context authorization"""
        pass
    
    @abstractmethod
    async def query_hr_data(self, query: ERPQuery) -> ERPResult:
        """Query HR data with privacy controls"""
        pass
    
    @abstractmethod
    async def query_operational_data(self, query: ERPQuery) -> ERPResult:
        """Query operational data with location-based access"""
        pass
    
    @abstractmethod
    async def get_metadata_schema(self, category: DataCategory) -> Dict[str, Any]:
        """Get metadata schema for data category"""
        pass
    
    async def execute_authorized_query(self, query: ERPQuery) -> ERPResult:
        """Execute query with proper authorization checks"""
        
        if self.status != ConnectionStatus.CONNECTED:
            raise ConnectionError(f"ERP connector not connected: {self.status}")
        
        # Log query for audit
        logger.info(f"Executing ERP query: category={query.category}, user={query.user_context.get('user_id')}")
        
        start_time = datetime.utcnow()
        
        try:
            # Route to appropriate query method
            if query.category == DataCategory.FINANCIAL:
                result = await self.query_financial_data(query)
            elif query.category == DataCategory.HR:
                result = await self.query_hr_data(query)
            elif query.category == DataCategory.OPERATIONAL:
                result = await self.query_operational_data(query)
            elif query.category == DataCategory.INVENTORY:
                result = await self.query_inventory_data(query)
            elif query.category == DataCategory.PROCUREMENT:
                result = await self.query_procurement_data(query)
            else:
                raise ValueError(f"Unsupported data category: {query.category}")
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            result.execution_time = execution_time
            
            return result
            
        except Exception as e:
            logger.error(f"ERP query failed: {e}")
            self.last_error = str(e)
            raise
    
    @abstractmethod
    async def query_inventory_data(self, query: ERPQuery) -> ERPResult:
        """Query inventory data"""
        pass
    
    @abstractmethod  
    async def query_procurement_data(self, query: ERPQuery) -> ERPResult:
        """Query procurement data"""
        pass
```

## SAP Connector Implementation

### 1. SAP ECC/S4HANA Connector

```python
# app/erp/connectors/sap_connector.py
from typing import Dict, List, Any, Optional
import asyncio
from pyrfc import Connection, ABAPApplicationError, ABAPRuntimeError
from .base_connector import BaseERPConnector, ERPQuery, ERPResult, ConnectionStatus, DataCategory
import pandas as pd

class SAPConnector(BaseERPConnector):
    """SAP ECC/S4HANA Connector using RFC calls"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.rfc_config = {
            'ashost': config.get('host'),
            'sysnr': config.get('system_number'),
            'client': config.get('client'),
            'user': config.get('username'),
            'passwd': config.get('password'),
            'lang': config.get('language', 'EN')
        }
        
    async def connect(self) -> bool:
        """Establish RFC connection to SAP"""
        try:
            self.status = ConnectionStatus.CONNECTING
            
            # Create RFC connection in thread pool since pyrfc is synchronous
            loop = asyncio.get_event_loop()
            self.connection = await loop.run_in_executor(
                None, lambda: Connection(**self.rfc_config)
            )
            
            # Test connection
            await loop.run_in_executor(None, self.connection.ping)
            
            self.status = ConnectionStatus.CONNECTED
            logger.info("SAP RFC connection established successfully")
            return True
            
        except Exception as e:
            self.status = ConnectionStatus.ERROR
            self.last_error = str(e)
            logger.error(f"SAP connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Close SAP RFC connection"""
        if self.connection:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.connection.close)
            self.connection = None
            self.status = ConnectionStatus.DISCONNECTED
    
    async def test_connection(self) -> bool:
        """Test SAP connection"""
        if not self.connection:
            return False
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.connection.ping)
            return True
        except:
            return False
    
    async def query_financial_data(self, query: ERPQuery) -> ERPResult:
        """Query SAP financial data using BAPIs"""
        
        filters = query.filters
        user_context = query.user_context
        
        # Determine which BAPI/RFC to call based on filters
        if 'profit_loss' in filters:
            return await self._query_profit_loss(query)
        elif 'balance_sheet' in filters:
            return await self._query_balance_sheet(query)
        elif 'cash_flow' in filters:
            return await self._query_cash_flow(query)
        elif 'gl_balance' in filters:
            return await self._query_gl_balance(query)
        else:
            return await self._query_general_financial(query)
    
    async def _query_profit_loss(self, query: ERPQuery) -> ERPResult:
        """Query P&L statement data"""
        
        filters = query.filters
        user_context = query.user_context
        
        # Build BAPI parameters
        bapi_params = {
            'COMPANYCODE': filters.get('company_code', user_context.get('company_code')),
            'FISCALYEAR': filters.get('fiscal_year', '2024'),
            'PERIOD_FROM': filters.get('period_from', '001'),
            'PERIOD_TO': filters.get('period_to', '012'),
            'LEDGER': filters.get('ledger', '0L'),
            'VARIANT': filters.get('variant', '000')
        }
        
        # Add department/profit center filters based on user access
        accessible_departments = user_context.get('accessible_departments', [])
        if accessible_departments:
            profit_centers = await self._get_profit_centers_for_departments(accessible_departments)
            bapi_params['PROFIT_CENTER_FROM'] = min(profit_centers)
            bapi_params['PROFIT_CENTER_TO'] = max(profit_centers)
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.connection.call('BAPI_PL_GETDATA', **bapi_params)
            )
            
            # Process result
            pl_data = result.get('RETURN_ITEMS', [])
            
            # Convert to standard format
            formatted_data = []
            for item in pl_data:
                formatted_data.append({
                    'account': item.get('GL_ACCOUNT'),
                    'account_name': item.get('GL_ACCOUNT_NAME'),
                    'amount': float(item.get('AMOUNT', 0)),
                    'currency': item.get('CURRENCY'),
                    'fiscal_year': item.get('FISCALYEAR'),
                    'period': item.get('PERIOD'),
                    'profit_center': item.get('PROFIT_CENTER'),
                    'cost_center': item.get('COST_CENTER'),
                    'document_type': 'profit_loss_statement'
                })
            
            return ERPResult(
                data=formatted_data,
                metadata={
                    'source': 'SAP_BAPI_PL_GETDATA',
                    'company_code': bapi_params['COMPANYCODE'],
                    'fiscal_year': bapi_params['FISCALYEAR'],
                    'query_parameters': bapi_params
                },
                total_count=len(formatted_data),
                has_more=False,
                execution_time=0  # Will be set by parent method
            )
            
        except (ABAPApplicationError, ABAPRuntimeError) as e:
            logger.error(f"SAP BAPI error: {e}")
            raise Exception(f"SAP query failed: {e}")
    
    async def _query_balance_sheet(self, query: ERPQuery) -> ERPResult:
        """Query Balance Sheet data"""
        
        filters = query.filters
        user_context = query.user_context
        
        bapi_params = {
            'COMPANYCODE': filters.get('company_code', user_context.get('company_code')),
            'FISCALYEAR': filters.get('fiscal_year', '2024'),
            'KEYDATE': filters.get('key_date', '20241231'),
            'LEDGER': filters.get('ledger', '0L')
        }
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.connection.call('BAPI_BS_GETDATA', **bapi_params)
            )
            
            bs_data = result.get('BALANCE_ITEMS', [])
            
            formatted_data = []
            for item in bs_data:
                formatted_data.append({
                    'account': item.get('GL_ACCOUNT'),
                    'account_name': item.get('GL_ACCOUNT_NAME'),
                    'balance': float(item.get('BALANCE', 0)),
                    'currency': item.get('CURRENCY'),
                    'fiscal_year': item.get('FISCALYEAR'),
                    'account_type': item.get('ACCOUNT_TYPE'),
                    'document_type': 'balance_sheet'
                })
            
            return ERPResult(
                data=formatted_data,
                metadata={
                    'source': 'SAP_BAPI_BS_GETDATA',
                    'company_code': bapi_params['COMPANYCODE'],
                    'key_date': bapi_params['KEYDATE']
                },
                total_count=len(formatted_data),
                has_more=False,
                execution_time=0
            )
            
        except Exception as e:
            logger.error(f"SAP Balance Sheet query failed: {e}")
            raise
    
    async def query_hr_data(self, query: ERPQuery) -> ERPResult:
        """Query SAP HR data using HR BAPIs"""
        
        filters = query.filters
        user_context = query.user_context
        
        # Check HR access permissions
        if not self._has_hr_access(user_context):
            raise PermissionError("No HR data access permission")
        
        if 'employee_info' in filters:
            return await self._query_employee_info(query)
        elif 'payroll' in filters:
            return await self._query_payroll_data(query)
        elif 'organizational_structure' in filters:
            return await self._query_org_structure(query)
        else:
            return await self._query_general_hr_data(query)
    
    async def _query_employee_info(self, query: ERPQuery) -> ERPResult:
        """Query employee information"""
        
        filters = query.filters
        user_context = query.user_context
        
        # Build employee selection criteria
        bapi_params = {
            'EMPLOYEENUMBER': filters.get('employee_number', ''),
            'BEGDA': filters.get('begin_date', '19000101'),
            'ENDDA': filters.get('end_date', '99991231')
        }
        
        # Apply department/organization filters
        accessible_departments = user_context.get('accessible_departments', [])
        if accessible_departments:
            org_units = await self._get_org_units_for_departments(accessible_departments)
            bapi_params['ORGUNIT'] = org_units
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.connection.call('BAPI_EMPLOYEE_GETDATA', **bapi_params)
            )
            
            employee_data = result.get('EMPLOYEE_LIST', [])
            
            formatted_data = []
            for emp in employee_data:
                # Apply GDPR data minimization
                emp_data = {
                    'employee_id': emp.get('PERNR'),
                    'first_name': emp.get('VORNA') if self._can_access_personal_data(user_context) else '[REDACTED]',
                    'last_name': emp.get('NACHN') if self._can_access_personal_data(user_context) else '[REDACTED]',
                    'position': emp.get('PLANS'),
                    'organization_unit': emp.get('ORGEH'),
                    'cost_center': emp.get('KOSTL'),
                    'hire_date': emp.get('EINDT'),
                    'employment_status': emp.get('STAT2'),
                    'document_type': 'employee_info'
                }
                
                # Apply additional GDPR filters
                if not self._has_sensitive_hr_access(user_context):
                    emp_data.pop('hire_date', None)
                
                formatted_data.append(emp_data)
            
            return ERPResult(
                data=formatted_data,
                metadata={
                    'source': 'SAP_BAPI_EMPLOYEE_GETDATA',
                    'gdpr_applied': True,
                    'data_minimization': not self._can_access_personal_data(user_context)
                },
                total_count=len(formatted_data),
                has_more=False,
                execution_time=0
            )
            
        except Exception as e:
            logger.error(f"SAP HR query failed: {e}")
            raise
    
    async def query_operational_data(self, query: ERPQuery) -> ERPResult:
        """Query SAP operational data"""
        
        filters = query.filters
        
        if 'material_master' in filters:
            return await self._query_material_master(query)
        elif 'purchase_orders' in filters:
            return await self._query_purchase_orders(query)
        elif 'sales_orders' in filters:
            return await self._query_sales_orders(query)
        elif 'production_orders' in filters:
            return await self._query_production_orders(query)
        else:
            return await self._query_general_operational(query)
    
    async def _query_material_master(self, query: ERPQuery) -> ERPResult:
        """Query material master data"""
        
        filters = query.filters
        user_context = query.user_context
        
        bapi_params = {
            'MATERIAL': filters.get('material_number', ''),
            'PLANT': filters.get('plant', ''),
            'VIEW': filters.get('view', 'BASIC')
        }
        
        # Apply location-based access control
        accessible_plants = user_context.get('accessible_locations', [])
        if accessible_plants and not bapi_params['PLANT']:
            # Query multiple plants if user has access
            results = []
            for plant in accessible_plants[:5]:  # Limit to 5 plants for performance
                plant_params = bapi_params.copy()
                plant_params['PLANT'] = plant
                
                try:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None,
                        lambda: self.connection.call('BAPI_MATERIAL_GETALL', **plant_params)
                    )
                    
                    materials = result.get('MATERIAL_GENERAL_DATA', [])
                    results.extend(materials)
                    
                except Exception as e:
                    logger.warning(f"Failed to query plant {plant}: {e}")
                    continue
        else:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.connection.call('BAPI_MATERIAL_GETALL', **bapi_params)
            )
            results = result.get('MATERIAL_GENERAL_DATA', [])
        
        formatted_data = []
        for material in results:
            formatted_data.append({
                'material_number': material.get('MATERIAL'),
                'material_description': material.get('MATL_DESC'),
                'material_type': material.get('MATL_TYPE'),
                'plant': material.get('PLANT'),
                'storage_location': material.get('STGE_LOC'),
                'base_unit': material.get('BASE_UOM'),
                'material_group': material.get('MATL_GROUP'),
                'created_on': material.get('CREATED_ON'),
                'document_type': 'material_master'
            })
        
        return ERPResult(
            data=formatted_data,
            metadata={
                'source': 'SAP_BAPI_MATERIAL_GETALL',
                'plants_queried': accessible_plants if accessible_plants else [bapi_params.get('PLANT')]
            },
            total_count=len(formatted_data),
            has_more=False,
            execution_time=0
        )
    
    async def query_inventory_data(self, query: ERPQuery) -> ERPResult:
        """Query SAP inventory/stock data"""
        
        filters = query.filters
        user_context = query.user_context
        
        bapi_params = {
            'MATERIAL': filters.get('material', ''),
            'PLANT': filters.get('plant', ''),
            'STORAGE_LOCATION': filters.get('storage_location', ''),
            'STOCK_TYPE': filters.get('stock_type', '')
        }
        
        # Apply location-based filtering
        accessible_plants = user_context.get('accessible_locations', [])
        if accessible_plants:
            if bapi_params['PLANT'] and bapi_params['PLANT'] not in accessible_plants:
                raise PermissionError(f"No access to plant {bapi_params['PLANT']}")
            
            if not bapi_params['PLANT']:
                # Query first accessible plant
                bapi_params['PLANT'] = accessible_plants[0]
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.connection.call('BAPI_MATERIAL_STOCK_REQ_LIST', **bapi_params)
            )
            
            stock_data = result.get('STOCK_LIST', [])
            
            formatted_data = []
            for stock in stock_data:
                formatted_data.append({
                    'material': stock.get('MATERIAL'),
                    'plant': stock.get('PLANT'),
                    'storage_location': stock.get('STGE_LOC'),
                    'stock_quantity': float(stock.get('STOCK_QTY', 0)),
                    'unit_of_measure': stock.get('UNIT'),
                    'stock_type': stock.get('STOCK_TYPE'),
                    'last_updated': stock.get('LAST_UPDATE'),
                    'document_type': 'inventory_stock'
                })
            
            return ERPResult(
                data=formatted_data,
                metadata={
                    'source': 'SAP_BAPI_MATERIAL_STOCK_REQ_LIST',
                    'plant': bapi_params['PLANT']
                },
                total_count=len(formatted_data),
                has_more=False,
                execution_time=0
            )
            
        except Exception as e:
            logger.error(f"SAP inventory query failed: {e}")
            raise
    
    async def query_procurement_data(self, query: ERPQuery) -> ERPResult:
        """Query SAP procurement data"""
        
        filters = query.filters
        user_context = query.user_context
        
        if 'purchase_orders' in filters:
            return await self._query_purchase_orders(query)
        elif 'vendor_master' in filters:
            return await self._query_vendor_master(query)
        elif 'purchase_requisitions' in filters:
            return await self._query_purchase_requisitions(query)
        else:
            return await self._query_general_procurement(query)
    
    async def _query_purchase_orders(self, query: ERPQuery) -> ERPResult:
        """Query purchase order data"""
        
        filters = query.filters
        user_context = query.user_context
        
        bapi_params = {
            'PURCHASEORDER': filters.get('po_number', ''),
            'COMPANYCODE': filters.get('company_code', user_context.get('company_code')),
            'PURCHASEORDERDATE': filters.get('po_date_from', ''),
            'VENDOR': filters.get('vendor', '')
        }
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.connection.call('BAPI_PO_GETITEMS', **bapi_params)
            )
            
            po_data = result.get('PO_ITEMS', [])
            
            formatted_data = []
            for po_item in po_data:
                # Apply procurement authority limits
                po_value = float(po_item.get('NET_VALUE', 0))
                authority_limit = user_context.get('procurement_authority_limit', 0)
                
                item_data = {
                    'purchase_order': po_item.get('PO_NUMBER'),
                    'po_item': po_item.get('PO_ITEM'),
                    'material': po_item.get('MATERIAL'),
                    'description': po_item.get('SHORT_TEXT'),
                    'vendor': po_item.get('VENDOR'),
                    'quantity': float(po_item.get('QUANTITY', 0)),
                    'unit': po_item.get('PO_UNIT'),
                    'net_value': po_value if authority_limit == 0 or po_value <= authority_limit else '[RESTRICTED]',
                    'currency': po_item.get('CURRENCY'),
                    'delivery_date': po_item.get('DELIV_DATE'),
                    'plant': po_item.get('PLANT'),
                    'document_type': 'purchase_order'
                }
                
                formatted_data.append(item_data)
            
            return ERPResult(
                data=formatted_data,
                metadata={
                    'source': 'SAP_BAPI_PO_GETITEMS',
                    'authority_limit_applied': authority_limit > 0
                },
                total_count=len(formatted_data),
                has_more=False,
                execution_time=0
            )
            
        except Exception as e:
            logger.error(f"SAP PO query failed: {e}")
            raise
    
    # Helper methods
    def _has_hr_access(self, user_context: Dict[str, Any]) -> bool:
        """Check if user has HR data access"""
        return (
            'hr_manager' in user_context.get('roles', []) or
            'hr_specialist' in user_context.get('roles', []) or
            user_context.get('department') == 'human_resources'
        )
    
    def _can_access_personal_data(self, user_context: Dict[str, Any]) -> bool:
        """Check if user can access personal data"""
        return (
            'hr_manager' in user_context.get('roles', []) or
            user_context.get('hr_clearance_level', 0) >= 3
        )
    
    def _has_sensitive_hr_access(self, user_context: Dict[str, Any]) -> bool:
        """Check if user has access to sensitive HR data"""
        return user_context.get('hr_clearance_level', 0) >= 4
    
    async def _get_profit_centers_for_departments(self, departments: List[str]) -> List[str]:
        """Map departments to profit centers"""
        # This would typically be configured or retrieved from SAP
        dept_to_pc_map = {
            'finance': ['1000', '1100'],
            'hr': ['2000'],
            'operations': ['3000', '3100', '3200'],
            'sales': ['4000', '4100']
        }
        
        profit_centers = []
        for dept in departments:
            profit_centers.extend(dept_to_pc_map.get(dept, []))
        
        return profit_centers or ['1000']  # Default fallback
    
    async def _get_org_units_for_departments(self, departments: List[str]) -> List[str]:
        """Map departments to organizational units"""
        dept_to_org_map = {
            'finance': ['50000001', '50000002'],
            'hr': ['50000003'],
            'operations': ['50000004', '50000005'],
            'sales': ['50000006']
        }
        
        org_units = []
        for dept in departments:
            org_units.extend(dept_to_org_map.get(dept, []))
        
        return org_units or ['50000001']
    
    async def get_metadata_schema(self, category: DataCategory) -> Dict[str, Any]:
        """Get SAP metadata schema for data category"""
        
        schemas = {
            DataCategory.FINANCIAL: {
                'fields': {
                    'account': 'string',
                    'account_name': 'string', 
                    'amount': 'number',
                    'currency': 'string',
                    'fiscal_year': 'string',
                    'period': 'string',
                    'profit_center': 'string',
                    'cost_center': 'string'
                },
                'required_fields': ['account', 'amount', 'currency'],
                'source_tables': ['FAGLFLEXT', 'GLT0', 'FAGLFLEXA']
            },
            DataCategory.HR: {
                'fields': {
                    'employee_id': 'string',
                    'first_name': 'string',
                    'last_name': 'string',
                    'position': 'string',
                    'organization_unit': 'string',
                    'cost_center': 'string',
                    'hire_date': 'date'
                },
                'required_fields': ['employee_id'],
                'source_tables': ['PA0000', 'PA0001', 'PA0002'],
                'privacy_fields': ['first_name', 'last_name', 'hire_date']
            },
            DataCategory.OPERATIONAL: {
                'fields': {
                    'material_number': 'string',
                    'material_description': 'string',
                    'plant': 'string',
                    'storage_location': 'string',
                    'stock_quantity': 'number',
                    'unit_of_measure': 'string'
                },
                'required_fields': ['material_number', 'plant'],
                'source_tables': ['MARA', 'MARC', 'MARD']
            }
        }
        
        return schemas.get(category, {})
```

## Oracle EBS Connector

### 2. Oracle E-Business Suite Connector

```python
# app/erp/connectors/oracle_connector.py
import asyncio
import asyncpg
from typing import Dict, List, Any, Optional
from .base_connector import BaseERPConnector, ERPQuery, ERPResult, ConnectionStatus, DataCategory

class OracleEBSConnector(BaseERPConnector):
    """Oracle E-Business Suite Connector using direct database queries"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.db_config = {
            'host': config.get('host'),
            'port': config.get('port', 1521),
            'database': config.get('database'),
            'user': config.get('username'),
            'password': config.get('password')
        }
        self.connection_pool = None
    
    async def connect(self) -> bool:
        """Establish connection pool to Oracle database"""
        try:
            self.status = ConnectionStatus.CONNECTING
            
            # Create PostgreSQL connection pool (using asyncpg for demo)
            # In production, use oracledb or cx_Oracle
            self.connection_pool = await asyncpg.create_pool(
                host=self.db_config['host'],
                port=self.db_config['port'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database=self.db_config['database'],
                min_size=5,
                max_size=20
            )
            
            self.status = ConnectionStatus.CONNECTED
            logger.info("Oracle EBS connection pool established")
            return True
            
        except Exception as e:
            self.status = ConnectionStatus.ERROR
            self.last_error = str(e)
            logger.error(f"Oracle EBS connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Close connection pool"""
        if self.connection_pool:
            await self.connection_pool.close()
            self.connection_pool = None
            self.status = ConnectionStatus.DISCONNECTED
    
    async def test_connection(self) -> bool:
        """Test Oracle connection"""
        if not self.connection_pool:
            return False
        
        try:
            async with self.connection_pool.acquire() as conn:
                await conn.execute("SELECT 1 FROM DUAL")
            return True
        except:
            return False
    
    async def query_financial_data(self, query: ERPQuery) -> ERPResult:
        """Query Oracle EBS financial data"""
        
        filters = query.filters
        user_context = query.user_context
        
        # Build SQL query based on filters
        if 'general_ledger' in filters:
            return await self._query_general_ledger(query)
        elif 'accounts_payable' in filters:
            return await self._query_accounts_payable(query)
        elif 'accounts_receivable' in filters:
            return await self._query_accounts_receivable(query)
        else:
            return await self._query_financial_summary(query)
    
    async def _query_general_ledger(self, query: ERPQuery) -> ERPResult:
        """Query GL balances from Oracle EBS"""
        
        filters = query.filters
        user_context = query.user_context
        
        # Build WHERE conditions
        where_conditions = ["1=1"]
        query_params = []
        
        # Company/Legal Entity filter
        if 'legal_entity_id' in filters:
            where_conditions.append("glb.legal_entity_id = $" + str(len(query_params) + 1))
            query_params.append(filters['legal_entity_id'])
        
        # Period filter
        if 'period_name' in filters:
            where_conditions.append("glb.period_name = $" + str(len(query_params) + 1))
            query_params.append(filters['period_name'])
        
        # Account segment filter based on user access
        accessible_accounts = self._get_accessible_accounts(user_context)
        if accessible_accounts:
            account_filter = "(" + " OR ".join([f"gcc.segment1 LIKE '{acc}%'" for acc in accessible_accounts]) + ")"
            where_conditions.append(account_filter)
        
        sql = f"""
            SELECT 
                glb.code_combination_id,
                gcc.segment1 as account_number,
                gcc.segment2 as cost_center,
                gcc.segment3 as department,
                glb.period_name,
                glb.begin_balance_dr,
                glb.begin_balance_cr,
                glb.period_net_dr,
                glb.period_net_cr,
                glb.end_balance_dr,
                glb.end_balance_cr,
                glb.currency_code,
                glb.set_of_books_id
            FROM gl_balances glb
            JOIN gl_code_combinations gcc ON glb.code_combination_id = gcc.code_combination_id
            WHERE {' AND '.join(where_conditions)}
            ORDER BY gcc.segment1, gcc.segment2
            LIMIT ${len(query_params) + 1}
        """
        
        query_params.append(query.limit or 1000)
        
        try:
            async with self.connection_pool.acquire() as conn:
                rows = await conn.fetch(sql, *query_params)
            
            formatted_data = []
            for row in rows:
                formatted_data.append({
                    'account_number': row['account_number'],
                    'cost_center': row['cost_center'],
                    'department': row['department'],
                    'period': row['period_name'],
                    'beginning_balance': float(row['begin_balance_dr'] or 0) - float(row['begin_balance_cr'] or 0),
                    'period_activity': float(row['period_net_dr'] or 0) - float(row['period_net_cr'] or 0),
                    'ending_balance': float(row['end_balance_dr'] or 0) - float(row['end_balance_cr'] or 0),
                    'currency': row['currency_code'],
                    'document_type': 'general_ledger'
                })
            
            return ERPResult(
                data=formatted_data,
                metadata={
                    'source': 'Oracle_GL_BALANCES',
                    'query_sql': sql,
                    'accessible_accounts': accessible_accounts
                },
                total_count=len(formatted_data),
                has_more=len(formatted_data) == query.limit,
                execution_time=0
            )
            
        except Exception as e:
            logger.error(f"Oracle GL query failed: {e}")
            raise
    
    async def query_hr_data(self, query: ERPQuery) -> ERPResult:
        """Query Oracle EBS HR data"""
        
        if not self._has_hr_access(query.user_context):
            raise PermissionError("No HR data access permission")
        
        filters = query.filters
        
        if 'employees' in filters:
            return await self._query_employees(query)
        elif 'payroll' in filters:
            return await self._query_payroll(query)
        else:
            return await self._query_employee_summary(query)
    
    async def _query_employees(self, query: ERPQuery) -> ERPResult:
        """Query employee data from Oracle EBS HRMS"""
        
        filters = query.filters
        user_context = query.user_context
        
        where_conditions = ["papf.current_employee_flag = 'Y'"]
        query_params = []
        
        # Department filter based on user access
        accessible_orgs = user_context.get('accessible_departments', [])
        if accessible_orgs:
            org_ids = await self._get_org_ids_for_departments(accessible_orgs)
            if org_ids:
                where_conditions.append(f"paaf.organization_id IN ({','.join(map(str, org_ids))})")
        
        # Employee number filter
        if 'employee_number' in filters:
            where_conditions.append("papf.employee_number = $" + str(len(query_params) + 1))
            query_params.append(filters['employee_number'])
        
        sql = f"""
            SELECT 
                papf.person_id,
                papf.employee_number,
                papf.first_name,
                papf.last_name,
                papf.full_name,
                papf.email_address,
                paaf.assignment_id,
                paaf.job_id,
                paaf.position_id,
                paaf.organization_id,
                paaf.supervisor_id,
                paaf.location_id,
                paaf.grade_id,
                pj.name as job_name,
                ho.name as organization_name
            FROM per_all_people_f papf
            JOIN per_all_assignments_f paaf ON papf.person_id = paaf.person_id
            LEFT JOIN per_jobs pj ON paaf.job_id = pj.job_id
            LEFT JOIN hr_organization_units ho ON paaf.organization_id = ho.organization_id
            WHERE {' AND '.join(where_conditions)}
            AND TRUNC(SYSDATE) BETWEEN papf.effective_start_date AND papf.effective_end_date
            AND TRUNC(SYSDATE) BETWEEN paaf.effective_start_date AND paaf.effective_end_date
            ORDER BY papf.employee_number
            LIMIT ${len(query_params) + 1}
        """
        
        query_params.append(query.limit or 1000)
        
        try:
            async with self.connection_pool.acquire() as conn:
                rows = await conn.fetch(sql, *query_params)
            
            formatted_data = []
            for row in rows:
                # Apply GDPR data minimization
                emp_data = {
                    'employee_number': row['employee_number'],
                    'employee_id': row['person_id'],
                    'first_name': row['first_name'] if self._can_access_personal_data(user_context) else '[REDACTED]',
                    'last_name': row['last_name'] if self._can_access_personal_data(user_context) else '[REDACTED]',
                    'email': row['email_address'] if self._can_access_personal_data(user_context) else '[REDACTED]',
                    'job_name': row['job_name'],
                    'organization_name': row['organization_name'],
                    'assignment_id': row['assignment_id'],
                    'document_type': 'employee_data'
                }
                formatted_data.append(emp_data)
            
            return ERPResult(
                data=formatted_data,
                metadata={
                    'source': 'Oracle_PER_ALL_PEOPLE_F',
                    'gdpr_applied': True,
                    'data_minimization': not self._can_access_personal_data(user_context)
                },
                total_count=len(formatted_data),
                has_more=len(formatted_data) == query.limit,
                execution_time=0
            )
            
        except Exception as e:
            logger.error(f"Oracle HR query failed: {e}")
            raise
    
    # Helper methods
    def _get_accessible_accounts(self, user_context: Dict[str, Any]) -> List[str]:
        """Get accessible account segments based on user context"""
        
        role_to_accounts = {
            'cfo': ['1', '2', '3', '4', '5'],  # All accounts
            'finance_manager': ['1', '2'],      # Assets and Liabilities
            'controller': ['1', '2', '3'],      # Assets, Liabilities, Equity
            'accountant': ['1'],                # Assets only
        }
        
        accessible_accounts = []
        for role in user_context.get('roles', []):
            accounts = role_to_accounts.get(role, [])
            accessible_accounts.extend(accounts)
        
        # Department-specific access
        dept = user_context.get('department')
        if dept == 'finance':
            accessible_accounts.extend(['1', '2', '3'])
        
        return list(set(accessible_accounts)) if accessible_accounts else ['1']
    
    async def _get_org_ids_for_departments(self, departments: List[str]) -> List[int]:
        """Map department names to Oracle organization IDs"""
        
        dept_map = {
            'finance': [101, 102],
            'hr': [201],
            'operations': [301, 302, 303],
            'sales': [401, 402]
        }
        
        org_ids = []
        for dept in departments:
            org_ids.extend(dept_map.get(dept, []))
        
        return org_ids or [101]
    
    def _has_hr_access(self, user_context: Dict[str, Any]) -> bool:
        """Check HR access permissions"""
        return (
            'hr_manager' in user_context.get('roles', []) or
            user_context.get('department') == 'human_resources'
        )
    
    def _can_access_personal_data(self, user_context: Dict[str, Any]) -> bool:
        """Check personal data access permissions"""
        return user_context.get('hr_clearance_level', 0) >= 3
```

## Microsoft Dynamics 365 Connector

### 3. Dynamics 365 Connector

```python
# app/erp/connectors/dynamics_connector.py
import aiohttp
import json
from typing import Dict, List, Any, Optional
from .base_connector import BaseERPConnector, ERPQuery, ERPResult, ConnectionStatus, DataCategory

class Dynamics365Connector(BaseERPConnector):
    """Microsoft Dynamics 365 Connector using OData APIs"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get('base_url')  # https://org.crm.dynamics.com
        self.tenant_id = config.get('tenant_id')
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.access_token = None
        self.session = None
    
    async def connect(self) -> bool:
        """Establish connection to Dynamics 365"""
        try:
            self.status = ConnectionStatus.CONNECTING
            
            # Get OAuth2 access token
            token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            
            token_data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': f"{self.base_url}/.default"
            }
            
            self.session = aiohttp.ClientSession()
            
            async with self.session.post(token_url, data=token_data) as resp:
                if resp.status == 200:
                    token_response = await resp.json()
                    self.access_token = token_response['access_token']
                    self.status = ConnectionStatus.CONNECTED
                    logger.info("Dynamics 365 connection established")
                    return True
                else:
                    raise Exception(f"Token request failed: {resp.status}")
                    
        except Exception as e:
            self.status = ConnectionStatus.ERROR
            self.last_error = str(e)
            logger.error(f"Dynamics 365 connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Close Dynamics 365 connection"""
        if self.session:
            await self.session.close()
            self.session = None
            self.access_token = None
            self.status = ConnectionStatus.DISCONNECTED
    
    async def test_connection(self) -> bool:
        """Test Dynamics 365 connection"""
        if not self.session or not self.access_token:
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            async with self.session.get(f"{self.base_url}/api/data/v9.2/organizations", headers=headers) as resp:
                return resp.status == 200
        except:
            return False
    
    async def query_financial_data(self, query: ERPQuery) -> ERPResult:
        """Query Dynamics 365 financial data"""
        
        filters = query.filters
        
        if 'accounts' in filters:
            return await self._query_accounts(query)
        elif 'transactions' in filters:
            return await self._query_transactions(query)
        elif 'budget' in filters:
            return await self._query_budget_data(query)
        else:
            return await self._query_financial_summary(query)
    
    async def _query_accounts(self, query: ERPQuery) -> ERPResult:
        """Query chart of accounts"""
        
        filters = query.filters
        user_context = query.user_context
        
        # Build OData query
        odata_filter = []
        
        if 'account_type' in filters:
            odata_filter.append(f"accounttype eq '{filters['account_type']}'")
        
        # Apply department-based filtering
        accessible_depts = user_context.get('accessible_departments', [])
        if accessible_depts and 'cfo' not in user_context.get('roles', []):
            dept_filter = " or ".join([f"contains(name, '{dept}')" for dept in accessible_depts])
            odata_filter.append(f"({dept_filter})")
        
        filter_str = ' and '.join(odata_filter) if odata_filter else ''
        
        url = f"{self.base_url}/api/data/v9.2/accounts"
        params = {
            '$select': 'accountid,name,accountnumber,accountcategorycode,balance,creditlimit',
            '$top': query.limit or 1000
        }
        
        if filter_str:
            params['$filter'] = filter_str
        
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            async with self.session.get(url, params=params, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    accounts = data.get('value', [])
                    
                    formatted_data = []
                    for account in accounts:
                        formatted_data.append({
                            'account_id': account.get('accountid'),
                            'account_name': account.get('name'),
                            'account_number': account.get('accountnumber'),
                            'account_category': account.get('accountcategorycode'),
                            'balance': float(account.get('balance', 0)),
                            'credit_limit': float(account.get('creditlimit', 0)),
                            'document_type': 'account_master'
                        })
                    
                    return ERPResult(
                        data=formatted_data,
                        metadata={
                            'source': 'Dynamics365_Accounts',
                            'odata_filter': filter_str,
                            'total_records': len(formatted_data)
                        },
                        total_count=len(formatted_data),
                        has_more=len(formatted_data) == query.limit,
                        execution_time=0
                    )
                else:
                    raise Exception(f"API request failed: {resp.status}")
                    
        except Exception as e:
            logger.error(f"Dynamics 365 accounts query failed: {e}")
            raise
    
    async def query_hr_data(self, query: ERPQuery) -> ERPResult:
        """Query Dynamics 365 HR data"""
        
        if not self._has_hr_access(query.user_context):
            raise PermissionError("No HR data access permission")
        
        return await self._query_contacts_as_employees(query)
    
    async def _query_contacts_as_employees(self, query: ERPQuery) -> ERPResult:
        """Query employee data from Dynamics contacts"""
        
        filters = query.filters
        user_context = query.user_context
        
        odata_filter = ["statecode eq 0"]  # Active contacts only
        
        if 'department' in filters:
            odata_filter.append(f"contains(department, '{filters['department']}')")
        
        url = f"{self.base_url}/api/data/v9.2/contacts"
        params = {
            '$select': 'contactid,firstname,lastname,fullname,emailaddress1,jobtitle,department,telephone1',
            '$filter': ' and '.join(odata_filter),
            '$top': query.limit or 1000
        }
        
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            async with self.session.get(url, params=params, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    contacts = data.get('value', [])
                    
                    formatted_data = []
                    for contact in contacts:
                        # Apply GDPR data minimization
                        contact_data = {
                            'employee_id': contact.get('contactid'),
                            'first_name': contact.get('firstname') if self._can_access_personal_data(user_context) else '[REDACTED]',
                            'last_name': contact.get('lastname') if self._can_access_personal_data(user_context) else '[REDACTED]',
                            'full_name': contact.get('fullname') if self._can_access_personal_data(user_context) else '[REDACTED]',
                            'email': contact.get('emailaddress1') if self._can_access_personal_data(user_context) else '[REDACTED]',
                            'job_title': contact.get('jobtitle'),
                            'department': contact.get('department'),
                            'phone': contact.get('telephone1') if self._can_access_personal_data(user_context) else '[REDACTED]',
                            'document_type': 'employee_contact'
                        }
                        formatted_data.append(contact_data)
                    
                    return ERPResult(
                        data=formatted_data,
                        metadata={
                            'source': 'Dynamics365_Contacts',
                            'gdpr_applied': True,
                            'data_minimization': not self._can_access_personal_data(user_context)
                        },
                        total_count=len(formatted_data),
                        has_more=len(formatted_data) == query.limit,
                        execution_time=0
                    )
                else:
                    raise Exception(f"API request failed: {resp.status}")
                    
        except Exception as e:
            logger.error(f"Dynamics 365 HR query failed: {e}")
            raise
    
    async def query_operational_data(self, query: ERPQuery) -> ERPResult:
        """Query Dynamics 365 operational data"""
        
        filters = query.filters
        
        if 'opportunities' in filters:
            return await self._query_opportunities(query)
        elif 'quotes' in filters:
            return await self._query_quotes(query)
        else:
            return await self._query_sales_summary(query)
    
    # Helper methods
    def _has_hr_access(self, user_context: Dict[str, Any]) -> bool:
        """Check HR access permissions"""
        return (
            'hr_manager' in user_context.get('roles', []) or
            user_context.get('department') == 'human_resources'
        )
    
    def _can_access_personal_data(self, user_context: Dict[str, Any]) -> bool:
        """Check personal data access permissions"""
        return user_context.get('hr_clearance_level', 0) >= 3
```

## Connector Factory and Manager

### 4. ERP Connector Factory

```python
# app/erp/connectors/connector_factory.py
from typing import Dict, Any, Optional
from .base_connector import BaseERPConnector
from .sap_connector import SAPConnector
from .oracle_connector import OracleEBSConnector
from .dynamics_connector import Dynamics365Connector

class ERPConnectorFactory:
    """Factory for creating ERP connectors"""
    
    CONNECTOR_TYPES = {
        'sap': SAPConnector,
        'oracle_ebs': OracleEBSConnector,
        'dynamics365': Dynamics365Connector,
    }
    
    @classmethod
    def create_connector(cls, erp_type: str, config: Dict[str, Any]) -> BaseERPConnector:
        """Create ERP connector instance"""
        
        connector_class = cls.CONNECTOR_TYPES.get(erp_type.lower())
        if not connector_class:
            raise ValueError(f"Unsupported ERP type: {erp_type}")
        
        return connector_class(config)
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """Get list of supported ERP types"""
        return list(cls.CONNECTOR_TYPES.keys())

# app/erp/connectors/connector_manager.py
import asyncio
from typing import Dict, List, Any, Optional
from .connector_factory import ERPConnectorFactory
from .base_connector import BaseERPConnector, ERPQuery, ERPResult, ConnectionStatus

class ERPConnectorManager:
    """Manager for multiple ERP connectors"""
    
    def __init__(self):
        self.connectors: Dict[str, BaseERPConnector] = {}
        self.connection_configs: Dict[str, Dict[str, Any]] = {}
    
    async def add_connector(self, name: str, erp_type: str, config: Dict[str, Any]) -> bool:
        """Add and initialize ERP connector"""
        
        try:
            connector = ERPConnectorFactory.create_connector(erp_type, config)
            
            # Test connection
            if await connector.connect():
                self.connectors[name] = connector
                self.connection_configs[name] = {
                    'type': erp_type,
                    'config': config
                }
                logger.info(f"ERP connector '{name}' added successfully")
                return True
            else:
                logger.error(f"Failed to connect ERP connector '{name}'")
                return False
                
        except Exception as e:
            logger.error(f"Error adding ERP connector '{name}': {e}")
            return False
    
    async def get_connector(self, name: str) -> Optional[BaseERPConnector]:
        """Get ERP connector by name"""
        return self.connectors.get(name)
    
    async def query_erp(self, connector_name: str, query: ERPQuery) -> ERPResult:
        """Execute query on specific ERP connector"""
        
        connector = self.connectors.get(connector_name)
        if not connector:
            raise ValueError(f"ERP connector '{connector_name}' not found")
        
        if connector.status != ConnectionStatus.CONNECTED:
            # Attempt to reconnect
            if not await connector.connect():
                raise ConnectionError(f"ERP connector '{connector_name}' not connected")
        
        return await connector.execute_authorized_query(query)
    
    async def query_all_erps(self, query: ERPQuery) -> Dict[str, ERPResult]:
        """Execute query on all available ERP connectors"""
        
        results = {}
        tasks = []
        
        for name, connector in self.connectors.items():
            if connector.status == ConnectionStatus.CONNECTED:
                task = asyncio.create_task(
                    self.query_erp(name, query),
                    name=f"query_{name}"
                )
                tasks.append((name, task))
        
        # Wait for all queries to complete
        for name, task in tasks:
            try:
                result = await task
                results[name] = result
            except Exception as e:
                logger.error(f"Query failed for ERP '{name}': {e}")
                results[name] = None
        
        return results
    
    async def get_connection_status(self) -> Dict[str, str]:
        """Get connection status for all connectors"""
        
        status = {}
        for name, connector in self.connectors.items():
            status[name] = connector.status.value
        
        return status
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Health check for all connectors"""
        
        health_status = {}
        
        for name, connector in self.connectors.items():
            try:
                health_status[name] = await connector.test_connection()
            except Exception as e:
                logger.error(f"Health check failed for '{name}': {e}")
                health_status[name] = False
        
        return health_status
    
    async def disconnect_all(self):
        """Disconnect all ERP connectors"""
        
        for name, connector in self.connectors.items():
            try:
                await connector.disconnect()
                logger.info(f"Disconnected ERP connector '{name}'")
            except Exception as e:
                logger.error(f"Error disconnecting '{name}': {e}")

# Global connector manager instance
erp_connector_manager = ERPConnectorManager()
```

## Usage Examples

### 5. Integration with RAG System

```python
# app/services/erp_rag_service.py
from typing import Dict, List, Any
from ..erp.connectors.connector_manager import erp_connector_manager
from ..erp.connectors.base_connector import ERPQuery, DataCategory

class ERPRAGService:
    """Service to integrate ERP data with RAG system"""
    
    async def fetch_contextual_erp_data(self, 
                                      query_intent: str, 
                                      user_context: Dict[str, Any],
                                      erp_filters: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch ERP data based on RAG query intent"""
        
        # Determine data category from query intent
        category = self._determine_data_category(query_intent)
        
        # Build ERP query
        erp_query = ERPQuery(
            category=category,
            filters=erp_filters,
            user_context=user_context,
            limit=50  # Limit for performance
        )
        
        # Query all available ERP systems
        erp_results = await erp_connector_manager.query_all_erps(erp_query)
        
        # Aggregate and format results
        aggregated_data = self._aggregate_erp_results(erp_results)
        
        return {
            'erp_data': aggregated_data,
            'data_sources': list(erp_results.keys()),
            'category': category.value,
            'total_records': sum(len(result.data) if result else 0 for result in erp_results.values())
        }
    
    def _determine_data_category(self, query_intent: str) -> DataCategory:
        """Determine ERP data category from RAG query intent"""
        
        intent_lower = query_intent.lower()
        
        if any(term in intent_lower for term in ['revenue', 'profit', 'budget', 'financial', 'accounting']):
            return DataCategory.FINANCIAL
        elif any(term in intent_lower for term in ['employee', 'staff', 'hr', 'payroll', 'personnel']):
            return DataCategory.HR
        elif any(term in intent_lower for term in ['inventory', 'stock', 'materials', 'warehouse']):
            return DataCategory.INVENTORY
        elif any(term in intent_lower for term in ['purchase', 'vendor', 'supplier', 'procurement']):
            return DataCategory.PROCUREMENT
        else:
            return DataCategory.OPERATIONAL
    
    def _aggregate_erp_results(self, erp_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Aggregate results from multiple ERP systems"""
        
        aggregated = []
        
        for erp_name, result in erp_results.items():
            if result and result.data:
                for record in result.data:
                    record['erp_source'] = erp_name
                    record['source_metadata'] = result.metadata
                    aggregated.append(record)
        
        return aggregated

# Global ERP RAG service
erp_rag_service = ERPRAGService()
```

This comprehensive ERP connector framework provides secure, performant, and scalable integration with major ERP systems while maintaining proper authorization controls through the RBAC system. The next documents will cover document classification, use cases, and performance optimization.