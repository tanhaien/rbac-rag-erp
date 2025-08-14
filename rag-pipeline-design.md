# RAG Pipeline Design with RBAC Integration

## Overview
This document outlines the comprehensive design for the Retrieval Augmented Generation (RAG) pipeline integrated with Role-Based Access Control (RBAC), ensuring secure and contextually relevant responses based on user permissions.

## RAG Pipeline Architecture

### 1. Core Components

```python
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio
from enum import Enum

class QueryType(Enum):
    FACTUAL = "factual"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    PROCEDURAL = "procedural"

class SecurityLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class RAGQuery:
    query_text: str
    user_id: str
    user_roles: List[str]
    user_department: str
    query_type: QueryType
    security_level: SecurityLevel
    context_filters: Optional[Dict[str, Any]] = None
    max_results: int = 10
    timestamp: datetime = None
    session_id: str = None

@dataclass
class RAGResponse:
    response_text: str
    sources: List[Dict[str, Any]]
    confidence_score: float
    security_classification: str
    filtered_content_count: int
    processing_time: float
    timestamp: datetime = None
```

### 2. Query Processing Pipeline

```python
class RAGPipelineService:
    def __init__(self, 
                 auth_service,
                 access_control_service,
                 vector_db_service,
                 llm_service,
                 security_filter_service):
        self.auth = auth_service
        self.access_control = access_control_service
        self.vector_db = vector_db_service
        self.llm = llm_service
        self.security_filter = security_filter_service
    
    async def process_query(self, query: RAGQuery) -> RAGResponse:
        """Main RAG processing pipeline with RBAC integration"""
        
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Query validation and preprocessing
            validated_query = await self._validate_and_preprocess_query(query)
            
            # Step 2: Intent analysis and query expansion
            analyzed_query = await self._analyze_query_intent(validated_query)
            
            # Step 3: Secure document retrieval
            relevant_documents = await self._retrieve_documents_with_rbac(analyzed_query)
            
            # Step 4: Context assembly and ranking
            context = await self._assemble_and_rank_context(relevant_documents, analyzed_query)
            
            # Step 5: Response generation
            raw_response = await self._generate_response(context, analyzed_query)
            
            # Step 6: Security filtering and sanitization
            filtered_response = await self._apply_security_filters(raw_response, query)
            
            # Step 7: Response validation and formatting
            final_response = await self._validate_and_format_response(filtered_response, context)
            
            # Step 8: Audit logging
            await self._log_query_and_response(query, final_response)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return RAGResponse(
                response_text=final_response['text'],
                sources=final_response['sources'],
                confidence_score=final_response['confidence'],
                security_classification=final_response['classification'],
                filtered_content_count=final_response['filtered_count'],
                processing_time=processing_time,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            await self._log_error(query, str(e))
            raise
    
    async def _validate_and_preprocess_query(self, query: RAGQuery) -> RAGQuery:
        """Validate and preprocess incoming query"""
        
        # Input validation
        if not query.query_text or len(query.query_text.strip()) < 3:
            raise ValueError("Query text must be at least 3 characters long")
        
        if len(query.query_text) > 10000:
            raise ValueError("Query text too long (max 10000 characters)")
        
        # Security scanning for malicious input
        if await self._is_malicious_query(query.query_text):
            raise ValueError("Potentially malicious query detected")
        
        # Normalize query text
        normalized_text = await self._normalize_query_text(query.query_text)
        
        query.query_text = normalized_text
        query.timestamp = datetime.utcnow()
        
        return query
    
    async def _analyze_query_intent(self, query: RAGQuery) -> Dict[str, Any]:
        """Analyze query intent and expand with relevant terms"""
        
        # Basic intent classification
        intent_keywords = {
            QueryType.FACTUAL: ["what", "when", "where", "who", "define", "explain"],
            QueryType.ANALYTICAL: ["analyze", "compare", "why", "how", "impact", "relationship"],
            QueryType.CREATIVE: ["create", "design", "suggest", "brainstorm", "ideas"],
            QueryType.PROCEDURAL: ["steps", "process", "procedure", "how to", "guide"]
        }
        
        query_lower = query.query_text.lower()
        intent_scores = {}
        
        for intent_type, keywords in intent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            intent_scores[intent_type] = score
        
        # Determine primary intent
        primary_intent = max(intent_scores, key=intent_scores.get) if max(intent_scores.values()) > 0 else QueryType.FACTUAL
        
        # Query expansion based on intent and user context
        expanded_terms = await self._expand_query_terms(query.query_text, primary_intent, query.user_department)
        
        return {
            'original_query': query.query_text,
            'expanded_query': ' '.join(expanded_terms),
            'primary_intent': primary_intent,
            'intent_scores': intent_scores,
            'expanded_terms': expanded_terms,
            'user_context': {
                'department': query.user_department,
                'roles': query.user_roles,
                'security_level': query.security_level
            }
        }
    
    async def _retrieve_documents_with_rbac(self, analyzed_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Retrieve documents with role-based access control"""
        
        original_query = analyzed_query['original_query']
        expanded_query = analyzed_query['expanded_query']
        user_context = analyzed_query['user_context']
        
        # Prepare search filters based on user permissions
        search_filters = {
            'user_roles': user_context['roles'],
            'user_department': user_context['department'],
            'security_level': user_context['security_level'].value
        }
        
        # Add context-specific filters
        if analyzed_query['primary_intent'] == QueryType.PROCEDURAL:
            search_filters['document_types'] = ['procedure', 'manual', 'guide']
        elif analyzed_query['primary_intent'] == QueryType.ANALYTICAL:
            search_filters['document_types'] = ['report', 'analysis', 'research']
        
        # Perform multi-stage retrieval
        results = []
        
        # Stage 1: Semantic search with expanded query
        semantic_results = await self.vector_db.search_with_access_control(
            query=expanded_query,
            user_id=analyzed_query.get('user_id'),
            user_roles=user_context['roles'],
            user_department=user_context['department'],
            filters=search_filters,
            limit=15
        )
        results.extend(semantic_results)
        
        # Stage 2: Keyword-based search for exact matches
        keyword_results = await self.vector_db.keyword_search_with_access_control(
            query=original_query,
            user_id=analyzed_query.get('user_id'),
            user_roles=user_context['roles'],
            user_department=user_context['department'],
            filters=search_filters,
            limit=10
        )
        
        # Merge and deduplicate results
        unique_results = await self._merge_and_deduplicate_results(results, keyword_results)
        
        # Apply additional RBAC filtering
        filtered_results = []
        for result in unique_results:
            if await self.access_control.check_document_access(
                result['document_id'], 
                analyzed_query.get('user_id'),
                user_context['roles'],
                user_context['department']
            ):
                filtered_results.append(result)
        
        return filtered_results[:20]  # Limit to top 20 results
    
    async def _assemble_and_rank_context(self, documents: List[Dict[str, Any]], 
                                       analyzed_query: Dict[str, Any]) -> Dict[str, Any]:
        """Assemble and rank context from retrieved documents"""
        
        # Score documents based on relevance and user context
        scored_documents = []
        
        for doc in documents:
            score = await self._calculate_document_relevance_score(doc, analyzed_query)
            scored_documents.append((score, doc))
        
        # Sort by relevance score
        scored_documents.sort(reverse=True, key=lambda x: x[0])
        
        # Assemble context while respecting token limits
        max_context_tokens = 4000  # Adjust based on LLM limits
        current_tokens = 0
        selected_documents = []
        
        for score, doc in scored_documents:
            doc_tokens = await self._estimate_token_count(doc['content'])
            
            if current_tokens + doc_tokens <= max_context_tokens:
                selected_documents.append(doc)
                current_tokens += doc_tokens
            else:
                break
        
        # Create structured context
        context = {
            'documents': selected_documents,
            'total_sources': len(selected_documents),
            'relevance_scores': [score for score, _ in scored_documents[:len(selected_documents)]],
            'context_summary': await self._create_context_summary(selected_documents),
            'security_levels': list(set(doc['metadata'].get('classification_level', 'internal') 
                                      for doc in selected_documents))
        }
        
        return context
    
    async def _generate_response(self, context: Dict[str, Any], 
                               analyzed_query: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response using LLM with assembled context"""
        
        # Determine response security level
        max_security_level = await self._determine_response_security_level(context['security_levels'])
        
        # Build prompt based on query intent
        prompt = await self._build_context_aware_prompt(analyzed_query, context, max_security_level)
        
        # Generate response using LLM
        llm_response = await self.llm.generate_response(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.3,
            user_context={
                'roles': analyzed_query['user_context']['roles'],
                'department': analyzed_query['user_context']['department']
            }
        )
        
        # Extract source citations
        citations = await self._extract_citations(llm_response, context['documents'])
        
        return {
            'text': llm_response,
            'citations': citations,
            'context_used': context,
            'security_level': max_security_level,
            'confidence': await self._calculate_response_confidence(llm_response, context)
        }
    
    async def _apply_security_filters(self, raw_response: Dict[str, Any], 
                                    original_query: RAGQuery) -> Dict[str, Any]:
        """Apply security filtering to generated response"""
        
        response_text = raw_response['text']
        security_level = raw_response['security_level']
        
        # Content sanitization
        sanitized_text = await self.security_filter.sanitize_content(
            response_text, 
            user_roles=original_query.user_roles,
            security_clearance=security_level
        )
        
        # Remove or redact sensitive information
        filtered_text = await self.security_filter.filter_sensitive_information(
            sanitized_text,
            user_department=original_query.user_department
        )
        
        # Filter citations based on access control
        filtered_citations = []
        for citation in raw_response['citations']:
            if await self.access_control.check_document_access(
                citation['document_id'],
                original_query.user_id,
                original_query.user_roles,
                original_query.user_department
            ):
                filtered_citations.append(citation)
        
        # Track what was filtered for audit purposes
        filtered_count = len(raw_response['citations']) - len(filtered_citations)
        
        return {
            'text': filtered_text,
            'citations': filtered_citations,
            'original_text': response_text,
            'security_level': security_level,
            'filtered_count': filtered_count,
            'confidence': raw_response['confidence']
        }
    
    async def _build_context_aware_prompt(self, analyzed_query: Dict[str, Any], 
                                        context: Dict[str, Any], 
                                        security_level: str) -> str:
        """Build context-aware prompt for LLM"""
        
        intent = analyzed_query['primary_intent']
        user_context = analyzed_query['user_context']
        
        # Base prompt template
        base_prompt = f"""
You are an AI assistant with access to company documents. Answer the user's question based on the provided context.

User Context:
- Department: {user_context['department']}
- Roles: {', '.join(user_context['roles'])}
- Security Clearance: {security_level}

Query Intent: {intent.value}
Original Query: {analyzed_query['original_query']}

Context Information:
"""
        
        # Add document context
        for i, doc in enumerate(context['documents'][:5]):  # Limit to top 5 for prompt length
            base_prompt += f"""
Document {i+1}:
Classification: {doc['metadata'].get('classification_level', 'internal')}
Department: {doc['metadata'].get('department', 'general')}
Content: {doc['content'][:500]}...
---
"""
        
        # Intent-specific instructions
        intent_instructions = {
            QueryType.FACTUAL: "Provide accurate, factual information based on the context. Include specific details and cite sources.",
            QueryType.ANALYTICAL: "Analyze the information and provide insights, comparisons, or explanations. Show reasoning clearly.",
            QueryType.CREATIVE: "Use the context as inspiration but feel free to be creative in your suggestions and ideas.",
            QueryType.PROCEDURAL: "Provide clear, step-by-step instructions based on the procedures in the context."
        }
        
        base_prompt += f"""
Instructions: {intent_instructions.get(intent, intent_instructions[QueryType.FACTUAL])}

Important Guidelines:
1. Only use information from the provided context
2. Clearly indicate if information is not available in the context
3. Respect the security classification of information
4. Be concise but comprehensive
5. Include relevant citations in your response

Response:
"""
        
        return base_prompt

class SecurityFilterService:
    def __init__(self):
        self.sensitive_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN pattern
            r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',  # Credit card pattern
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email pattern
            r'\$[\d,]+(?:\.\d{2})?',  # Currency amounts
        ]
        
        self.department_restrictions = {
            'hr': ['salary', 'compensation', 'performance_review'],
            'finance': ['revenue', 'profit', 'budget', 'financial_data'],
            'legal': ['contract', 'litigation', 'legal_advice']
        }
    
    async def sanitize_content(self, content: str, user_roles: List[str], 
                             security_clearance: str) -> str:
        """Sanitize content based on user permissions"""
        
        # Apply role-based content filtering
        if 'admin' not in user_roles:
            # Remove highly sensitive information for non-admin users
            content = await self._apply_sensitivity_filters(content, security_clearance)
        
        # Apply pattern-based sanitization
        for pattern in self.sensitive_patterns:
            content = re.sub(pattern, '[REDACTED]', content)
        
        return content
    
    async def filter_sensitive_information(self, content: str, user_department: str) -> str:
        """Filter department-specific sensitive information"""
        
        # Apply department-specific filters
        if user_department in self.department_restrictions:
            restricted_terms = self.department_restrictions[user_department]
            
            for term in restricted_terms:
                if user_department not in ['hr', 'finance', 'legal']:  # These departments can see their own data
                    content = re.sub(f'\\b{term}\\b', '[RESTRICTED]', content, flags=re.IGNORECASE)
        
        return content

class ResponseCacheService:
    def __init__(self, redis_client):
        self.cache = redis_client
        self.default_ttl = 3600  # 1 hour
    
    async def get_cached_response(self, query_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached response for query"""
        
        cached_data = await self.cache.get(f"rag_response:{query_hash}")
        if cached_data:
            return json.loads(cached_data)
        return None
    
    async def cache_response(self, query_hash: str, response: Dict[str, Any], ttl: int = None):
        """Cache response with TTL"""
        
        ttl = ttl or self.default_ttl
        
        # Don't cache responses with sensitive information
        if response.get('security_level') in ['confidential', 'restricted']:
            ttl = 300  # 5 minutes for sensitive content
        
        await self.cache.setex(
            f"rag_response:{query_hash}",
            ttl,
            json.dumps(response, default=str)
        )
    
    async def generate_query_hash(self, query: RAGQuery) -> str:
        """Generate hash for query caching"""
        
        # Include user context in hash for personalized caching
        query_data = {
            'text': query.query_text,
            'user_roles': sorted(query.user_roles),
            'user_department': query.user_department,
            'query_type': query.query_type.value,
            'security_level': query.security_level.value
        }
        
        query_string = json.dumps(query_data, sort_keys=True)
        return hashlib.sha256(query_string.encode()).hexdigest()
```

