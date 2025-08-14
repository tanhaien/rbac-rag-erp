# ERP Performance Optimization for RBAC-RAG Systems

## Overview

This document provides comprehensive performance optimization strategies for ERP RBAC-RAG systems handling large datasets, high query volumes, and real-time processing requirements. The optimizations cover database performance, vector search efficiency, caching strategies, and system scalability.

## Performance Architecture

### 1. Multi-Tier Caching Strategy

```python
# app/performance/caching_layers.py
import redis
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import hashlib

@dataclass
class CacheConfig:
    ttl_seconds: int
    max_size: int
    eviction_policy: str
    compression: bool = False
    encryption: bool = False

class MultiTierCacheManager:
    """Multi-layer caching system for ERP RBAC-RAG performance"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.local_cache = {}
        
        # Cache configuration by data type
        self.cache_configs = {
            "authorization_decisions": CacheConfig(
                ttl_seconds=300,  # 5 minutes
                max_size=10000,
                eviction_policy="lru"
            ),
            "erp_query_results": CacheConfig(
                ttl_seconds=1800,  # 30 minutes
                max_size=1000,
                eviction_policy="lru",
                compression=True
            ),
            "document_metadata": CacheConfig(
                ttl_seconds=3600,  # 1 hour
                max_size=50000,
                eviction_policy="lru"
            ),
            "user_permissions": CacheConfig(
                ttl_seconds=900,  # 15 minutes
                max_size=5000,
                eviction_policy="lru"
            ),
            "vector_search_results": CacheConfig(
                ttl_seconds=600,  # 10 minutes
                max_size=2000,
                eviction_policy="lru",
                compression=True
            ),
            "financial_reports": CacheConfig(
                ttl_seconds=7200,  # 2 hours
                max_size=500,
                eviction_policy="lfu",  # Least frequently used
                encryption=True  # Financial data needs encryption
            )
        }
    
    async def get_cached_item(self, cache_type: str, key: str) -> Optional[Any]:
        """Get item from appropriate cache layer"""
        
        cache_key = f"{cache_type}:{key}"
        config = self.cache_configs.get(cache_type)
        
        if not config:
            return None
        
        # Try local cache first (L1)
        if cache_key in self.local_cache:
            item = self.local_cache[cache_key]
            if item['expires'] > datetime.utcnow():
                return item['data']
            else:
                del self.local_cache[cache_key]
        
        # Try Redis cache (L2)
        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                
                # Decompress if needed
                if config.compression:
                    data = await self._decompress_data(data)
                
                # Decrypt if needed
                if config.encryption:
                    data = await self._decrypt_data(data)
                
                # Store in local cache for faster access
                self._store_local_cache(cache_key, data, config.ttl_seconds)
                
                return data
                
        except Exception as e:
            logger.warning(f"Cache retrieval error for {cache_key}: {e}")
        
        return None
    
    async def set_cached_item(self, cache_type: str, key: str, data: Any):
        """Set item in appropriate cache layers"""
        
        cache_key = f"{cache_type}:{key}"
        config = self.cache_configs.get(cache_type)
        
        if not config:
            return
        
        # Process data based on config
        processed_data = data
        
        if config.encryption:
            processed_data = await self._encrypt_data(processed_data)
        
        if config.compression:
            processed_data = await self._compress_data(processed_data)
        
        # Store in Redis (L2)
        try:
            await self.redis.setex(
                cache_key,
                config.ttl_seconds,
                json.dumps(processed_data, default=str)
            )
        except Exception as e:
            logger.error(f"Redis cache storage error for {cache_key}: {e}")
        
        # Store in local cache (L1)
        self._store_local_cache(cache_key, data, config.ttl_seconds)
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        
        # Invalidate local cache
        keys_to_remove = [k for k in self.local_cache.keys() if pattern in k]
        for key in keys_to_remove:
            del self.local_cache[key]
        
        # Invalidate Redis cache
        try:
            keys = await self.redis.keys(f"*{pattern}*")
            if keys:
                await self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"Cache invalidation error for pattern {pattern}: {e}")
    
    def _store_local_cache(self, key: str, data: Any, ttl_seconds: int):
        """Store item in local cache with size limits"""
        
        # Remove expired items first
        current_time = datetime.utcnow()
        expired_keys = [
            k for k, v in self.local_cache.items() 
            if v['expires'] <= current_time
        ]
        for key in expired_keys:
            del self.local_cache[key]
        
        # Check size limits and evict if necessary
        if len(self.local_cache) >= 1000:  # Global local cache limit
            # Remove oldest entries
            sorted_items = sorted(
                self.local_cache.items(),
                key=lambda x: x[1]['created']
            )
            for old_key, _ in sorted_items[:100]:  # Remove 100 oldest
                del self.local_cache[old_key]
        
        # Store new item
        self.local_cache[key] = {
            'data': data,
            'created': current_time,
            'expires': current_time + timedelta(seconds=ttl_seconds)
        }

# Global cache manager
cache_manager = MultiTierCacheManager(redis_client)
```

