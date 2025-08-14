# ERP Document Classification System

## Overview

This document defines a comprehensive classification system for ERP documents, reports, and data assets. The classification framework ensures proper access control, compliance with regulations, and efficient document management across financial, HR, operational, and compliance domains.

## Classification Framework

### 1. Classification Levels

```python
# Document Classification Levels
CLASSIFICATION_LEVELS = {
    "public": {
        "level": 0,
        "description": "Information that can be freely shared publicly",
        "access_requirement": "none",
        "examples": ["company blog posts", "press releases", "public financial reports"],
        "retention_period": "indefinite",
        "encryption_required": False,
        "audit_level": "basic"
    },
    
    "internal": {
        "level": 1, 
        "description": "Information for internal company use only",
        "access_requirement": "employee_status",
        "examples": ["internal policies", "org charts", "general announcements"],
        "retention_period": "5_years",
        "encryption_required": False,
        "audit_level": "standard"
    },
    
    "confidential": {
        "level": 2,
        "description": "Sensitive business information requiring authorization",
        "access_requirement": "role_based_clearance",
        "examples": ["financial reports", "strategic plans", "performance data"],
        "retention_period": "7_years",
        "encryption_required": True,
        "audit_level": "enhanced"
    },
    
    "restricted": {
        "level": 3,
        "description": "Highly sensitive information with strict access controls",
        "access_requirement": "executive_clearance",
        "examples": ["board minutes", "M&A documents", "legal settlements"],
        "retention_period": "permanent",
        "encryption_required": True,
        "audit_level": "comprehensive"
    },
    
    "top_secret": {
        "level": 4,
        "description": "Critical business secrets requiring highest security",
        "access_requirement": "c_suite_only",
        "examples": ["acquisition targets", "trade secrets", "regulatory investigations"],
        "retention_period": "permanent",
        "encryption_required": True,
        "audit_level": "forensic"
    }
}
```

### 2. Document Categories

