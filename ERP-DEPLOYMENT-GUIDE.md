# ERP Deployment Guide for RBAC-RAG Systems

## 1. Introduction

This guide provides detailed instructions for deploying the ERP RBAC-RAG system to various environments, including development, staging, and production. It covers deployment using Docker Compose and provides a roadmap for migrating to a Kubernetes-based deployment.

## 2. Prerequisites

- **Docker and Docker Compose**: Installed on the deployment server.
- **Git**: For cloning the repository.
- **kubectl and Helm**: For Kubernetes deployment.
- **Cloud Provider Account**: (Optional) For deploying to a cloud environment (e.g., AWS, GCP, Azure).

## 3. Deployment Environments

### 3.1. Development Environment
- Use the `docker-compose.yml` file for a local development setup.
- This environment is intended for developers to build and test new features.

### 3.2. Staging Environment
- A replica of the production environment.
- Used for testing new releases before deploying to production.

### 3.3. Production Environment
- The live environment for end-users.
- Requires high availability, security, and monitoring.

## 4. Deployment with Docker Compose

### 4.1. Clone the Repository
```bash
git clone <repository_url>
cd rbac-rag-system
```

### 4.2. Configure Environment Variables
- Create a `.env` file in the root directory and populate it with the necessary environment variables for the target environment.

### 4.3. Build and Run the Application
```bash
docker-compose -f docker/docker-compose.prod.yml build
docker-compose -f docker/docker-compose.prod.yml up -d
```

### 4.4. Run Database Migrations
```bash
docker-compose -f docker/docker-compose.prod.yml run backend alembic upgrade head
```

## 5. Kubernetes Deployment (Advanced)

For large-scale deployments, it is recommended to use Kubernetes for better scalability, and manageability.

### 5.1. Create Kubernetes Manifests
- Create Kubernetes manifest files (e.g., `deployment.yaml`, `service.yaml`, `ingress.yaml`) for each service (backend, frontend, cerbos, postgres, redis).
- Use Helm charts to package and manage the Kubernetes applications.

### 5.2. Deploy to Kubernetes Cluster
```bash
kubectl apply -f <path_to_manifests>/
# or with Helm
helm install rbac-rag ./helm-charts/rbac-rag
```

## 6. CI/CD Pipeline

- Set up a CI/CD pipeline using tools like Jenkins, GitLab CI, or GitHub Actions.
- The pipeline should automate the following steps:
    1.  **Build**: Build the Docker images.
    2.  **Test**: Run unit and integration tests.
    3.  **Push**: Push the Docker images to a container registry (e.g., Docker Hub, ECR, GCR).
    4.  **Deploy**: Deploy the new version to the staging/production environment.

## 7. Monitoring and Logging

- **Prometheus and Grafana**: Use for monitoring application metrics and performance.
- **ELK Stack (Elasticsearch, Logstash, Kibana)** or **Loki**: For centralized logging and analysis.

## 8. Backup and Restore

- **Database**: Implement a regular backup schedule for the PostgreSQL database.
- **Vector Database**: Back up the vector database data.
- **Cerbos Policies**: Version control the Cerbos policies in a Git repository.

## 9. Security Considerations

- **Secrets Management**: Use a secrets management tool like HashiCorp Vault or AWS Secrets Manager to store sensitive information.
- **Network Policies**: Configure network policies to restrict traffic between pods in the Kubernetes cluster.
- **Image Scanning**: Integrate an image scanning tool into the CI/CD pipeline to scan for vulnerabilities in Docker images.