### 2. Query Performance Optimization

```python
# app/performance/query_optimizer.py
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import time
from ..erp.connectors.base_connector import ERPQuery, DataCategory

@dataclass
class QueryPerformanceMetrics:
    query_time: float
    cache_hit_rate: float
    authorization_time: float
    erp_fetch_time: float
    vector_search_time: float
    total_time: float
    result_count: int
    filtered_count: int

class QueryOptimizer:
    """Optimize ERP RAG query performance"""
    
    def __init__(self, cache_manager, metrics_collector):
        self.cache = cache_manager
        self.metrics = metrics_collector
        self.query_stats = {}
        
    async def optimize_query_execution(self, 
                                     query: str,
                                     user_context: Dict[str, Any],
                                     query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize query execution with performance tracking"""
        
        start_time = time.time()
        metrics = QueryPerformanceMetrics(0, 0, 0, 0, 0, 0, 0, 0)
        
        try:
            # Generate query signature for caching
            query_signature = self._generate_query_signature(query, user_context, query_params)
            
            # Check cache first
            cache_start = time.time()
            cached_result = await self.cache.get_cached_item("rag_query_results", query_signature)
            if cached_result:
                metrics.cache_hit_rate = 1.0
                metrics.total_time = time.time() - start_time
                await self.metrics.record_query_performance(metrics)
                return cached_result
            
            # Execute optimized query pipeline
            result = await self._execute_optimized_pipeline(
                query, user_context, query_params, metrics
            )
            
            # Cache successful results
            await self.cache.set_cached_item("rag_query_results", query_signature, result)
            
            metrics.total_time = time.time() - start_time
            await self.metrics.record_query_performance(metrics)
            
            return result
            
        except Exception as e:
            metrics.total_time = time.time() - start_time
            await self.metrics.record_query_error(query, str(e), metrics)
            raise
    
    async def _execute_optimized_pipeline(self,
                                        query: str,
                                        user_context: Dict[str, Any],
                                        query_params: Dict[str, Any],
                                        metrics: QueryPerformanceMetrics) -> Dict[str, Any]:
        """Execute optimized query pipeline"""
        
        # Stage 1: Fast authorization check
        auth_start = time.time()
        user_permissions = await self._get_cached_user_permissions(user_context)
        metrics.authorization_time = time.time() - auth_start
        
        # Stage 2: Parallel data fetching
        fetch_start = time.time()
        
        # Determine optimal data sources based on query
        data_sources = await self._analyze_optimal_sources(query, user_permissions)
        
        # Execute parallel fetches
        fetch_tasks = []
        
        if 'vector_search' in data_sources:
            fetch_tasks.append(self._optimized_vector_search(query, user_context))
        
        if 'erp_data' in data_sources:
            fetch_tasks.append(self._optimized_erp_fetch(query, user_context, query_params))
        
        if 'document_metadata' in data_sources:
            fetch_tasks.append(self._optimized_metadata_fetch(query, user_context))
        
        # Wait for all fetches to complete
        fetch_results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
        metrics.erp_fetch_time = time.time() - fetch_start
        
        # Stage 3: Result assembly and filtering
        assembly_start = time.time()
        
        assembled_results = await self._assemble_results(fetch_results, user_permissions)
        metrics.result_count = len(assembled_results.get('raw_results', []))
        
        # Apply authorization filtering
        filtered_results = await self._apply_authorization_filters(assembled_results, user_context)
        metrics.filtered_count = len(filtered_results.get('authorized_results', []))
        
        # Stage 4: Response generation optimization
        response = await self._generate_optimized_response(filtered_results, query)
        
        return response
    
    async def _optimized_vector_search(self, query: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimized vector database search"""
        
        search_start = time.time()
        
        # Build optimized search parameters
        search_params = {
            'query': query,
            'user_roles': user_context['roles'],
            'user_department': user_context.get('department'),
            'limit': 50,  # Fetch more initially, filter later
            'include_metadata': True
        }
        
        # Use semantic search with pre-filtering
        results = await self.vector_db.optimized_search(search_params)
        
        search_time = time.time() - search_start
        
        return {
            'type': 'vector_search',
            'results': results,
            'search_time': search_time,
            'result_count': len(results)
        }
    
    async def _optimized_erp_fetch(self, 
                                 query: str, 
                                 user_context: Dict[str, Any],
                                 query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Optimized ERP data fetching"""
        
        fetch_start = time.time()
        
        # Determine ERP query type and optimize parameters
        erp_query_type = self._classify_erp_query(query)
        
        optimized_params = await self._optimize_erp_parameters(
            erp_query_type, query_params, user_context
        )
        
        # Use appropriate ERP connector with optimized query
        erp_results = await self.erp_connector.execute_optimized_query(optimized_params)
        
        fetch_time = time.time() - fetch_start
        
        return {
            'type': 'erp_data',
            'results': erp_results,
            'fetch_time': fetch_time,
            'query_type': erp_query_type
        }
    
    async def _get_cached_user_permissions(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get user permissions with caching"""
        
        user_id = user_context['user_id']
        cache_key = f"permissions_{user_id}_{hash(str(user_context['roles']))}"
        
        cached_permissions = await self.cache.get_cached_item("user_permissions", cache_key)
        
        if cached_permissions:
            return cached_permissions
        
        # Compute permissions if not cached
        permissions = await self.authorization_service.get_user_permissions(user_context)
        
        # Cache for future use
        await self.cache.set_cached_item("user_permissions", cache_key, permissions)
        
        return permissions
    
    def _generate_query_signature(self, 
                                query: str, 
                                user_context: Dict[str, Any],
                                query_params: Dict[str, Any]) -> str:
        """Generate unique signature for query caching"""
        
        signature_data = {
            'query': query.lower().strip(),
            'user_roles': sorted(user_context.get('roles', [])),
            'user_department': user_context.get('department'),
            'clearance_level': user_context.get('clearance_level'),
            'query_params': query_params
        }
        
        signature_str = json.dumps(signature_data, sort_keys=True)
        return hashlib.sha256(signature_str.encode()).hexdigest()[:16]
    
    async def _analyze_optimal_sources(self, query: str, user_permissions: Dict[str, Any]) -> List[str]:
        """Analyze and determine optimal data sources for query"""
        
        sources = []
        query_lower = query.lower()
        
        # Always include vector search for semantic matching
        sources.append('vector_search')
        
        # Add ERP data if query suggests structured data need
        if any(term in query_lower for term in ['revenue', 'budget', 'employee', 'inventory', 'sales']):
            sources.append('erp_data')
        
        # Add metadata if query is about document properties
        if any(term in query_lower for term in ['document', 'report', 'file', 'classification']):
            sources.append('document_metadata')
        
        return sources

# Global query optimizer
query_optimizer = QueryOptimizer(cache_manager, metrics_collector)
```

