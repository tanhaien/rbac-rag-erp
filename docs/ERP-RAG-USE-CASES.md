# ERP RAG Use Cases and Implementation Scenarios

## Overview

This document provides comprehensive, real-world use cases for ERP RBAC-RAG systems across different business functions. Each use case includes practical queries, expected responses, authorization requirements, and implementation examples.

## Financial Use Cases

### 1. Executive Financial Reporting

**Scenario**: CFO needs quarterly financial analysis for board presentation

**User Profile**:
- Role: CFO
- Clearance Level: Executive (5)
- Departments: Finance, All (executive override)
- Regulatory Access: SOX-controlled documents

**Query Examples**:

```python
# Query 1: Quarterly Revenue Analysis
query_1 = {
    "text": "Show me Q3 2024 revenue breakdown by department and compare with Q2 2024. Highlight any significant variances.",
    "intent": "financial_analysis",
    "parameters": {
        "time_period": "Q3_2024",
        "comparison_period": "Q2_2024",
        "breakdown": "department",
        "variance_threshold": 0.05
    }
}

# Expected Response
response_1 = {
    "summary": "Q3 2024 revenue totaled $125.3M, up 8.2% from Q2 2024 ($115.8M). Key drivers: Engineering (+$12.5M, +15.3%), Sales (+$8.2M, +12.1%). Marketing showed decline (-$2.1M, -8.5%) due to campaign restructuring.",
    
    "detailed_breakdown": {
        "engineering": {
            "q3_2024": 94500000,
            "q2_2024": 82000000,
            "variance": 0.153,
            "variance_reason": "New product launches and expanded client base"
        },
        "sales": {
            "q3_2024": 76300000,
            "q2_2024": 68100000,
            "variance": 0.121,
            "variance_reason": "Strong B2B sales performance and new market penetration"
        },
        "marketing": {
            "q3_2024": 22100000,
            "q2_2024": 24200000,
            "variance": -0.085,
            "variance_reason": "Strategic campaign restructuring and budget reallocation"
        }
    },
    
    "sources": [
        {"document": "Q3_2024_Financial_Statements", "classification": "confidential"},
        {"document": "Departmental_Budget_Reports_Q3", "classification": "internal"},
        {"document": "Revenue_Recognition_Analysis", "classification": "confidential"}
    ],
    
    "compliance_notes": "All data sourced from SOX-compliant financial systems. Revenue recognition follows GAAP standards.",
    
    "recommendations": [
        "Investigate marketing variance - may impact Q4 projections",
        "Engineering growth trajectory suggests capacity planning review needed",
        "Sales performance indicates opportunity for increased investment"
    ]
}
```

```python
# Query 2: Cash Flow Analysis
query_2 = {
    "text": "What's our current cash position and projected cash flow for the next 6 months? Include any liquidity risks.",
    "intent": "cash_flow_analysis",
    "parameters": {
        "projection_period": "6_months",
        "include_scenarios": ["best_case", "worst_case", "most_likely"]
    }
}

# Expected Response
response_2 = {
    "current_cash_position": {
        "cash_and_equivalents": 45600000,
        "available_credit_lines": 25000000,
        "total_liquidity": 70600000,
        "as_of_date": "2024-10-31"
    },
    
    "six_month_projection": {
        "most_likely_scenario": {
            "months": [
                {"month": "Nov_2024", "ending_cash": 48200000, "net_cash_flow": 2600000},
                {"month": "Dec_2024", "ending_cash": 52100000, "net_cash_flow": 3900000},
                {"month": "Jan_2025", "ending_cash": 49800000, "net_cash_flow": -2300000},
                {"month": "Feb_2025", "ending_cash": 51500000, "net_cash_flow": 1700000},
                {"month": "Mar_2025", "ending_cash": 54200000, "net_cash_flow": 2700000},
                {"month": "Apr_2025", "ending_cash": 56800000, "net_cash_flow": 2600000}
            ]
        }
    },
    
    "liquidity_risks": [
        {
            "risk": "Q4 bonus payments",
            "impact": -8500000,
            "timing": "December 2024",
            "mitigation": "Staggered payment schedule available"
        },
        {
            "risk": "Capital expenditure commitments", 
            "impact": -12000000,
            "timing": "Q1 2025",
            "mitigation": "Can defer 30% if needed"
        }
    ],
    
    "key_assumptions": [
        "Revenue collection maintains 95% efficiency",
        "No significant one-time expenses beyond planned capex",
        "Credit facilities remain available at current terms"
    ]
}
```