```python
# ERP Document Categories
ERP_DOCUMENT_CATEGORIES = {
    "financial": {
        "description": "Financial statements, reports, and accounting documents",
        "subcategories": {
            "financial_statements": {
                "classification_range": ["confidential", "restricted"],
                "regulatory_requirements": ["SOX_404", "SEC_filing"],
                "typical_documents": [
                    "profit_loss_statement",
                    "balance_sheet", 
                    "cash_flow_statement",
                    "statement_of_equity"
                ]
            },
            "management_reports": {
                "classification_range": ["internal", "confidential"],
                "typical_documents": [
                    "budget_variance_reports",
                    "departmental_financials",
                    "cost_center_analysis",
                    "management_dashboards"
                ]
            },
            "audit_documents": {
                "classification_range": ["restricted", "top_secret"],
                "regulatory_requirements": ["SOX_404", "PCAOB"],
                "immutable": True,
                "typical_documents": [
                    "external_audit_reports",
                    "internal_audit_findings",
                    "sox_compliance_documentation",
                    "audit_trail_reports"
                ]
            },
            "tax_documents": {
                "classification_range": ["confidential", "restricted"],
                "regulatory_requirements": ["IRS", "local_tax_authorities"],
                "typical_documents": [
                    "tax_returns",
                    "tax_provision_calculations",
                    "transfer_pricing_documentation",
                    "tax_compliance_reports"
                ]
            },
            "treasury_documents": {
                "classification_range": ["restricted", "top_secret"],
                "typical_documents": [
                    "bank_statements",
                    "investment_portfolios",
                    "debt_agreements",
                    "cash_management_reports"
                ]
            }
        }
    },
    
    "human_resources": {
        "description": "Employee records, HR policies, and people-related documents",
        "data_protection_laws": ["GDPR", "CCPA", "PIPEDA"],
        "subcategories": {
            "employee_records": {
                "classification_range": ["confidential", "restricted"],
                "data_subject_rights": True,
                "typical_documents": [
                    "employee_personal_files",
                    "employment_contracts",
                    "background_check_results",
                    "immigration_documents"
                ]
            },
            "payroll_documents": {
                "classification_range": ["restricted", "top_secret"],
                "encryption_mandatory": True,
                "typical_documents": [
                    "payroll_registers",
                    "salary_information",
                    "bonus_calculations",
                    "tax_withholding_documents"
                ]
            },
            "performance_management": {
                "classification_range": ["confidential", "restricted"],
                "manager_accessible": True,
                "typical_documents": [
                    "performance_reviews",
                    "360_feedback_reports",
                    "career_development_plans",
                    "succession_planning_documents"
                ]
            },
            "benefits_administration": {
                "classification_range": ["confidential", "restricted"],
                "typical_documents": [
                    "health_insurance_records",
                    "retirement_plan_documents",
                    "workers_compensation_claims",
                    "leave_of_absence_records"
                ]
            },
            "disciplinary_records": {
                "classification_range": ["restricted", "top_secret"],
                "legal_sensitivity": "high",
                "typical_documents": [
                    "disciplinary_actions",
                    "investigation_reports",
                    "grievance_procedures",
                    "termination_documents"
                ]
            },
            "hr_policies": {
                "classification_range": ["internal", "confidential"],
                "employee_accessible": True,
                "typical_documents": [
                    "employee_handbook",
                    "code_of_conduct",
                    "diversity_policies",
                    "remote_work_guidelines"
                ]
            }
        }
    },
    
    "operational": {
        "description": "Operations, manufacturing, and supply chain documents",
        "subcategories": {
            "inventory_management": {
                "classification_range": ["internal", "confidential"],
                "real_time_updates": True,
                "typical_documents": [
                    "inventory_reports",
                    "stock_movement_records",
                    "cycle_count_results",
                    "obsolescence_analysis"
                ]
            },
            "procurement": {
                "classification_range": ["confidential", "restricted"],
                "vendor_sensitive": True,
                "typical_documents": [
                    "purchase_orders",
                    "vendor_contracts",
                    "rfp_responses",
                    "supplier_performance_reports"
                ]
            },
            "manufacturing": {
                "classification_range": ["internal", "confidential"],
                "location_specific": True,
                "typical_documents": [
                    "production_schedules",
                    "work_instructions",
                    "quality_control_reports",
                    "equipment_maintenance_logs"
                ]
            },
            "quality_assurance": {
                "classification_range": ["confidential", "restricted"],
                "regulatory_requirements": ["FDA", "ISO", "industry_specific"],
                "typical_documents": [
                    "quality_audit_reports",
                    "customer_complaint_logs",
                    "corrective_action_plans",
                    "supplier_quality_assessments"
                ]
            },
            "logistics": {
                "classification_range": ["internal", "confidential"],
                "customer_data_included": True,
                "typical_documents": [
                    "shipping_manifests",
                    "delivery_reports",
                    "freight_invoices",
                    "warehouse_activity_reports"
                ]
            }
        }
    },
    
    "sales_marketing": {
        "description": "Customer-related documents and sales information",
        "subcategories": {
            "customer_data": {
                "classification_range": ["confidential", "restricted"],
                "data_protection_laws": ["GDPR", "CCPA"],
                "typical_documents": [
                    "customer_master_records",
                    "sales_contracts",
                    "credit_applications",
                    "customer_communication_logs"
                ]
            },
            "sales_performance": {
                "classification_range": ["internal", "confidential"],
                "commission_sensitive": True,
                "typical_documents": [
                    "sales_reports",
                    "territory_analysis",
                    "commission_calculations",
                    "pipeline_reports"
                ]
            },
            "pricing": {
                "classification_range": ["restricted", "top_secret"],
                "competitive_sensitivity": "high",
                "typical_documents": [
                    "price_lists",
                    "discount_schedules",
                    "competitive_analysis",
                    "pricing_strategy_documents"
                ]
            },
            "marketing_campaigns": {
                "classification_range": ["internal", "confidential"],
                "typical_documents": [
                    "campaign_performance_reports",
                    "market_research_data",
                    "lead_generation_reports",
                    "brand_guidelines"
                ]
            }
        }
    },
    
    "compliance_legal": {
        "description": "Legal documents, compliance reports, and regulatory filings",
        "subcategories": {
            "regulatory_compliance": {
                "classification_range": ["confidential", "restricted"],
                "regulatory_requirements": ["industry_specific"],
                "immutable": True,
                "typical_documents": [
                    "compliance_reports",
                    "regulatory_filings",
                    "inspection_reports",
                    "violation_notices"
                ]
            },
            "contracts": {
                "classification_range": ["confidential", "restricted"],
                "legal_privilege": True,
                "typical_documents": [
                    "master_service_agreements",
                    "nda_agreements",
                    "employment_contracts",
                    "vendor_agreements"
                ]
            },
            "litigation": {
                "classification_range": ["restricted", "top_secret"],
                "attorney_client_privilege": True,
                "typical_documents": [
                    "legal_proceedings",
                    "settlement_agreements",
                    "court_filings",
                    "attorney_correspondence"
                ]
            },
            "intellectual_property": {
                "classification_range": ["restricted", "top_secret"],
                "trade_secret_protection": True,
                "typical_documents": [
                    "patent_applications",
                    "trademark_registrations",
                    "trade_secret_documentation",
                    "ip_licensing_agreements"
                ]
            }
        }
    },
    
    "it_security": {
        "description": "IT infrastructure, security, and technology documents",
        "subcategories": {
            "security_policies": {
                "classification_range": ["internal", "confidential"],
                "typical_documents": [
                    "information_security_policies",
                    "access_control_procedures",
                    "incident_response_plans",
                    "disaster_recovery_procedures"
                ]
            },
            "system_documentation": {
                "classification_range": ["confidential", "restricted"],
                "technical_sensitivity": True,
                "typical_documents": [
                    "system_architecture_diagrams",
                    "database_schemas",
                    "network_configurations",
                    "api_documentation"
                ]
            },
            "security_incidents": {
                "classification_range": ["restricted", "top_secret"],
                "incident_response_required": True,
                "typical_documents": [
                    "security_incident_reports",
                    "forensic_analysis_results",
                    "breach_notifications",
                    "remediation_plans"
                ]
            }
        }
    }
}
```