### 3. Performance Optimization

```python
class RAGPerformanceOptimizer:
    def __init__(self, cache_service, metrics_service):
        self.cache = cache_service
        self.metrics = metrics_service
    
    async def optimize_query_performance(self, query: RAGQuery) -> RAGQuery:
        """Optimize query for better performance"""
        
        # Query simplification for complex queries
        if len(query.query_text) > 500:
            simplified_query = await self._simplify_complex_query(query.query_text)
            query.query_text = simplified_query
        
        # Adjust search parameters based on query type
        if query.query_type == QueryType.FACTUAL:
            query.max_results = min(query.max_results, 5)  # Fewer results for factual queries
        elif query.query_type == QueryType.ANALYTICAL:
            query.max_results = min(query.max_results, 15)  # More results for analysis
        
        return query
    
    async def implement_progressive_loading(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Implement progressive loading for large contexts"""
        
        documents = context['documents']
        
        # Load essential documents first
        essential_docs = documents[:3]  # Top 3 most relevant
        
        # Load additional documents based on confidence scores
        if context.get('confidence_threshold', 0.8) < 0.8:
            additional_docs = documents[3:8]  # Load more if confidence is low
            essential_docs.extend(additional_docs)
        
        context['documents'] = essential_docs
        context['progressive_loading'] = True
        
        return context
```