### 2. Department Manager Budget Monitoring

**Scenario**: Engineering Manager tracking departmental budget performance

**User Profile**:
- Role: Engineering Manager
- Clearance Level: Management (3)
- Departments: Engineering
- Budget Authority: $2M

**Query Examples**:

```python
# Query: Budget Variance Analysis
query_dept_budget = {
    "text": "How is my engineering department performing against budget this quarter? Show detailed breakdown by cost categories.",
    "intent": "budget_monitoring",
    "parameters": {
        "department": "engineering",
        "time_period": "Q3_2024",
        "breakdown": "cost_category"
    }
}

# Expected Response (filtered by department access)
response_dept_budget = {
    "department": "Engineering",
    "period": "Q3 2024",
    "budget_performance": {
        "total_budget": 2000000,
        "actual_spend": 1850000,
        "variance": -150000,
        "variance_percentage": -0.075,
        "status": "under_budget"
    },
    
    "cost_breakdown": {
        "salaries_benefits": {
            "budget": 1400000,
            "actual": 1380000,
            "variance": -20000,
            "note": "Two open positions unfilled"
        },
        "contractor_services": {
            "budget": 300000,
            "actual": 285000,
            "variance": -15000,
            "note": "Reduced contractor usage due to internal capacity"
        },
        "software_licenses": {
            "budget": 180000,
            "actual": 165000,
            "variance": -15000,
            "note": "Volume discounts achieved"
        },
        "equipment_supplies": {
            "budget": 120000,
            "actual": 95000,
            "variance": -25000,
            "note": "Deferred laptop refresh to Q4"
        }
    },
    
    "recommendations": [
        "Consider accelerating hiring for open positions",
        "Laptop refresh budget should be confirmed for Q4",
        "Strong performance may support additional Q4 initiatives"
    ],
    
    "access_note": "Data filtered to show only Engineering department information based on your authorization level."
}
```

## HR Use Cases

### 3. HR Analytics and Reporting

**Scenario**: HR Manager analyzing employee metrics and performance trends

**User Profile**:
- Role: HR Manager
- Clearance Level: HR Management (4)
- Departments: Human Resources, All Employee Data
- GDPR Compliance: Certified

**Query Examples**:

```python
# Query: Employee Turnover Analysis
query_hr_turnover = {
    "text": "What are our employee turnover rates by department for the past 12 months? Include reasons for departure and impact on business continuity.",
    "intent": "hr_analytics",
    "parameters": {
        "time_period": "12_months",
        "breakdown": "department",
        "include_reasons": True,
        "include_impact_analysis": True
    }
}

# Expected Response (with GDPR compliance)
response_hr_turnover = {
    "analysis_period": "Nov 2023 - Oct 2024",
    "overall_turnover": {
        "total_separations": 47,
        "average_headcount": 342,
        "turnover_rate": 0.137,
        "industry_benchmark": 0.145,
        "status": "below_benchmark"
    },
    
    "department_breakdown": {
        "engineering": {
            "separations": 18,
            "headcount": 120,
            "turnover_rate": 0.15,
            "top_reasons": ["better_compensation", "career_growth", "remote_work_flexibility"],
            "business_impact": "2 critical projects delayed by avg 3 weeks"
        },
        "sales": {
            "separations": 15,
            "headcount": 85,
            "turnover_rate": 0.176,
            "top_reasons": ["quota_attainment", "territory_changes", "management_changes"],
            "business_impact": "Q2 revenue shortfall of $1.2M attributed to ramp time"
        },
        "marketing": {
            "separations": 8,
            "headcount": 42,
            "turnover_rate": 0.19,
            "top_reasons": ["budget_cuts", "role_elimination", "strategic_changes"],
            "business_impact": "Campaign execution delays, 2 product launches postponed"
        }
    },
    
    "predictive_insights": {
        "at_risk_employees": 23,
        "flight_risk_factors": ["compensation_below_market", "no_promotion_2_years", "manager_change"],
        "retention_recommendations": [
            "Conduct compensation review for engineering roles",
            "Implement structured career development program",
            "Review management training effectiveness in sales"
        ]
    },
    
    "gdpr_compliance": {
        "data_processed": "aggregate_anonymized_data",
        "individual_identification": "not_possible",
        "processing_basis": "legitimate_business_interest",
        "retention_period": "5_years"
    }
}
```