### 3. Database Performance Optimization

```python
# app/performance/database_optimizer.py
import asyncio
import asyncpg
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager

class DatabaseOptimizer:
    """Database performance optimization for ERP RBAC-RAG"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.connection_pool = None
        self.read_replicas = []
        self.prepared_statements = {}
        
    async def initialize_optimized_pool(self):
        """Initialize optimized connection pool"""
        
        self.connection_pool = await asyncpg.create_pool(
            self.database_url,
            min_size=10,
            max_size=50,
            max_queries=50000,
            max_inactive_connection_lifetime=300,
            command_timeout=30,
            server_settings={
                'jit': 'off',  # Disable JIT for OLTP workloads
                'shared_preload_libraries': 'pg_stat_statements',
                'track_activity_query_size': '2048',
                'wal_buffers': '16MB',
                'checkpoint_completion_target': '0.9',
                'random_page_cost': '1.1',  # For SSD storage
                'effective_cache_size': '4GB'
            }
        )
        
        # Prepare frequently used statements
        await self._prepare_statements()
        
        # Set up read replicas if available
        await self._setup_read_replicas()
    
    async def _prepare_statements(self):
        """Prepare frequently used SQL statements"""
        
        statements = {
            'get_user_permissions': """
                SELECT ur.role_id, r.name as role_name, r.permissions
                FROM user_roles ur
                JOIN roles r ON ur.role_id = r.id
                WHERE ur.user_id = $1 AND ur.is_active = true
            """,
            
            'check_document_access': """
                SELECT dac.permission_type
                FROM document_access_control dac
                WHERE dac.document_id = $1 
                AND dac.access_type = $2 
                AND dac.access_value = $3
                AND dac.is_active = true
                AND (dac.expires_at IS NULL OR dac.expires_at > NOW())
            """,
            
            'get_document_metadata': """
                SELECT d.id, d.title, d.classification_level, d.department, 
                       d.metadata, d.created_at, d.updated_at
                FROM documents d
                WHERE d.id = ANY($1) AND d.is_active = true
            """,
            
            'search_documents': """
                SELECT d.id, d.title, d.classification_level, d.department,
                       ts_rank(d.search_vector, plainto_tsquery($1)) as rank
                FROM documents d
                WHERE d.search_vector @@ plainto_tsquery($1)
                AND d.classification_level = ANY($2)
                AND d.department = ANY($3)
                ORDER BY rank DESC
                LIMIT $4
            """,
            
            'log_query_audit': """
                INSERT INTO access_audit_log 
                (user_id, action, resource_type, resource_id, details, ip_address, success)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """
        }
        
        async with self.connection_pool.acquire() as conn:
            for name, sql in statements.items():
                await conn.execute(f"PREPARE {name} AS {sql}")
                self.prepared_statements[name] = sql
    
    @asynccontextmanager
    async def get_optimized_connection(self, read_only: bool = False):
        """Get optimized database connection"""
        
        pool = self.connection_pool
        
        # Use read replica for read-only queries if available
        if read_only and self.read_replicas:
            pool = random.choice(self.read_replicas)
        
        async with pool.acquire() as conn:
            if read_only:
                await conn.execute("SET default_transaction_read_only = on")
            
            yield conn
    
    async def execute_optimized_query(self, 
                                    query_name: str, 
                                    params: List[Any],
                                    read_only: bool = True) -> List[Dict[str, Any]]:
        """Execute optimized prepared statement"""
        
        async with self.get_optimized_connection(read_only) as conn:
            if query_name in self.prepared_statements:
                return await conn.fetch(f"EXECUTE {query_name}({', '.join(['$' + str(i+1) for i in range(len(params))])})", *params)
            else:
                raise ValueError(f"Prepared statement {query_name} not found")
    
    async def bulk_operation_optimized(self, 
                                     operation: str,
                                     data: List[Dict[str, Any]],
                                     batch_size: int = 1000) -> int:
        """Optimized bulk database operations"""
        
        total_affected = 0
        
        async with self.get_optimized_connection(read_only=False) as conn:
            # Use transaction for consistency
            async with conn.transaction():
                # Process in batches to avoid memory issues
                for i in range(0, len(data), batch_size):
                    batch = data[i:i + batch_size]
                    
                    if operation == 'insert_documents':
                        result = await conn.executemany(
                            """INSERT INTO documents 
                               (id, title, classification_level, department, metadata, created_by)
                               VALUES ($1, $2, $3, $4, $5, $6)""",
                            [(d['id'], d['title'], d['classification_level'], 
                              d['department'], d['metadata'], d['created_by']) for d in batch]
                        )
                    elif operation == 'update_classifications':
                        result = await conn.executemany(
                            """UPDATE documents 
                               SET classification_level = $2, updated_at = NOW()
                               WHERE id = $1""",
                            [(d['id'], d['classification_level']) for d in batch]
                        )
                    
                    total_affected += len(batch)
        
        return total_affected
    
    async def optimize_database_performance(self):
        """Run database performance optimizations"""
        
        async with self.get_optimized_connection(read_only=False) as conn:
            
            # Update table statistics
            await conn.execute("ANALYZE documents")
            await conn.execute("ANALYZE document_access_control")
            await conn.execute("ANALYZE users")
            await conn.execute("ANALYZE user_roles")
            
            # Rebuild indexes if needed
            await conn.execute("REINDEX INDEX CONCURRENTLY idx_documents_classification")
            await conn.execute("REINDEX INDEX CONCURRENTLY idx_document_access_control_document_id")
            
            # Clean up old audit logs
            await conn.execute("""
                DELETE FROM access_audit_log 
                WHERE timestamp < NOW() - INTERVAL '90 days'
            """)
            
            # Update query planner statistics
            await conn.execute("SELECT pg_stat_reset()")

# Database performance monitoring
class DatabaseMetrics:
    """Monitor database performance metrics"""
    
    def __init__(self, db_optimizer: DatabaseOptimizer):
        self.db = db_optimizer
        self.metrics_history = []
    
    async def collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive database performance metrics"""
        
        async with self.db.get_optimized_connection(read_only=True) as conn:
            
            # Connection pool metrics
            pool_stats = {
                'total_connections': self.db.connection_pool.get_size(),
                'available_connections': self.db.connection_pool.get_idle_size(),
                'max_connections': self.db.connection_pool.get_max_size()
            }
            
            # Query performance metrics
            query_stats = await conn.fetch("""
                SELECT query, calls, total_time, mean_time, max_time, rows
                FROM pg_stat_statements 
                WHERE query LIKE '%documents%' OR query LIKE '%user_roles%'
                ORDER BY total_time DESC
                LIMIT 10
            """)
            
            # Lock metrics
            lock_stats = await conn.fetch("""
                SELECT mode, locktype, database, relation::regclass, count(*)
                FROM pg_locks 
                WHERE database = (SELECT oid FROM pg_database WHERE datname = current_database())
                GROUP BY mode, locktype, database, relation
                ORDER BY count DESC
            """)
            
            # Index usage metrics
            index_stats = await conn.fetch("""
                SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch
                FROM pg_stat_user_indexes 
                WHERE schemaname = 'public'
                ORDER BY idx_tup_read + idx_tup_fetch DESC
                LIMIT 10
            """)
            
            return {
                'timestamp': datetime.utcnow(),
                'pool_stats': pool_stats,
                'slow_queries': [dict(row) for row in query_stats],
                'locks': [dict(row) for row in lock_stats],
                'index_usage': [dict(row) for row in index_stats]
            }
    
    async def identify_performance_issues(self) -> List[Dict[str, Any]]:
        """Identify potential performance issues"""
        
        issues = []
        
        async with self.db.get_optimized_connection(read_only=True) as conn:
            
            # Check for unused indexes
            unused_indexes = await conn.fetch("""
                SELECT schemaname, tablename, indexname, idx_scan
                FROM pg_stat_user_indexes 
                WHERE idx_scan < 10 AND schemaname = 'public'
            """)
            
            for idx in unused_indexes:
                issues.append({
                    'type': 'unused_index',
                    'severity': 'medium',
                    'description': f"Index {idx['indexname']} on {idx['tablename']} has low usage ({idx['idx_scan']} scans)",
                    'recommendation': 'Consider dropping this index to improve write performance'
                })
            
            # Check for missing indexes
            seq_scans = await conn.fetch("""
                SELECT schemaname, tablename, seq_scan, seq_tup_read, 
                       seq_tup_read/GREATEST(seq_scan, 1) as avg_tup_per_scan
                FROM pg_stat_user_tables 
                WHERE seq_scan > 1000 AND schemaname = 'public'
                ORDER BY seq_tup_read DESC
            """)
            
            for scan in seq_scans:
                if scan['avg_tup_per_scan'] > 10000:
                    issues.append({
                        'type': 'missing_index',
                        'severity': 'high',
                        'description': f"Table {scan['tablename']} has high sequential scan cost",
                        'recommendation': 'Consider adding indexes on frequently queried columns'
                    })
        
        return issues

# Global database optimizer
db_optimizer = DatabaseOptimizer(database_url)
```

