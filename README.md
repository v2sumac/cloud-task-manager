# Cloud Task Manager

A cloud-native task management application developed using Python Flask microservices, PostgreSQL, Docker, and Kubernetes.

This is a student project that demonstrates microservices architecture, RESTful communication, containerization, independent horizontal scaling, and persistent database storage.

## 1. Project Overview

Cloud Task Manager allows users to create projects, manage tasks, update task statuses, and monitor project progress through a browser-based interface.

The application consists of two independently deployable microservices:

- **Project Service:** Manages projects, serves the web interface, and communicates with the Task Service.
- **Task Service:** Manages tasks, including creation, retrieval, status updates, and deletion.

Both services communicate with a PostgreSQL database running inside Kubernetes.

## 2. Technologies

| Technology | Purpose |
|---|---|
| Python | Backend development |
| Flask | REST API implementation |
| PostgreSQL | Persistent relational database |
| SQLAlchemy | Database interaction |
| Docker | Containerization |
| Docker Hub | Container image registry |
| Kubernetes | Container orchestration |
| Minikube | Local Kubernetes cluster |
| HTML, CSS, JavaScript | Browser-based user interface |
| Git and GitHub | Version control and source hosting |

## 3. Architecture

```text
                    Web Browser
                         |
                         v
                Project Service
                 Flask REST API
                  Port 5000
                         |
              +----------+----------+
              |                     |
              v                     v
       PostgreSQL             Task Service
        Port 5432              Flask REST API
                                Port 5001
                                    |
                                    v
                                PostgreSQL
                                 Port 5432
```

The Project Service provides the browser interface and project-related REST endpoints.

The Task Service provides task-related REST endpoints.

Kubernetes Services provide stable internal networking between the containers.

## 4. Project Structure

```text
cloud-task-manager/
|
|-- project-service/
|   |-- app.py
|   |-- Dockerfile
|   |-- requirements.txt
|   `-- templates/
|       `-- index.html
|
|-- task-service/
|   |-- app.py
|   |-- Dockerfile
|   `-- requirements.txt
|
|-- kubernetes/
|   `-- app.yaml
|
|-- .gitignore
`-- README.md
```

## 5. REST API

### Project Service

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Display the web interface |
| GET | `/health` | Service health check |
| GET | `/api/projects` | Retrieve projects |
| POST | `/api/projects` | Create a project |
| GET | `/api/projects/<id>/summary` | Retrieve a project summary |

### Task Service

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Service health check |
| GET | `/api/tasks` | Retrieve tasks |
| POST | `/api/tasks` | Create a task |
| PUT | `/api/tasks/<id>` | Update a task |
| DELETE | `/api/tasks/<id>` | Delete a task |

The Project Service also exposes a `/tasks-api/` reverse-proxy route for browser requests to the Task Service.

## 6. Docker Images

The application uses two custom Docker images published to Docker Hub.

**Project Service:**

`v2sumac/cloud-project-service:1.2`

**Task Service:**

`v2sumac/cloud-task-service:1.2`

Build the images:

```bash
docker build -t v2sumac/cloud-project-service:1.2 ./project-service
docker build -t v2sumac/cloud-task-service:1.2 ./task-service
```

Push the images:

```bash
docker push v2sumac/cloud-project-service:1.2
docker push v2sumac/cloud-task-service:1.2
```

## 7. Kubernetes Deployment

The Kubernetes configuration is located in:

`kubernetes/app.yaml`

It defines:

- ConfigMap for application configuration
- PersistentVolumeClaim for PostgreSQL
- PostgreSQL Deployment and Service
- Project Service Deployment and Service
- Task Service Deployment and Service

### Prerequisites

- Docker Desktop
- Minikube
- kubectl
- Access to the published Docker images

### Start Minikube

```bash
minikube start --driver=docker --cpus=2 --memory=3072
```

### Create the database Secret

The application expects a Kubernetes Secret named `task-db-secret` containing the key `POSTGRES_PASSWORD`.

Create it before deploying:

```bash
kubectl create secret generic task-db-secret \
  --from-literal=POSTGRES_PASSWORD='REPLACE_WITH_A_STRONG_PASSWORD'