```python
# Query: Performance Management Insights
query_performance = {
    "text": "Show me performance review trends and identify high performers who might be ready for promotion. Include diversity metrics.",
    "intent": "performance_analysis",
    "parameters": {
        "include_diversity": True,
        "promotion_ready_threshold": 4.5,
        "review_period": "latest_cycle"
    }
}

# Expected Response
response_performance = {
    "review_cycle": "2024_Annual_Reviews",
    "participation_rate": 0.98,
    
    "performance_distribution": {
        "exceptional": {"count": 42, "percentage": 0.12},
        "exceeds_expectations": {"count": 103, "percentage": 0.30},
        "meets_expectations": {"count": 165, "percentage": 0.48},
        "needs_improvement": {"count": 25, "percentage": 0.07},
        "unsatisfactory": {"count": 7, "percentage": 0.02}
    },
    
    "promotion_ready_candidates": {
        "total_eligible": 38,
        "by_department": {
            "engineering": 15,
            "sales": 12,
            "marketing": 6,
            "operations": 5
        },
        "diversity_breakdown": {
            "gender": {"female": 16, "male": 22},
            "ethnicity": {"underrepresented_minorities": 14, "others": 24},
            "tenure": {"2-5_years": 28, "5+_years": 10}
        }
    },
    
    "development_priorities": [
        "Leadership training program needed for 15 senior individual contributors",
        "Technical skills development in AI/ML for engineering team",
        "Cross-functional exposure for high-potential sales candidates"
    ],
    
    "privacy_note": "Individual performance data anonymized. Aggregate statistics only provided to ensure employee privacy."
}
```

### 4. Employee Self-Service Queries

**Scenario**: Employee accessing their own HR information

**User Profile**:
- Role: Senior Software Engineer
- Clearance Level: Employee (2)
- Employee ID: EMP12345
- Self-Access: Enabled

**Query Examples**:

```python
# Query: Personal Benefits Information
query_benefits = {
    "text": "What are my current benefits and how much vacation time do I have remaining?",
    "intent": "self_service_hr",
    "employee_id": "EMP12345"
}

# Expected Response (self-access only)
response_benefits = {
    "employee_id": "EMP12345",
    "access_type": "self_service",
    
    "benefits_summary": {
        "health_insurance": {
            "plan": "Premier PPO",
            "coverage": "Employee + Family",
            "monthly_premium": 450.00,
            "employee_contribution": 135.00,
            "deductible_remaining": 1200.00
        },
        "retirement": {
            "401k_contribution": "8%",
            "company_match": "4%",
            "vested_percentage": 100,
            "current_balance": 85600.00
        },
        "stock_options": {
            "total_granted": 5000,
            "vested": 3000,
            "unvested": 2000,
            "next_vesting_date": "2025-01-01"
        }
    },
    
    "time_off_balances": {
        "vacation_days": {
            "accrued": 25,
            "used": 18,
            "remaining": 7,
            "carryover_limit": 5
        },
        "sick_days": {
            "accrued": 12,
            "used": 3,
            "remaining": 9
        },
        "personal_days": {
            "accrued": 3,
            "used": 1,
            "remaining": 2
        }
    },
    
    "recent_activity": [
        {"date": "2024-10-15", "action": "vacation_request_approved", "days": 3},
        {"date": "2024-09-30", "action": "benefits_enrollment_updated", "change": "added_dental"},
        {"date": "2024-09-01", "action": "401k_contribution_increased", "new_rate": "8%"}
    ],
    
    "available_actions": [
        "Request time off",
        "Update benefits enrollment",
        "View pay statements",
        "Update emergency contacts"
    ]
}
```

## Operational Use Cases

### 5. Supply Chain Management

**Scenario**: Operations Manager monitoring supply chain performance