### 4. Vector Search Optimization

```python
# app/performance/vector_optimizer.py
import chromadb
import numpy as np
from typing import Dict, List, Any, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
import faiss

class VectorSearchOptimizer:
    """Optimize vector search performance for large ERP datasets"""
    
    def __init__(self, chromadb_client):
        self.client = chromadb_client
        self.collection = None
        self.faiss_index = None
        self.document_metadata = {}
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        
    async def initialize_optimized_collection(self, collection_name: str = "erp_documents"):
        """Initialize optimized vector collection"""
        
        # Create or get collection with optimized settings
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={
                "hnsw:space": "cosine",
                "hnsw:M": 16,  # Optimized for balance of speed/accuracy
                "hnsw:ef_construction": 200,
                "hnsw:ef_search": 100
            }
        )
        
        # Build FAISS index for ultra-fast search
        await self._build_faiss_index()
    
    async def _build_faiss_index(self):
        """Build FAISS index for high-performance search"""
        
        try:
            # Get all embeddings from ChromaDB
            all_data = self.collection.get(include=['embeddings', 'metadatas'])
            
            if not all_data['embeddings']:
                return
            
            embeddings = np.array(all_data['embeddings']).astype('float32')
            
            # Choose FAISS index type based on dataset size
            if len(embeddings) < 100000:
                # Use IVF for medium datasets
                nlist = min(4096, len(embeddings) // 10)
                quantizer = faiss.IndexFlatIP(embeddings.shape[1])  # Inner product for cosine similarity
                self.faiss_index = faiss.IndexIVFFlat(quantizer, embeddings.shape[1], nlist)
                
            else:
                # Use HNSW for large datasets
                self.faiss_index = faiss.IndexHNSWFlat(embeddings.shape[1], 32)
                self.faiss_index.hnsw.efConstruction = 200
                self.faiss_index.hnsw.efSearch = 100
            
            # Train and add vectors
            if hasattr(self.faiss_index, 'train'):
                self.faiss_index.train(embeddings)
            
            self.faiss_index.add(embeddings)
            
            # Store metadata mapping
            self.document_metadata = {
                i: all_data['metadatas'][i] for i in range(len(all_data['metadatas']))
            }
            
            logger.info(f"FAISS index built with {len(embeddings)} vectors")
            
        except Exception as e:
            logger.error(f"Failed to build FAISS index: {e}")
    
    async def optimized_search(self, 
                             query_embedding: List[float],
                             user_context: Dict[str, Any],
                             limit: int = 10,
                             pre_filter: bool = True) -> List[Dict[str, Any]]:
        """Perform optimized vector search with RBAC filtering"""
        
        if self.faiss_index is None:
            # Fallback to ChromaDB search
            return await self._chromadb_search(query_embedding, user_context, limit)
        
        # Convert query to numpy array
        query_vector = np.array([query_embedding]).astype('float32')
        
        # Search with FAISS (much faster than ChromaDB)
        search_k = min(limit * 5, len(self.document_metadata))  # Get more candidates for filtering
        
        loop = asyncio.get_event_loop()
        distances, indices = await loop.run_in_executor(
            self.thread_pool,
            lambda: self.faiss_index.search(query_vector, search_k)
        )
        
        # Process results with authorization filtering
        results = []
        user_roles = user_context.get('roles', [])
        user_department = user_context.get('department')
        clearance_level = user_context.get('clearance_level', 1)
        
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx == -1:  # FAISS uses -1 for empty results
                continue
                
            metadata = self.document_metadata.get(idx, {})
            
            # Apply authorization filtering
            if await self._check_vector_access(metadata, user_roles, user_department, clearance_level):
                results.append({
                    'id': metadata.get('document_id'),
                    'distance': float(distance),
                    'similarity': 1.0 - float(distance),  # Convert distance to similarity
                    'metadata': metadata,
                    'rank': i + 1
                })
            
            if len(results) >= limit:
                break
        
        return results
    
    async def _check_vector_access(self, 
                                 metadata: Dict[str, Any],
                                 user_roles: List[str],
                                 user_department: str,
                                 clearance_level: int) -> bool:
        """Fast authorization check for vector search results"""
        
        # Check classification level
        doc_classification = metadata.get('classification_level', 'internal')
        required_clearance = CLASSIFICATION_LEVELS.get(doc_classification, {}).get('level', 1)
        
        if clearance_level < required_clearance:
            return False
        
        # Check department access
        doc_department = metadata.get('department')
        if doc_department and doc_department != 'general':
            if user_department != doc_department and 'admin' not in user_roles:
                # Check cross-department access
                accessible_departments = metadata.get('accessible_departments', [])
                if user_department not in accessible_departments:
                    return False
        
        return True
    
    async def batch_add_documents(self, 
                                documents: List[Dict[str, Any]],
                                batch_size: int = 1000):
        """Optimized batch document addition"""
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            # Prepare batch data
            ids = [doc['id'] for doc in batch]
            embeddings = [doc['embedding'] for doc in batch]
            metadatas = [doc['metadata'] for doc in batch]
            documents_text = [doc.get('text', '') for doc in batch]
            
            # Add to ChromaDB
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents_text
            )
            
            logger.info(f"Added batch {i//batch_size + 1}/{len(documents)//batch_size + 1}")
        
        # Rebuild FAISS index after batch operations
        await self._build_faiss_index()
    
    async def update_vector_metadata(self, 
                                   document_id: str,
                                   new_metadata: Dict[str, Any]):
        """Update vector metadata efficiently"""
        
        # Update in ChromaDB
        self.collection.update(
            ids=[document_id],
            metadatas=[new_metadata]
        )
        
        # Update local metadata cache
        for idx, metadata in self.document_metadata.items():
            if metadata.get('document_id') == document_id:
                self.document_metadata[idx] = new_metadata
                break

# Performance monitoring for vector operations
class VectorPerformanceMonitor:
    """Monitor vector search performance"""
    
    def __init__(self):
        self.search_metrics = []
        
    async def record_search_performance(self,
                                      query_time: float,
                                      result_count: int,
                                      filtered_count: int,
                                      search_method: str):
        """Record vector search performance metrics"""
        
        metric = {
            'timestamp': datetime.utcnow(),
            'query_time': query_time,
            'result_count': result_count,
            'filtered_count': filtered_count,
            'filter_rate': (result_count - filtered_count) / result_count if result_count > 0 else 0,
            'search_method': search_method
        }
        
        self.search_metrics.append(metric)
        
        # Keep only last 1000 metrics
        if len(self.search_metrics) > 1000:
            self.search_metrics = self.search_metrics[-1000:]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get vector search performance summary"""
        
        if not self.search_metrics:
            return {}
        
        recent_metrics = self.search_metrics[-100:]  # Last 100 searches
        
        avg_query_time = sum(m['query_time'] for m in recent_metrics) / len(recent_metrics)
        avg_results = sum(m['result_count'] for m in recent_metrics) / len(recent_metrics)
        avg_filter_rate = sum(m['filter_rate'] for m in recent_metrics) / len(recent_metrics)
        
        return {
            'avg_query_time': avg_query_time,
            'avg_result_count': avg_results,
            'avg_filter_rate': avg_filter_rate,
            'total_searches': len(self.search_metrics),
            'search_methods': list(set(m['search_method'] for m in recent_metrics))
        }

# Global instances
vector_optimizer = VectorSearchOptimizer(chromadb_client)
vector_monitor = VectorPerformanceMonitor()
```