```

Replace the placeholder with a suitable password.

The actual password must not be committed to Git.

### Deploy the application

```bash
kubectl apply -f kubernetes/app.yaml
```

Check the deployment:

```bash
kubectl get deployments
kubectl get pods
kubectl get services
```

### Access the browser interface

```bash
kubectl port-forward svc/project-service 8080:5000
```

Open the application in a browser at `http://localhost:8080`.

## 8. Horizontal Scaling

The Project Service and Task Service are deployed independently.

Each microservice can be scaled without changing the replica count of the other service.

Example:

```bash
kubectl scale deployment/project-service --replicas=2
kubectl scale deployment/task-service --replicas=2
```

Verify:

```bash
kubectl get deployments
kubectl get pods -o wide
```

During testing, both services successfully ran with two replicas.

This demonstrates independent horizontal scaling.

## 9. Persistent Storage

PostgreSQL uses a Kubernetes PersistentVolumeClaim named `postgres-data`.

The volume has:

- Capacity: 1 GiB
- Access mode: ReadWriteOnce
- Storage class: standard

Verify the volume:

```bash
kubectl get pvc,pv
```

The persistent volume separates database files from the temporary container filesystem.

A PostgreSQL Pod can be replaced while retaining the existing volume.

To test persistence:

1. Create a project and task in the browser.
2. Verify the data appears.
3. Delete the PostgreSQL Pod:

```bash
kubectl delete pod -l app=postgres
```

4. Wait for Kubernetes to create a replacement.
5. Refresh the browser and verify the saved data remains.

**Note:** Do not delete the PersistentVolumeClaim during this test.

## 10. Cloud-Native Design Principles

### Microservices architecture

Project management and task management are implemented as separate services.

### Containerization

Each microservice has its own Dockerfile and Docker image.

### Independent deployment

The Project Service and Task Service can be updated separately.

### Horizontal scalability

Kubernetes can run multiple replicas of either microservice.

### Service discovery

Kubernetes Services provide stable internal names for communication between application components.

### Persistent storage

PostgreSQL stores application data on a persistent volume.

### Health monitoring

Kubernetes readiness probes monitor whether the services are ready to receive requests.

## 11. Benefits

The architecture provides several advantages:

- Independent scaling of application services
- Separation of project and task responsibilities
- Reproducible deployments using Docker images
- Automated Pod replacement through Kubernetes
- Persistent database storage
- Easier maintenance of individual services

## 12. Challenges

The implementation also introduces challenges:

- Increased deployment complexity compared with a monolithic application
- Communication dependencies between microservices
- Database availability affecting both services
- Container image version management
- Kubernetes configuration and troubleshooting
- Additional resource consumption when scaling

During development, container image issues and database connection configuration required troubleshooting.

## 13. Security Considerations

The application uses a Kubernetes Secret to provide the PostgreSQL password rather than storing the password directly in the deployment YAML.

The Docker containers use a non-root application user.

Additional security improvements recommended for production include:

- User authentication and authorization
- HTTPS/TLS
- Kubernetes NetworkPolicies
- Database access restrictions
- Resource limits and requests
- Secret rotation and external secret management
- Automated vulnerability scanning
- Database backup and recovery procedures

The current implementation is intended as a local educational demonstration rather than a production-ready system.

## 14. Monitoring and Logs

Kubernetes provides commands for inspecting deployments and application logs.

```bash
kubectl get pods
kubectl get deployments
kubectl logs deployment/project-service
kubectl logs deployment/task-service
kubectl logs deployment/postgres
```

These commands help identify runtime errors and investigate application behavior.

## 15. Conclusion

Cloud Task Manager demonstrates the deployment of a browser-based application using two Flask microservices, PostgreSQL, Docker, and Kubernetes.

The implementation supports project and task management, independent horizontal scaling, service discovery, health monitoring, and persistent database storage.

The project illustrates both the benefits and operational challenges of cloud-native software development.