**User Profile**:
- Role: Operations Manager
- Clearance Level: Management (3)
- Departments: Operations, Manufacturing
- Locations: Plant_A, Plant_B, Warehouse_Central

**Query Examples**:

```python
# Query: Inventory Status and Risks
query_inventory = {
    "text": "What's our current inventory status for critical components? Highlight any supply chain risks or potential stockouts.",
    "intent": "supply_chain_monitoring",
    "parameters": {
        "focus": "critical_components",
        "include_risks": True,
        "locations": ["Plant_A", "Plant_B", "Warehouse_Central"]
    }
}

# Expected Response
response_inventory = {
    "analysis_date": "2024-10-31",
    "locations_analyzed": ["Plant_A", "Plant_B", "Warehouse_Central"],
    
    "inventory_summary": {
        "total_sku_count": 1245,
        "critical_components": 89,
        "stockout_risk_items": 12,
        "overstock_items": 23,
        "optimal_stock_items": 54
    },
    
    "critical_components_status": [
        {
            "component": "Semiconductor_Chip_XR400",
            "current_stock": 850,
            "safety_stock": 1200,
            "status": "below_safety",
            "days_supply": 18,
            "risk_level": "high",
            "supplier": "TechSupplier_Asia",
            "lead_time_days": 45,
            "recommended_action": "Expedite emergency order"
        },
        {
            "component": "Steel_Alloy_SA235",
            "current_stock": 2500,
            "safety_stock": 1800,
            "status": "adequate",
            "days_supply": 32,
            "risk_level": "medium",
            "supplier": "MetalCorp_USA",
            "lead_time_days": 21,
            "recommended_action": "Monitor weekly"
        }
    ],
    
    "supply_chain_risks": [
        {
            "risk_type": "supplier_concentration",
            "description": "65% of critical components from single region (Asia)",
            "impact": "high",
            "mitigation": "Accelerate supplier diversification program"
        },
        {
            "risk_type": "transportation_delays",
            "description": "Port congestion affecting 3 key suppliers",
            "impact": "medium",
            "mitigation": "Consider air freight for critical items"
        }
    ],
    
    "recommended_actions": [
        "Place emergency orders for 5 critical components",
        "Review and update safety stock levels based on new lead times",
        "Accelerate supplier audit for alternative sources"
    ],
    
    "location_access_note": "Data shown only for authorized locations: Plant_A, Plant_B, Warehouse_Central"
}
```

### 6. Quality Management

**Scenario**: Quality Manager investigating quality issues and trends

**User Profile**:
- Role: Quality Manager  
- Clearance Level: Management (3)
- Departments: Quality, Manufacturing
- Certifications: ISO_9001, FDA_Compliance

**Query Examples**:

```python
# Query: Quality Metrics and Issues
query_quality = {
    "text": "Show me quality metrics for the past quarter and identify any concerning trends. Include customer complaints and corrective actions.",
    "intent": "quality_analysis",
    "parameters": {
        "time_period": "Q3_2024",
        "include_customer_feedback": True,
        "include_corrective_actions": True
    }
}

# Expected Response
response_quality = {
    "reporting_period": "Q3 2024 (Jul-Sep)",
    "certification_status": "ISO_9001_current, FDA_compliant",
    
    "quality_metrics": {
        "overall_quality_score": 94.2,
        "defect_rate": 0.0034,
        "first_pass_yield": 0.967,
        "customer_satisfaction": 4.6,
        "on_time_delivery": 0.943
    },
    
    "trend_analysis": {
        "defect_rate_trend": {
            "direction": "improving",
            "change": -0.0008,
            "vs_previous_quarter": "15% improvement"
        },
        "concerning_trends": [
            {
                "metric": "supplier_quality_variance",
                "trend": "increasing",
                "impact": "3 suppliers showing declining performance",
                "action_required": "Supplier audit and corrective action plans"
            }
        ]
    },
    
    "customer_complaints": {
        "total_complaints": 23,
        "complaint_rate": 0.0012,
        "category_breakdown": {
            "product_defects": 12,
            "delivery_issues": 7,
            "documentation_errors": 4
        },
        "resolved_complaints": 19,
        "avg_resolution_time": "4.2_days"
    },
    
    "active_corrective_actions": [
        {
            "ca_number": "CA-2024-045",
            "issue": "Inconsistent coating thickness Product Line B",
            "root_cause": "Calibration drift in application equipment",
            "actions": ["Equipment recalibration", "Enhanced monitoring protocol"],
            "due_date": "2024-11-15",
            "status": "in_progress"
        },
        {
            "ca_number": "CA-2024-038", 
            "issue": "Supplier material variance Batch SR-334",
            "root_cause": "Supplier process change not communicated",
            "actions": ["Supplier audit", "Enhanced incoming inspection"],
            "due_date": "2024-10-31",
            "status": "verification_pending"
        }
    ],
    
    "regulatory_compliance": {
        "fda_inspections": 0,
        "iso_audit_status": "passed_with_minor_observations",
        "compliance_training_current": 0.98
    },
    
    "recommendations": [
        "Focus on supplier quality improvement program",
        "Implement predictive maintenance for coating equipment",
        "Enhance customer communication for delivery expectations"
    ]
}
```