### 4. Error Handling and Fallbacks

```python
class RAGErrorHandler:
    def __init__(self, fallback_service, notification_service):
        self.fallback = fallback_service
        self.notifications = notification_service
    
    async def handle_retrieval_failure(self, query: RAGQuery, error: Exception) -> List[Dict[str, Any]]:
        """Handle document retrieval failures"""
        
        # Log error
        await self._log_retrieval_error(query, error)
        
        # Try fallback retrieval strategies
        fallback_results = []
        
        try:
            # Strategy 1: Simplified query
            simplified_query = await self._simplify_query(query.query_text)
            fallback_results = await self.fallback.simple_keyword_search(
                simplified_query, query.user_roles, query.user_department
            )
        except Exception:
            pass
        
        if not fallback_results:
            try:
                # Strategy 2: Cached similar queries
                fallback_results = await self.fallback.find_similar_cached_results(query)
            except Exception:
                pass
        
        return fallback_results or []
    
    async def handle_llm_failure(self, query: RAGQuery, context: Dict[str, Any], 
                               error: Exception) -> str:
        """Handle LLM generation failures"""
        
        await self._log_llm_error(query, error)
        
        # Fallback to template-based responses
        if query.query_type == QueryType.FACTUAL:
            return await self._generate_template_factual_response(context)
        elif query.query_type == QueryType.PROCEDURAL:
            return await self._generate_template_procedural_response(context)
        else:
            return ("I apologize, but I'm unable to generate a response at this time. "
                   "Please try rephrasing your question or contact support for assistance.")
```

