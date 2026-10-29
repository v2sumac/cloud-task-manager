import os
import time

from flask import Flask, jsonify, request
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://taskapp:taskapp@localhost:5432/taskdb"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

VALID_STATUSES = ("Pending", "In Progress", "Completed")


def initialize_database():
    for attempt in range(30):
        try:
            with engine.begin() as db:
                db.execute(text("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id SERIAL PRIMARY KEY,
                        project_id INTEGER NOT NULL,
                        title VARCHAR(200) NOT NULL,
                        status VARCHAR(20) NOT NULL DEFAULT 'Pending'
                    )
                """))
            return
        except SQLAlchemyError:
            if attempt == 29:
                raise
            time.sleep(2)


@app.get("/health")
def health():
    return jsonify({
        "status": "healthy",
        "service": "task-service"
    })


@app.get("/api/tasks")
def get_tasks():
    project_id = request.args.get("project_id", type=int)

    with engine.connect() as db:
        if project_id is None:
            rows = db.execute(text("""
                SELECT id, project_id, title, status
                FROM tasks
                ORDER BY id
            """)).mappings().all()
        else:
            rows = db.execute(text("""
                SELECT id, project_id, title, status
                FROM tasks
                WHERE project_id = :project_id
                ORDER BY id
            """), {"project_id": project_id}).mappings().all()

    return jsonify([dict(row) for row in rows])


@app.post("/api/tasks")
def create_task():
    data = request.get_json(silent=True) or {}

    title = str(data.get("title", "")).strip()
    project_id = data.get("project_id")

    if not title:
        return jsonify({"error": "Task title is required"}), 400

    try:
        project_id = int(project_id)
        if project_id <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({"error": "Valid project_id is required"}), 400

    with engine.begin() as db:
        row = db.execute(text("""
            INSERT INTO tasks (project_id, title)
            VALUES (:project_id, :title)
            RETURNING id, project_id, title, status
        """), {
            "project_id": project_id,
            "title": title
        }).mappings().one()

    return jsonify(dict(row)), 201


@app.put("/api/tasks/<int:task_id>")
def update_task(task_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status")

    if status not in VALID_STATUSES:
        return jsonify({
            "error": "Status must be Pending, In Progress, or Completed"
        }), 400

    with engine.begin() as db:
        row = db.execute(text("""
            UPDATE tasks
            SET status = :status
            WHERE id = :task_id
            RETURNING id, project_id, title, status
        """), {
            "status": status,
            "task_id": task_id
        }).mappings().first()

    if row is None:
        return jsonify({"error": "Task not found"}), 404

    return jsonify(dict(row))


@app.delete("/api/tasks/<int:task_id>")
def delete_task(task_id):
    with engine.begin() as db:
        row = db.execute(text("""
            DELETE FROM tasks
            WHERE id = :task_id
            RETURNING id
        """), {"task_id": task_id}).mappings().first()

    if row is None:
        return jsonify({"error": "Task not found"}), 404

    return jsonify({"message": "Task deleted successfully"})


initialize_database()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