## Executive Dashboard Use Cases

### 7. CEO Strategic Overview

**Scenario**: CEO requesting comprehensive business performance overview

**User Profile**:
- Role: CEO
- Clearance Level: Executive (5)
- Departments: All (executive override)
- Strategic Access: Board materials, M&A data

**Query Examples**:

```python
# Query: Strategic Business Overview
query_executive = {
    "text": "Give me a comprehensive overview of our business performance this quarter across all key metrics - financial, operational, and strategic initiatives.",
    "intent": "executive_dashboard",
    "parameters": {
        "comprehensive": True,
        "all_departments": True,
        "strategic_initiatives": True,
        "competitive_context": True
    }
}

# Expected Response
response_executive = {
    "executive_summary": {
        "period": "Q3 2024",
        "overall_performance": "strong",
        "key_highlights": [
            "Revenue up 12% YoY, exceeding guidance by 3%",
            "Successfully launched AI product suite - early traction positive",
            "Completed acquisition of DataTech Solutions",
            "Market share increased to 23% in core segment"
        ],
        "key_concerns": [
            "Rising customer acquisition costs in competitive market",
            "Talent retention challenges in engineering (15% turnover)",
            "Supply chain disruptions impacting 2 product lines"
        ]
    },
    
    "financial_performance": {
        "revenue": {
            "q3_2024": 125300000,
            "yoy_growth": 0.12,
            "vs_guidance": 0.03,
            "guidance_range": "120-122M"
        },
        "profitability": {
            "gross_margin": 0.642,
            "operating_margin": 0.186,
            "net_margin": 0.142,
            "trend": "stable_improving"
        },
        "cash_position": {
            "cash_equivalents": 45600000,
            "free_cash_flow": 18200000,
            "runway_months": 18,
            "debt_to_equity": 0.23
        }
    },
    
    "operational_performance": {
        "customer_metrics": {
            "new_customers": 347,
            "customer_retention": 0.94,
            "nps_score": 67,
            "churn_rate": 0.06
        },
        "product_development": {
            "ai_product_adoption": 0.34,
            "feature_release_velocity": "2.3_per_month",
            "customer_satisfaction": 4.6,
            "r&d_investment": 0.15
        },
        "operational_efficiency": {
            "employee_productivity": "up_8%",
            "process_automation": 0.67,
            "quality_metrics": 94.2,
            "on_time_delivery": 0.943
        }
    },
    
    "strategic_initiatives": [
        {
            "initiative": "AI Product Suite Launch",
            "status": "completed",
            "results": "34% adoption rate, $8.2M ARR in first quarter",
            "next_phase": "International expansion Q4 2024"
        },
        {
            "initiative": "DataTech Solutions Acquisition",
            "status": "integration_underway",
            "progress": "75% systems integrated, talent retention 90%",
            "expected_synergies": "$12M annually by end of 2025"
        },
        {
            "initiative": "European Market Expansion",
            "status": "planning",
            "timeline": "Launch Q1 2025",
            "investment_required": "$25M",
            "projected_roi": "2.4x over 3 years"
        }
    ],
    
    "competitive_landscape": {
        "market_position": "2nd_largest_player",
        "market_share": 0.23,
        "key_differentiators": ["AI capabilities", "customer_service", "enterprise_focus"],
        "competitive_threats": [
            "New entrant with significant VC backing",
            "Price pressure from established competitor"
        ]
    },
    
    "risk_assessment": {
        "high_risks": [
            "Key customer concentration (30% revenue from top 5)",
            "Regulatory changes in core market",
            "Cybersecurity threats to critical infrastructure"
        ],
        "medium_risks": [
            "Talent retention in competitive market",
            "Supply chain cost inflation",
            "Economic downturn impact on discretionary spending"
        ],
        "mitigation_status": "active_monitoring_all_risks"
    },
    
    "board_readiness": {
        "materials_prepared": True,
        "compliance_status": "all_current",
        "audit_status": "no_material_issues",
        "strategic_decisions_required": [
            "European expansion investment approval",
            "R&D budget increase for AI initiative",
            "Acquisition pipeline review"
        ]
    }
}
```