### 5. API Integration

```python
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    query_type: Optional[str] = "factual"
    security_level: Optional[str] = "medium"
    context_filters: Optional[Dict[str, Any]] = None
    max_results: Optional[int] = 10

class QueryResponse(BaseModel):
    response: str
    sources: List[Dict[str, Any]]
    confidence_score: float
    security_classification: str
    processing_time: float
    query_id: str

@router.post("/rag/query", response_model=QueryResponse)
@require_permission("query:rag")
async def process_rag_query(request: Request, query_request: QueryRequest):
    """Process RAG query with RBAC"""
    
    user_data = request.state.user
    
    # Create RAG query object
    rag_query = RAGQuery(
        query_text=query_request.query,
        user_id=user_data['sub'],
        user_roles=user_data['roles'],
        user_department=user_data.get('department', 'general'),
        query_type=QueryType(query_request.query_type),
        security_level=SecurityLevel(query_request.security_level),
        context_filters=query_request.context_filters,
        max_results=query_request.max_results,
        session_id=request.headers.get('X-Session-ID')
    )
    
    # Process query through RAG pipeline
    try:
        response = await rag_pipeline_service.process_query(rag_query)
        
        return QueryResponse(
            response=response.response_text,
            sources=response.sources,
            confidence_score=response.confidence_score,
            security_classification=response.security_classification,
            processing_time=response.processing_time,
            query_id=str(uuid.uuid4())
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@router.get("/rag/query-history")
@require_permission("query:history")
async def get_query_history(request: Request, limit: int = 20, offset: int = 0):
    """Get user's query history"""
    
    user_data = request.state.user
    history = await query_history_service.get_user_history(
        user_data['sub'], limit, offset
    )
    
    return {
        "queries": history,
        "total": len(history)
    }
```

This RAG pipeline design provides comprehensive integration with RBAC while maintaining high performance, security, and user experience. The system ensures that users only receive information they're authorized to access while providing contextually relevant and accurate responses.