## Classification Engine

### 1. Automatic Classification Service

```python
# app/services/document_classification.py
import re
import spacy
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ClassificationResult:
    category: str
    subcategory: str
    classification_level: str
    confidence: float
    reasoning: List[str]
    regulatory_requirements: List[str]
    special_handling: Dict[str, Any]

class DocumentClassificationEngine:
    """Advanced document classification engine for ERP documents"""
    
    def __init__(self):
        # Load spaCy model for NLP
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found, using fallback classification")
            self.nlp = None
        
        self.classification_rules = self._load_classification_rules()
        self.keyword_mappings = self._build_keyword_mappings()
        self.regex_patterns = self._compile_regex_patterns()
    
    async def classify_document(self, 
                              content: str,
                              filename: str = "",
                              metadata: Dict[str, Any] = None) -> ClassificationResult:
        """Classify document based on content, filename, and metadata"""
        
        # Multi-stage classification approach
        results = []
        
        # Stage 1: Rule-based classification
        rule_result = await self._rule_based_classification(content, filename, metadata)
        results.append(rule_result)
        
        # Stage 2: Keyword-based classification
        keyword_result = await self._keyword_based_classification(content)
        results.append(keyword_result)
        
        # Stage 3: NLP-based classification (if available)
        if self.nlp:
            nlp_result = await self._nlp_based_classification(content)
            results.append(nlp_result)
        
        # Stage 4: Pattern-based classification
        pattern_result = await self._pattern_based_classification(content, filename)
        results.append(pattern_result)
        
        # Combine results and determine final classification
        final_result = await self._combine_classification_results(results, metadata)
        
        return final_result
    
    async def _rule_based_classification(self,
                                       content: str,
                                       filename: str,
                                       metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Apply rule-based classification logic"""
        
        content_lower = content.lower()
        filename_lower = filename.lower()
        
        # Financial document rules
        if any(term in content_lower for term in ['balance sheet', 'income statement', 'cash flow']):
            return {
                'category': 'financial',
                'subcategory': 'financial_statements',
                'classification_level': 'confidential',
                'confidence': 0.95,
                'reasoning': ['Financial statement keywords detected'],
                'regulatory_requirements': ['SOX_404']
            }
        
        # Audit document rules
        if any(term in content_lower for term in ['audit report', 'audit findings', 'sox compliance']):
            return {
                'category': 'financial',
                'subcategory': 'audit_documents',
                'classification_level': 'restricted',
                'confidence': 0.9,
                'reasoning': ['Audit document keywords detected'],
                'regulatory_requirements': ['SOX_404', 'PCAOB']
            }
        
        # HR document rules
        if any(term in content_lower for term in ['employee', 'payroll', 'performance review']):
            classification_level = 'restricted' if 'salary' in content_lower or 'payroll' in content_lower else 'confidential'
            return {
                'category': 'human_resources',
                'subcategory': 'employee_records' if 'employee' in content_lower else 'payroll_documents',
                'classification_level': classification_level,
                'confidence': 0.85,
                'reasoning': ['HR keywords detected'],
                'regulatory_requirements': ['GDPR'] if 'personal' in content_lower else []
            }
        
        # Contract rules
        if any(term in content_lower for term in ['agreement', 'contract', 'terms and conditions']):
            return {
                'category': 'compliance_legal',
                'subcategory': 'contracts',
                'classification_level': 'confidential',
                'confidence': 0.8,
                'reasoning': ['Contract keywords detected'],
                'regulatory_requirements': []
            }
        
        # Default classification
        return {
            'category': 'operational',
            'subcategory': 'general',
            'classification_level': 'internal',
            'confidence': 0.3,
            'reasoning': ['No specific classification rules matched'],
            'regulatory_requirements': []
        }
    
    async def _keyword_based_classification(self, content: str) -> Dict[str, Any]:
        """Classify based on keyword density and importance"""
        
        content_lower = content.lower()
        
        # Calculate keyword scores for each category
        category_scores = {}
        
        for category, keywords in self.keyword_mappings.items():
            score = 0
            matched_keywords = []
            
            for keyword, weight in keywords.items():
                if keyword in content_lower:
                    count = content_lower.count(keyword)
                    score += count * weight
                    matched_keywords.append(keyword)
            
            if score > 0:
                category_scores[category] = {
                    'score': score,
                    'matched_keywords': matched_keywords
                }
        
        if not category_scores:
            return {
                'category': 'operational',
                'subcategory': 'general',
                'classification_level': 'internal',
                'confidence': 0.2,
                'reasoning': ['No significant keywords detected'],
                'regulatory_requirements': []
            }
        
        # Get highest scoring category
        best_category = max(category_scores.keys(), key=lambda k: category_scores[k]['score'])
        best_score = category_scores[best_category]['score']
        
        # Determine classification level based on keyword importance
        classification_level = self._determine_classification_level(best_category, best_score)
        
        return {
            'category': best_category,
            'subcategory': self._determine_subcategory(best_category, category_scores[best_category]['matched_keywords']),
            'classification_level': classification_level,
            'confidence': min(0.8, best_score / 100),  # Normalize confidence
            'reasoning': [f'Keyword analysis: {", ".join(category_scores[best_category]["matched_keywords"][:3])}'],
            'regulatory_requirements': self._get_regulatory_requirements(best_category)
        }
    
    async def _nlp_based_classification(self, content: str) -> Dict[str, Any]:
        """Use NLP for advanced document classification"""
        
        if not self.nlp:
            return {'confidence': 0}
        
        # Process content with spaCy
        doc = self.nlp(content[:5000])  # Limit to first 5000 chars for performance
        
        # Extract named entities
        entities = {ent.label_: ent.text for ent in doc.ents}
        
        # Analyze sentence structure and context
        financial_indicators = 0
        hr_indicators = 0
        legal_indicators = 0
        
        for sent in doc.sents:
            sent_text = sent.text.lower()
            
            # Financial indicators
            if any(term in sent_text for term in ['revenue', 'profit', 'expenses', 'assets']):
                financial_indicators += 1
            
            # HR indicators
            if any(term in sent_text for term in ['employee', 'staff', 'personnel', 'human resources']):
                hr_indicators += 1
            
            # Legal indicators
            if any(term in sent_text for term in ['agreement', 'liability', 'compliance', 'regulation']):
                legal_indicators += 1
        
        # Determine category based on indicators
        max_indicators = max(financial_indicators, hr_indicators, legal_indicators)
        
        if max_indicators == 0:
            return {'confidence': 0.1}
        
        if financial_indicators == max_indicators:
            category = 'financial'
        elif hr_indicators == max_indicators:
            category = 'human_resources'
        else:
            category = 'compliance_legal'
        
        confidence = min(0.7, max_indicators / len(list(doc.sents)))
        
        return {
            'category': category,
            'subcategory': 'general',
            'classification_level': 'confidential',
            'confidence': confidence,
            'reasoning': [f'NLP analysis: {max_indicators} relevant sentences detected'],
            'regulatory_requirements': self._get_regulatory_requirements(category)
        }
    
    async def _pattern_based_classification(self, content: str, filename: str) -> Dict[str, Any]:
        """Classify based on regex patterns and file structure"""
        
        # Check filename patterns
        filename_lower = filename.lower()
        
        for pattern_name, pattern_info in self.regex_patterns.items():
            if pattern_info['pattern'].search(content) or any(fp.search(filename_lower) for fp in pattern_info.get('filename_patterns', [])):
                return {
                    'category': pattern_info['category'],
                    'subcategory': pattern_info['subcategory'],
                    'classification_level': pattern_info['classification_level'],
                    'confidence': pattern_info['confidence'],
                    'reasoning': [f'Pattern match: {pattern_name}'],
                    'regulatory_requirements': pattern_info.get('regulatory_requirements', [])
                }
        
        return {'confidence': 0}
    
    async def _combine_classification_results(self, 
                                            results: List[Dict[str, Any]], 
                                            metadata: Dict[str, Any] = None) -> ClassificationResult:
        """Combine multiple classification results into final classification"""
        
        # Filter out low-confidence results
        valid_results = [r for r in results if r.get('confidence', 0) > 0.1]
        
        if not valid_results:
            # Default classification
            return ClassificationResult(
                category='operational',
                subcategory='general',
                classification_level='internal',
                confidence=0.1,
                reasoning=['No confident classification found'],
                regulatory_requirements=[],
                special_handling={}
            )
        
        # Weight results by confidence
        weighted_categories = {}
        all_reasoning = []
        all_regulatory_requirements = set()
        
        for result in valid_results:
            category = result.get('category', 'operational')
            confidence = result.get('confidence', 0)
            
            if category not in weighted_categories:
                weighted_categories[category] = {
                    'total_weight': 0,
                    'subcategories': {},
                    'classification_levels': {},
                    'results': []
                }
            
            weighted_categories[category]['total_weight'] += confidence
            weighted_categories[category]['results'].append(result)
            
            # Collect subcategories and classification levels
            subcategory = result.get('subcategory', 'general')
            classification_level = result.get('classification_level', 'internal')
            
            weighted_categories[category]['subcategories'][subcategory] = weighted_categories[category]['subcategories'].get(subcategory, 0) + confidence
            weighted_categories[category]['classification_levels'][classification_level] = weighted_categories[category]['classification_levels'].get(classification_level, 0) + confidence
            
            # Collect reasoning and regulatory requirements
            all_reasoning.extend(result.get('reasoning', []))
            all_regulatory_requirements.update(result.get('regulatory_requirements', []))
        
        # Determine final category
        final_category = max(weighted_categories.keys(), key=lambda k: weighted_categories[k]['total_weight'])
        category_data = weighted_categories[final_category]
        
        # Determine final subcategory
        final_subcategory = max(category_data['subcategories'].keys(), key=lambda k: category_data['subcategories'][k])
        
        # Determine final classification level (take highest security level)
        classification_levels = category_data['classification_levels']
        level_hierarchy = ['public', 'internal', 'confidential', 'restricted', 'top_secret']
        final_classification_level = max(classification_levels.keys(), key=lambda k: level_hierarchy.index(k))
        
        # Calculate final confidence
        final_confidence = min(0.95, category_data['total_weight'] / len(valid_results))
        
        # Apply metadata overrides if available
        if metadata:
            if 'manual_classification' in metadata:
                final_classification_level = metadata['manual_classification']
                all_reasoning.append('Manual classification override applied')
                final_confidence = max(final_confidence, 0.9)
            
            if 'department_hint' in metadata:
                dept_hint = metadata['department_hint']
                if dept_hint == 'finance' and final_category != 'financial':
                    final_category = 'financial'
                    all_reasoning.append('Department hint applied')
        
        # Determine special handling requirements
        special_handling = self._determine_special_handling(
            final_category, 
            final_subcategory, 
            final_classification_level,
            list(all_regulatory_requirements)
        )
        
        return ClassificationResult(
            category=final_category,
            subcategory=final_subcategory,
            classification_level=final_classification_level,
            confidence=final_confidence,
            reasoning=list(set(all_reasoning)),
            regulatory_requirements=list(all_regulatory_requirements),
            special_handling=special_handling
        )
    
    def _load_classification_rules(self) -> Dict[str, Any]:
        """Load classification rules configuration"""
        return {
            'financial_keywords': ['revenue', 'profit', 'expenses', 'assets', 'liabilities', 'equity'],
            'hr_keywords': ['employee', 'personnel', 'payroll', 'benefits', 'performance'],
            'legal_keywords': ['contract', 'agreement', 'compliance', 'regulation', 'lawsuit'],
            'operational_keywords': ['inventory', 'production', 'manufacturing', 'supply chain'],
        }
    
    def _build_keyword_mappings(self) -> Dict[str, Dict[str, float]]:
        """Build keyword mappings with weights for each category"""
        return {
            'financial': {
                'revenue': 10, 'profit': 10, 'balance sheet': 15, 'income statement': 15,
                'cash flow': 15, 'financial report': 12, 'audit': 8, 'budget': 8,
                'expenses': 6, 'assets': 6, 'liabilities': 6, 'equity': 6,
                'sox': 12, 'gaap': 10, 'sec filing': 12
            },
            'human_resources': {
                'employee': 8, 'personnel': 8, 'payroll': 12, 'salary': 10,
                'performance review': 10, 'benefits': 8, 'hire': 6, 'termination': 8,
                'training': 6, 'hr policy': 8, 'gdpr': 10, 'personal data': 10
            },
            'compliance_legal': {
                'contract': 10, 'agreement': 10, 'compliance': 12, 'regulation': 10,
                'legal': 8, 'lawsuit': 8, 'liability': 8, 'terms and conditions': 8,
                'nda': 10, 'intellectual property': 12, 'patent': 10
            },
            'operational': {
                'inventory': 8, 'production': 8, 'manufacturing': 8, 'supply chain': 8,
                'procurement': 8, 'vendor': 6, 'quality': 6, 'logistics': 6,
                'warehouse': 6, 'shipping': 6
            }
        }
    
    def _compile_regex_patterns(self) -> Dict[str, Any]:
        """Compile regex patterns for document classification"""
        return {
            'ssn_pattern': {
                'pattern': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
                'category': 'human_resources',
                'subcategory': 'employee_records',
                'classification_level': 'restricted',
                'confidence': 0.9,
                'regulatory_requirements': ['GDPR', 'CCPA']
            },
            'financial_account': {
                'pattern': re.compile(r'\b\d{4}-\d{4}-\d{4}-\d{4}\b'),
                'category': 'financial',
                'subcategory': 'financial_statements',
                'classification_level': 'confidential',
                'confidence': 0.8
            },
            'ip_address': {
                'pattern': re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),
                'category': 'it_security',
                'subcategory': 'system_documentation',
                'classification_level': 'confidential',
                'confidence': 0.7
            },
            'contract_signature': {
                'pattern': re.compile(r'(signature|executed|agreement dated)', re.IGNORECASE),
                'filename_patterns': [re.compile(r'.*contract.*\.pdf$'), re.compile(r'.*agreement.*\.pdf$')],
                'category': 'compliance_legal',
                'subcategory': 'contracts',
                'classification_level': 'confidential',
                'confidence': 0.85
            }
        }
    
    def _determine_classification_level(self, category: str, keyword_score: float) -> str:
        """Determine classification level based on category and keyword score"""
        
        # Base classification levels by category
        base_levels = {
            'financial': 'confidential',
            'human_resources': 'confidential', 
            'compliance_legal': 'confidential',
            'operational': 'internal',
            'sales_marketing': 'internal',
            'it_security': 'confidential'
        }
        
        base_level = base_levels.get(category, 'internal')
        
        # Upgrade classification based on keyword score
        if keyword_score > 50:
            level_hierarchy = ['public', 'internal', 'confidential', 'restricted', 'top_secret']
            current_index = level_hierarchy.index(base_level)
            if current_index < len(level_hierarchy) - 1:
                return level_hierarchy[current_index + 1]
        
        return base_level
    
    def _determine_subcategory(self, category: str, matched_keywords: List[str]) -> str:
        """Determine subcategory based on matched keywords"""
        
        subcategory_keywords = {
            'financial': {
                'financial_statements': ['balance sheet', 'income statement', 'cash flow'],
                'audit_documents': ['audit', 'sox', 'compliance'],
                'management_reports': ['budget', 'variance', 'dashboard']
            },
            'human_resources': {
                'employee_records': ['employee', 'personnel', 'hire'],
                'payroll_documents': ['payroll', 'salary', 'wages'],
                'performance_management': ['performance', 'review', 'evaluation']
            },
            'compliance_legal': {
                'contracts': ['contract', 'agreement', 'terms'],
                'regulatory_compliance': ['compliance', 'regulation', 'filing'],
                'litigation': ['lawsuit', 'legal', 'court']
            }
        }
        
        if category in subcategory_keywords:
            for subcategory, keywords in subcategory_keywords[category].items():
                if any(keyword in ' '.join(matched_keywords) for keyword in keywords):
                    return subcategory
        
        return 'general'
    
    def _get_regulatory_requirements(self, category: str) -> List[str]:
        """Get regulatory requirements for category"""
        
        requirements = {
            'financial': ['SOX_404'],
            'human_resources': ['GDPR'],
            'compliance_legal': ['industry_specific'],
            'operational': [],
            'sales_marketing': ['GDPR', 'CCPA'],
            'it_security': ['SOC2', 'ISO27001']
        }
        
        return requirements.get(category, [])
    
    def _determine_special_handling(self, 
                                  category: str, 
                                  subcategory: str, 
                                  classification_level: str,
                                  regulatory_requirements: List[str]) -> Dict[str, Any]:
        """Determine special handling requirements"""
        
        special_handling = {}
        
        # Encryption requirements
        if classification_level in ['confidential', 'restricted', 'top_secret']:
            special_handling['encryption_required'] = True
        
        # Audit requirements
        if 'SOX_404' in regulatory_requirements:
            special_handling['audit_trail_required'] = True
            special_handling['immutable'] = True
        
        # Data subject rights (GDPR)
        if 'GDPR' in regulatory_requirements:
            special_handling['data_subject_rights'] = True
            special_handling['data_minimization'] = True
            special_handling['right_to_deletion'] = True
        
        # Time-based access controls
        if category == 'financial' and subcategory == 'audit_documents':
            special_handling['time_based_access'] = True
            special_handling['retention_period'] = 'permanent'
        
        # Multi-person approval
        if classification_level == 'restricted' or category == 'compliance_legal':
            special_handling['approval_required'] = True
            special_handling['min_approvers'] = 2
        
        return special_handling

# Global classification engine instance
document_classifier = DocumentClassificationEngine()
```