### 5. System Scaling and Load Balancing

```python
# app/performance/scaling_manager.py
import asyncio
import psutil
from typing import Dict, List, Any
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta

@dataclass 
class SystemMetrics:
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    active_connections: int
    query_queue_size: int
    timestamp: datetime

class AutoScalingManager:
    """Manage automatic scaling based on system metrics"""
    
    def __init__(self):
        self.metrics_history = []
        self.scaling_thresholds = {
            'cpu_high': 80.0,
            'cpu_low': 30.0,
            'memory_high': 85.0,
            'memory_low': 40.0,
            'queue_high': 100,
            'response_time_high': 2.0
        }
        self.scaling_actions = []
        
    async def monitor_and_scale(self):
        """Continuously monitor system and trigger scaling actions"""
        
        while True:
            try:
                # Collect current metrics
                metrics = await self._collect_system_metrics()
                self.metrics_history.append(metrics)
                
                # Keep only last hour of metrics
                cutoff_time = datetime.utcnow() - timedelta(hours=1)
                self.metrics_history = [
                    m for m in self.metrics_history if m.timestamp > cutoff_time
                ]
                
                # Analyze scaling needs
                scaling_decision = await self._analyze_scaling_needs(metrics)
                
                if scaling_decision['action'] != 'none':
                    await self._execute_scaling_action(scaling_decision)
                
                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Auto-scaling monitor error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _collect_system_metrics(self) -> SystemMetrics:
        """Collect comprehensive system metrics"""
        
        # CPU usage
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_usage = disk.percent
        
        # Network I/O
        network = psutil.net_io_counters()
        network_io = {
            'bytes_sent': network.bytes_sent,
            'bytes_recv': network.bytes_recv,
            'packets_sent': network.packets_sent,
            'packets_recv': network.packets_recv
        }
        
        # Application-specific metrics
        active_connections = await self._get_active_connections()
        query_queue_size = await self._get_query_queue_size()
        
        return SystemMetrics(
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            network_io=network_io,
            active_connections=active_connections,
            query_queue_size=query_queue_size,
            timestamp=datetime.utcnow()
        )
    
    async def _analyze_scaling_needs(self, current_metrics: SystemMetrics) -> Dict[str, Any]:
        """Analyze if scaling actions are needed"""
        
        if len(self.metrics_history) < 5:
            return {'action': 'none', 'reason': 'insufficient_data'}
        
        # Get recent metrics (last 5 minutes)
        recent_metrics = self.metrics_history[-10:]
        
        avg_cpu = sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_usage for m in recent_metrics) / len(recent_metrics)
        avg_queue_size = sum(m.query_queue_size for m in recent_metrics) / len(recent_metrics)
        
        # Scale up conditions
        if (avg_cpu > self.scaling_thresholds['cpu_high'] or 
            avg_memory > self.scaling_thresholds['memory_high'] or
            avg_queue_size > self.scaling_thresholds['queue_high']):
            
            return {
                'action': 'scale_up',
                'reason': 'high_resource_usage',
                'metrics': {
                    'avg_cpu': avg_cpu,
                    'avg_memory': avg_memory,
                    'avg_queue_size': avg_queue_size
                }
            }
        
        # Scale down conditions
        elif (avg_cpu < self.scaling_thresholds['cpu_low'] and 
              avg_memory < self.scaling_thresholds['memory_low'] and
              avg_queue_size < 10):
            
            return {
                'action': 'scale_down',
                'reason': 'low_resource_usage',
                'metrics': {
                    'avg_cpu': avg_cpu,
                    'avg_memory': avg_memory,
                    'avg_queue_size': avg_queue_size
                }
            }
        
        return {'action': 'none', 'reason': 'metrics_within_thresholds'}
    
    async def _execute_scaling_action(self, scaling_decision: Dict[str, Any]):
        """Execute scaling actions"""
        
        action = scaling_decision['action']
        
        if action == 'scale_up':
            await self._scale_up_resources()
        elif action == 'scale_down':
            await self._scale_down_resources()
        
        # Log scaling action
        self.scaling_actions.append({
            'timestamp': datetime.utcnow(),
            'action': action,
            'reason': scaling_decision['reason'],
            'metrics': scaling_decision.get('metrics', {})
        })
        
        logger.info(f"Executed scaling action: {action} - {scaling_decision['reason']}")
    
    async def _scale_up_resources(self):
        """Scale up system resources"""
        
        # Increase connection pool sizes
        if hasattr(db_optimizer, 'connection_pool'):
            current_max = db_optimizer.connection_pool.get_max_size()
            new_max = min(current_max * 1.5, 100)  # Cap at 100
            await db_optimizer.connection_pool.set_max_size(int(new_max))
        
        # Increase cache sizes
        for cache_type, config in cache_manager.cache_configs.items():
            config.max_size = int(config.max_size * 1.2)
        
        # Increase worker threads for CPU-intensive tasks
        if hasattr(vector_optimizer, 'thread_pool'):
            vector_optimizer.thread_pool._max_workers = min(
                vector_optimizer.thread_pool._max_workers + 2, 8
            )
    
    async def _scale_down_resources(self):
        """Scale down system resources"""
        
        # Decrease connection pool sizes
        if hasattr(db_optimizer, 'connection_pool'):
            current_max = db_optimizer.connection_pool.get_max_size()
            new_max = max(current_max * 0.8, 10)  # Minimum 10
            await db_optimizer.connection_pool.set_max_size(int(new_max))
        
        # Decrease cache sizes
        for cache_type, config in cache_manager.cache_configs.items():
            config.max_size = max(int(config.max_size * 0.8), 100)  # Minimum 100
    
    async def _get_active_connections(self) -> int:
        """Get current active database connections"""
        
        try:
            if hasattr(db_optimizer, 'connection_pool'):
                return db_optimizer.connection_pool.get_size() - db_optimizer.connection_pool.get_idle_size()
        except:
            pass
        return 0
    
    async def _get_query_queue_size(self) -> int:
        """Get current query queue size"""
        
        # This would integrate with your query queue monitoring
        return 0

# Performance reporting and alerts
class PerformanceReporter:
    """Generate performance reports and alerts"""
    
    def __init__(self, auto_scaler: AutoScalingManager):
        self.auto_scaler = auto_scaler
        
    async def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        
        current_time = datetime.utcnow()
        
        # System metrics summary
        recent_metrics = self.auto_scaler.metrics_history[-60:]  # Last 30 minutes
        if recent_metrics:
            avg_cpu = sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_usage for m in recent_metrics) / len(recent_metrics)
            max_queue_size = max(m.query_queue_size for m in recent_metrics)
        else:
            avg_cpu = avg_memory = max_queue_size = 0
        
        # Cache performance
        cache_metrics = await cache_manager.get_cache_statistics()
        
        # Database performance
        db_metrics = await db_optimizer.collect_performance_metrics() if db_optimizer else {}
        
        # Vector search performance
        vector_metrics = vector_monitor.get_performance_summary()
        
        # Recent scaling actions
        recent_scaling = [
            action for action in self.auto_scaler.scaling_actions
            if action['timestamp'] > current_time - timedelta(hours=24)
        ]
        
        return {
            'report_timestamp': current_time,
            'system_performance': {
                'avg_cpu_usage': avg_cpu,
                'avg_memory_usage': avg_memory,
                'max_queue_size': max_queue_size,
                'status': 'healthy' if avg_cpu < 70 and avg_memory < 80 else 'warning'
            },
            'cache_performance': cache_metrics,
            'database_performance': db_metrics,
            'vector_search_performance': vector_metrics,
            'scaling_actions_24h': recent_scaling,
            'recommendations': await self._generate_recommendations()
        }
    
    async def _generate_recommendations(self) -> List[str]:
        """Generate performance optimization recommendations"""
        
        recommendations = []
        
        # Check recent metrics for patterns
        if len(self.auto_scaler.metrics_history) > 10:
            recent_cpu = [m.cpu_usage for m in self.auto_scaler.metrics_history[-10:]]
            if sum(recent_cpu) / len(recent_cpu) > 80:
                recommendations.append("Consider scaling up CPU resources or optimizing query performance")
        
        # Check cache hit rates
        cache_stats = await cache_manager.get_cache_statistics()
        for cache_type, stats in cache_stats.items():
            if stats.get('hit_rate', 1.0) < 0.7:
                recommendations.append(f"Low cache hit rate for {cache_type} - consider increasing TTL or cache size")
        
        return recommendations

# Global instances
auto_scaler = AutoScalingManager()
performance_reporter = PerformanceReporter(auto_scaler)
```