## Compliance and Audit Use Cases

### 8. Internal Audit Investigation

**Scenario**: Internal Auditor conducting SOX compliance review

**User Profile**:
- Role: Internal Auditor
- Clearance Level: Audit (4)
- Departments: All (audit access)
- Certifications: SOX_404, CPA, CISA

**Query Examples**:

```python
# Query: SOX Compliance Review
query_sox_audit = {
    "text": "Perform a SOX 404 compliance review for Q3 2024. Show all financial reporting controls, any deficiencies, and management remediation actions.",
    "intent": "sox_compliance_audit",
    "parameters": {
        "period": "Q3_2024",
        "control_scope": "financial_reporting",
        "include_deficiencies": True,
        "remediation_status": True
    }
}

# Expected Response
response_sox_audit = {
    "audit_period": "Q3 2024",
    "audit_scope": "SOX 404 - Internal Controls over Financial Reporting",
    "auditor": "Internal Audit Team",
    "compliance_status": "effective_with_deficiencies",
    
    "controls_tested": {
        "total_controls": 124,
        "controls_tested": 124,
        "effective_controls": 119,
        "deficient_controls": 5,
        "effectiveness_rate": 0.96
    },
    
    "control_categories": {
        "entity_level_controls": {
            "tested": 18,
            "effective": 18,
            "deficient": 0,
            "status": "effective"
        },
        "transaction_level_controls": {
            "tested": 67,
            "effective": 64,
            "deficient": 3,
            "status": "effective_with_deficiencies"
        },
        "it_general_controls": {
            "tested": 23,
            "effective": 22,
            "deficient": 1,
            "status": "effective_with_minor_deficiency"
        },
        "closing_controls": {
            "tested": 16,
            "effective": 15,
            "deficient": 1,
            "status": "effective_with_minor_deficiency"
        }
    },
    
    "identified_deficiencies": [
        {
            "deficiency_id": "DEF-2024-003",
            "severity": "significant_deficiency",
            "control_area": "revenue_recognition",
            "description": "Manual review control for complex revenue contracts not consistently documented",
            "root_cause": "Inadequate training on new revenue recognition procedures",
            "potential_impact": "Material misstatement in revenue recognition",
            "management_response": "Enhanced training program implemented, additional review layer added",
            "remediation_timeline": "Completed 10/15/2024",
            "status": "remediated"
        },
        {
            "deficiency_id": "DEF-2024-007",
            "severity": "deficiency",
            "control_area": "accounts_payable", 
            "description": "Three-way match control bypassed in 4 instances without proper authorization",
            "root_cause": "System workflow allowed override without secondary approval",
            "potential_impact": "Unauthorized payments or duplicate payments",
            "management_response": "System configuration updated, workflow redesigned",
            "remediation_timeline": "In progress - due 11/30/2024",
            "status": "in_remediation"
        }
    ],
    
    "management_assessment": {
        "ceo_certification": "pending_quarter_end_close",
        "cfo_certification": "pending_quarter_end_close",
        "disclosure_controls": "effective",
        "material_changes": "Implementation of new revenue recognition system",
        "quarterly_assessment": "No material weaknesses identified"
    },
    
    "recommendations": [
        "Strengthen documentation requirements for manual controls",
        "Implement quarterly control self-assessment process",
        "Enhance IT access controls monitoring",
        "Consider automation opportunities for high-risk manual processes"
    ],
    
    "regulatory_implications": {
        "sec_filing_impact": "Management assessment of ICFR effectiveness",
        "external_auditor_coordination": "Deficiencies communicated to external auditors",
        "disclosure_requirements": "Significant deficiency disclosed in 10-Q filing"
    }
}
```