### 2. Classification API Integration

```python
# app/api/classification_routes.py
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from typing import Dict, Any, Optional
from ..auth.dependencies import get_current_user, require_permission
from ..services.document_classification import document_classifier, ClassificationResult
import aiofiles

router = APIRouter(prefix="/api/classification", tags=["Document Classification"])

@router.post("/classify-content")
@require_permission("classify:documents")
async def classify_document_content(
    content: str = Form(...),
    filename: str = Form(""),
    metadata: Optional[Dict[str, Any]] = Form(None),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Classify document based on content"""
    
    try:
        result = await document_classifier.classify_document(
            content=content,
            filename=filename,
            metadata=metadata
        )
        
        return {
            "classification": {
                "category": result.category,
                "subcategory": result.subcategory,
                "classification_level": result.classification_level,
                "confidence": result.confidence,
                "reasoning": result.reasoning,
                "regulatory_requirements": result.regulatory_requirements,
                "special_handling": result.special_handling
            },
            "classified_by": current_user["user_id"],
            "classification_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")

@router.post("/classify-file")
@require_permission("classify:documents")
async def classify_uploaded_file(
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Classify uploaded file"""
    
    if file.size > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=413, detail="File too large")
    
    try:
        # Read file content
        content = await file.read()
        text_content = content.decode('utf-8', errors='ignore')
        
        # Parse metadata if provided
        metadata_dict = None
        if metadata:
            import json
            metadata_dict = json.loads(metadata)
        
        # Classify document
        result = await document_classifier.classify_document(
            content=text_content,
            filename=file.filename,
            metadata=metadata_dict
        )
        
        return {
            "filename": file.filename,
            "file_size": file.size,
            "classification": {
                "category": result.category,
                "subcategory": result.subcategory,
                "classification_level": result.classification_level,
                "confidence": result.confidence,
                "reasoning": result.reasoning,
                "regulatory_requirements": result.regulatory_requirements,
                "special_handling": result.special_handling
            },
            "classified_by": current_user["user_id"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File classification failed: {str(e)}")

@router.get("/categories")
async def get_document_categories():
    """Get available document categories and subcategories"""
    
    return {
        "categories": ERP_DOCUMENT_CATEGORIES,
        "classification_levels": CLASSIFICATION_LEVELS
    }

@router.post("/bulk-classify")
@require_permission("classify:bulk_documents")
async def bulk_classify_documents(
    documents: List[Dict[str, Any]],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Bulk classify multiple documents"""
    
    if len(documents) > 100:
        raise HTTPException(status_code=413, detail="Too many documents (max 100)")
    
    results = []
    
    for i, doc in enumerate(documents):
        try:
            result = await document_classifier.classify_document(
                content=doc.get('content', ''),
                filename=doc.get('filename', f'document_{i}'),
                metadata=doc.get('metadata')
            )
            
            results.append({
                "document_index": i,
                "filename": doc.get('filename'),
                "classification": {
                    "category": result.category,
                    "subcategory": result.subcategory,
                    "classification_level": result.classification_level,
                    "confidence": result.confidence,
                    "regulatory_requirements": result.regulatory_requirements
                },
                "status": "success"
            })
            
        except Exception as e:
            results.append({
                "document_index": i,
                "filename": doc.get('filename'),
                "status": "error",
                "error": str(e)
            })
    
    return {
        "total_documents": len(documents),
        "successful_classifications": len([r for r in results if r["status"] == "success"]),
        "failed_classifications": len([r for r in results if r["status"] == "error"]),
        "results": results,
        "classified_by": current_user["user_id"]
    }
```

