import os
import time

import requests
from flask import Flask, jsonify, render_template, request, Response
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://taskapp:taskapp@localhost:5432/taskdb"
)

TASK_SERVICE_URL = os.getenv(
    "TASK_SERVICE_URL",
    "http://localhost:5001"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def initialize_database():
    for attempt in range(30):
        try:
            with engine.begin() as db:
                db.execute(text("""
                    CREATE TABLE IF NOT EXISTS projects (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(200) NOT NULL,
                        description TEXT DEFAULT ''
                    )
                """))
            return
        except SQLAlchemyError:
            if attempt == 29:
                raise
            time.sleep(2)


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify({"status": "healthy", "service": "project-service"})


@app.get("/api/projects")
def get_projects():
    with engine.connect() as db:
        rows = db.execute(
            text("SELECT id, name, description FROM projects ORDER BY id")
        ).mappings().all()

    return jsonify([dict(row) for row in rows])


@app.post("/api/projects")
def create_project():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    description = str(data.get("description", "")).strip()

    if not name:
        return jsonify({"error": "Project name is required"}), 400

    with engine.begin() as db:
        row = db.execute(
            text("""
                INSERT INTO projects (name, description)
                VALUES (:name, :description)
                RETURNING id, name, description
            """),
            {"name": name, "description": description}
        ).mappings().one()

    return jsonify(dict(row)), 201


@app.get("/api/projects/<int:project_id>/summary")
def project_summary(project_id):
    with engine.connect() as db:
        project = db.execute(
            text("""
                SELECT id, name, description
                FROM projects
                WHERE id = :id
            """),
            {"id": project_id}
        ).mappings().first()

    if project is None:
        return jsonify({"error": "Project not found"}), 404

    try:
        response = requests.get(
            f"{TASK_SERVICE_URL}/api/tasks",
            params={"project_id": project_id},
            timeout=5
        )
        response.raise_for_status()
        tasks = response.json()
    except requests.RequestException:
        return jsonify({"error": "Task Service unavailable"}), 503

    return jsonify({
        "project": dict(project),
        "total_tasks": len(tasks),
        "completed_tasks": sum(
            task["status"] == "Completed" for task in tasks
        )
    })


@app.route("/tasks-api/<path:subpath>", methods=["GET", "POST", "PUT", "DELETE"])
def task_proxy(subpath):
    try:
        response = requests.request(
            method=request.method,
            url=f"{TASK_SERVICE_URL}/api/{subpath}",
            params=request.args,
            json=request.get_json(silent=True),
            timeout=10
        )

        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get(
                "Content-Type", "application/json"
            )
        )
    except requests.RequestException:
        return jsonify({"error": "Task Service unavailable"}), 503


initialize_database()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