## Advanced Analytics Use Cases

### 9. Predictive Analytics and Forecasting

**Scenario**: Business Analyst building predictive models for revenue forecasting

**User Profile**:
- Role: Senior Business Analyst
- Clearance Level: Analyst (3)
- Departments: Finance, Sales, Marketing
- Analytics Access: Predictive modeling tools

**Query Examples**:

```python
# Query: Revenue Forecasting Model
query_forecasting = {
    "text": "Build a revenue forecast model for next quarter using historical data, current pipeline, and market indicators. Include scenario analysis.",
    "intent": "predictive_analytics",
    "parameters": {
        "forecast_period": "Q4_2024",
        "model_type": "ensemble",
        "include_scenarios": ["pessimistic", "realistic", "optimistic"],
        "confidence_intervals": True
    }
}

# Expected Response
response_forecasting = {
    "forecast_period": "Q4 2024",
    "model_methodology": "Ensemble (regression, time_series, ML)",
    "data_sources": ["historical_revenue", "sales_pipeline", "market_indicators", "economic_data"],
    "model_accuracy": "87% on historical validation",
    
    "base_forecast": {
        "predicted_revenue": 132500000,
        "confidence_interval_95": [127800000, 137200000],
        "vs_q3_2024": 0.057,
        "vs_q4_2023": 0.089
    },
    
    "scenario_analysis": {
        "pessimistic": {
            "revenue": 121000000,
            "probability": 0.15,
            "key_assumptions": [
                "Economic downturn impacts customer spending",
                "2 major deals slip to Q1 2025",
                "Competitive pressure reduces pricing by 5%"
            ]
        },
        "realistic": {
            "revenue": 132500000,
            "probability": 0.70,
            "key_assumptions": [
                "Current pipeline conversion rates maintained",
                "Seasonal patterns consistent with historical",
                "No major market disruptions"
            ]
        },
        "optimistic": {
            "revenue": 145000000,
            "probability": 0.15,
            "key_assumptions": [
                "Accelerated AI product adoption",
                "Two strategic deals close ahead of schedule",
                "Market expansion ahead of plan"
            ]
        }
    },
    
    "key_drivers": [
        {
            "driver": "sales_pipeline_value",
            "impact_coefficient": 0.72,
            "current_value": 89500000,
            "trend": "stable_increasing"
        },
        {
            "driver": "customer_retention_rate",
            "impact_coefficient": 0.45,
            "current_value": 0.94,
            "trend": "stable"
        },
        {
            "driver": "market_growth_rate",
            "impact_coefficient": 0.33,
            "current_value": 0.08,
            "trend": "slowing"
        }
    ],
    
    "risk_factors": [
        {
            "risk": "Major customer churn",
            "probability": 0.08,
            "potential_impact": -12000000,
            "early_warning_indicators": ["NPS decline", "support ticket volume", "contract negotiation delays"]
        },
        {
            "risk": "Competitive disruption",
            "probability": 0.12,
            "potential_impact": -8000000,
            "early_warning_indicators": ["Market share decline", "pricing pressure", "win rate reduction"]
        }
    ],
    
    "recommendations": [
        "Focus sales efforts on high-probability pipeline deals",
        "Accelerate customer success initiatives to protect retention",
        "Prepare contingency plans for pessimistic scenario",
        "Monitor leading indicators weekly for early forecast updates"
    ],
    
    "model_updates": {
        "next_refresh": "2024-11-15",
        "refresh_frequency": "bi_weekly",
        "accuracy_monitoring": "continuous",
        "retrain_trigger": "accuracy_below_80%"
    }
}
```

This comprehensive collection of ERP RAG use cases demonstrates the practical application of RBAC-RAG systems across different business functions, user roles, and access levels. Each use case includes realistic queries, detailed responses, and proper authorization considerations, providing a blueprint for implementing similar systems in production environments.