## Compliance and Regulatory Mappings

### 3. Regulatory Compliance Framework

```python
# Regulatory Requirements Mapping
REGULATORY_COMPLIANCE_MAPPING = {
    "SOX_404": {
        "full_name": "Sarbanes-Oxley Act Section 404",
        "description": "Internal controls over financial reporting",
        "applicable_categories": ["financial"],
        "applicable_subcategories": ["financial_statements", "audit_documents"],
        "requirements": {
            "immutable_records": True,
            "audit_trail": True,
            "access_logging": True,
            "segregation_of_duties": True,
            "management_certification": True
        },
        "retention_period": "7_years_minimum",
        "geographic_scope": ["US", "US_subsidiaries"]
    },
    
    "GDPR": {
        "full_name": "General Data Protection Regulation",
        "description": "EU data protection and privacy regulation",
        "applicable_categories": ["human_resources", "sales_marketing"],
        "data_types": ["personal_data", "sensitive_personal_data"],
        "requirements": {
            "data_minimization": True,
            "purpose_limitation": True,
            "storage_limitation": True,
            "data_subject_rights": True,
            "privacy_by_design": True,
            "breach_notification": True
        },
        "data_subject_rights": [
            "right_of_access",
            "right_to_rectification", 
            "right_to_erasure",
            "right_to_portability",
            "right_to_object"
        ],
        "geographic_scope": ["EU", "EEA", "global_eu_citizens"]
    },
    
    "CCPA": {
        "full_name": "California Consumer Privacy Act",
        "description": "California privacy law for consumer data",
        "applicable_categories": ["sales_marketing", "human_resources"],
        "requirements": {
            "disclosure_requirements": True,
            "opt_out_rights": True,
            "data_deletion_rights": True,
            "non_discrimination": True
        },
        "geographic_scope": ["California", "California_consumers"]
    },
    
    "HIPAA": {
        "full_name": "Health Insurance Portability and Accountability Act",
        "description": "Healthcare data privacy and security",
        "applicable_categories": ["human_resources"],
        "applicable_subcategories": ["benefits_administration"],
        "data_types": ["protected_health_information"],
        "requirements": {
            "administrative_safeguards": True,
            "physical_safeguards": True,
            "technical_safeguards": True,
            "breach_notification": True
        },
        "geographic_scope": ["US"]
    }
}

# Industry-Specific Classifications
INDUSTRY_CLASSIFICATIONS = {
    "financial_services": {
        "additional_regulations": ["SEC", "FINRA", "BASEL_III"],
        "enhanced_classifications": {
            "trading_data": "restricted",
            "customer_financial_data": "restricted",
            "regulatory_reports": "confidential"
        }
    },
    
    "healthcare": {
        "additional_regulations": ["HIPAA", "FDA"],
        "enhanced_classifications": {
            "patient_data": "restricted",
            "clinical_trial_data": "confidential",
            "medical_device_documentation": "confidential"
        }
    },
    
    "manufacturing": {
        "additional_regulations": ["FDA", "EPA", "OSHA"],
        "enhanced_classifications": {
            "safety_data_sheets": "internal",
            "environmental_reports": "confidential",
            "product_specifications": "confidential"
        }
    }
}
```