## Production Performance Tuning

### 6. Configuration Templates

```python
# Production configuration for high performance
PRODUCTION_CONFIG = {
    "database": {
        "max_connections": 50,
        "min_connections": 10,
        "connection_timeout": 30,
        "query_timeout": 45,
        "prepared_statements": True,
        "connection_pooling": True
    },
    
    "cache": {
        "redis_max_memory": "4gb",
        "redis_eviction_policy": "allkeys-lru",
        "local_cache_size": 1000,
        "cache_ttl": {
            "user_permissions": 900,
            "document_metadata": 3600,
            "authorization_decisions": 300,
            "query_results": 1800
        }
    },
    
    "vector_search": {
        "faiss_index_type": "IVFFlat",
        "hnsw_m": 16,
        "hnsw_ef_construction": 200,
        "hnsw_ef_search": 100,
        "batch_size": 1000,
        "parallel_search": True
    },
    
    "query_optimization": {
        "max_concurrent_queries": 20,
        "query_timeout": 60,
        "result_limit": 50,
        "enable_query_cache": True,
        "parallel_data_fetch": True
    },
    
    "scaling": {
        "auto_scaling_enabled": True,
        "cpu_threshold_high": 80,
        "cpu_threshold_low": 30,
        "memory_threshold_high": 85,
        "memory_threshold_low": 40,
        "scale_up_cooldown": 300,
        "scale_down_cooldown": 600
    }
}
```

This comprehensive performance optimization framework ensures that the ERP RBAC-RAG system can handle enterprise-scale workloads while maintaining security, compliance, and user experience requirements. The next documents will cover compliance frameworks and security patterns.