## Integration with Vector Database

### 4. Classified Document Indexing

```python
# app/services/classified_document_indexer.py
from typing import Dict, List, Any
from ..services.document_classification import document_classifier, ClassificationResult
from ..vector.vector_service import VectorDatabaseService

class ClassifiedDocumentIndexer:
    """Index documents with classification metadata in vector database"""
    
    def __init__(self, vector_db_service: VectorDatabaseService):
        self.vector_db = vector_db_service
    
    async def index_classified_document(self,
                                      document_id: str,
                                      content: str,
                                      filename: str,
                                      user_context: Dict[str, Any],
                                      manual_classification: Dict[str, Any] = None) -> Dict[str, Any]:
        """Index document with automatic classification"""
        
        # Classify document
        if manual_classification:
            classification = ClassificationResult(**manual_classification)
        else:
            classification = await document_classifier.classify_document(
                content=content,
                filename=filename,
                metadata={'user_context': user_context}
            )
        
        # Build metadata for vector database
        vector_metadata = {
            'document_id': document_id,
            'filename': filename,
            'category': classification.category,
            'subcategory': classification.subcategory,
            'classification_level': classification.classification_level,
            'classification_confidence': classification.confidence,
            'regulatory_requirements': classification.regulatory_requirements,
            'special_handling': classification.special_handling,
            'classified_by': user_context.get('user_id'),
            'classification_timestamp': datetime.utcnow().isoformat(),
            
            # Access control metadata
            'required_clearance_level': CLASSIFICATION_LEVELS[classification.classification_level]['level'],
            'encryption_required': classification.special_handling.get('encryption_required', False),
            'audit_required': classification.special_handling.get('audit_trail_required', False),
            
            # Compliance metadata
            'gdpr_applicable': 'GDPR' in classification.regulatory_requirements,
            'sox_controlled': 'SOX_404' in classification.regulatory_requirements,
            'data_subject_rights': classification.special_handling.get('data_subject_rights', False)
        }
        
        # Chunk document based on classification
        chunks = await self._intelligent_chunking(content, classification)
        
        # Index chunks with classification metadata
        indexing_results = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = vector_metadata.copy()
            chunk_metadata.update({
                'chunk_index': i,
                'chunk_size': len(chunk),
                'total_chunks': len(chunks)
            })
            
            result = await self.vector_db.add_document_chunk(
                chunk_id=f"{document_id}_chunk_{i}",
                content=chunk,
                metadata=chunk_metadata
            )
            
            indexing_results.append(result)
        
        return {
            'document_id': document_id,
            'classification': {
                'category': classification.category,
                'subcategory': classification.subcategory,
                'classification_level': classification.classification_level,
                'confidence': classification.confidence
            },
            'chunks_indexed': len(chunks),
            'indexing_results': indexing_results,
            'metadata': vector_metadata
        }
    
    async def _intelligent_chunking(self, content: str, classification: ClassificationResult) -> List[str]:
        """Intelligent document chunking based on classification"""
        
        # Different chunking strategies based on document type
        if classification.category == 'financial' and 'statements' in classification.subcategory:
            # Financial statements - preserve table structure
            return await self._financial_statement_chunking(content)
        
        elif classification.category == 'compliance_legal':
            # Legal documents - preserve section structure
            return await self._legal_document_chunking(content)
        
        elif classification.category == 'human_resources':
            # HR documents - privacy-aware chunking
            return await self._privacy_aware_chunking(content)
        
        else:
            # Standard semantic chunking
            return await self._semantic_chunking(content)
    
    async def _financial_statement_chunking(self, content: str) -> List[str]:
        """Chunk financial statements preserving structure"""
        # Implementation for financial statement specific chunking
        # Preserve table structures, financial line items, etc.
        return self._standard_chunking(content, chunk_size=800)
    
    async def _legal_document_chunking(self, content: str) -> List[str]:
        """Chunk legal documents preserving clause structure"""
        # Implementation for legal document chunking
        # Preserve clauses, sections, definitions, etc.
        return self._standard_chunking(content, chunk_size=1000)
    
    async def _privacy_aware_chunking(self, content: str) -> List[str]:
        """Chunk HR documents with privacy considerations"""
        # Implementation for HR document chunking
        # Ensure PII is not split across chunks
        return self._standard_chunking(content, chunk_size=600)
    
    async def _semantic_chunking(self, content: str) -> List[str]:
        """Standard semantic chunking"""
        return self._standard_chunking(content, chunk_size=500)
    
    def _standard_chunking(self, content: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Standard text chunking with overlap"""
        chunks = []
        words = content.split()
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk = ' '.join(chunk_words)
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks

# Global classified document indexer
classified_indexer = ClassifiedDocumentIndexer(vector_db_service)
```

This comprehensive document classification system provides automated, intelligent classification of ERP documents with proper compliance handling and integration with the RBAC-RAG architecture. The next document will cover practical RAG use cases for ERP systems.