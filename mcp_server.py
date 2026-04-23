import os
import httpx
from fastmcp import FastMCP
from fastmcp import tool
from pydantic import Field

# ─── CONFIGURATION ──────────────────────────────────────────────────
# Ensure 'schoolms' matches your Django container name in docker-compose
DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://schoolms:8000/api")

mcp = FastMCP("School Management System")

async def api_call(method: str, endpoint: str, data: dict = None):
    # Ensure no leading/trailing slashes on the endpoint string
    clean_endpoint = endpoint.strip("/")
    
    # Construct URL WITHOUT the trailing slash
    url = f"http://schoolms:8000/api/{clean_endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(method, url, json=data, timeout=10.0)
            
            # If we get a 404, return a helpful error for the Brain
            if response.status_code == 404:
                return {"error": f"404 Not Found at {url}. Ensure the route exists in Django."}
            
            # Return the JSON if successful
            return response.json()
        except Exception as e:
            return {"error": f"Connection failed: {str(e)}"}
        
# ─── HELPER FORMATTER ────────────────────────────────────
def format_response(title: str, data: list):
    if not data:
        return {"text": f"No {title} found.", "data": []}

    output = f"{title}:\n"
    for item in data:
        line = " - " + ", ".join(f"{k}: {v}" for k, v in item.items())
        output += line + "\n"

    return {
        "text": output,
        "data": data
    } 
# ─── SUBJECT TOOLS ──────────────────────────────────────────────────

@mcp.tool()
async def list_subjects():
    """
    Retrieve all academic subjects.

    Use this tool when:
    - The user asks to see, list, view, or check subjects
    - The user wants to know what subjects exist

    Guidelines:
    - Always call this tool instead of guessing subject names
    - Use this before creating subjects to avoid duplicates
    - If the user asks "what subjects are available?", use this tool

    Examples:
    - "list subjects"
    - "show all subjects"
    - "what subjects do we have?"
    """

    data = await api_call("GET", "/subjects")
    return format_response("Subjects", data)

@mcp.tool()
async def create_subjects(names: list[str]):
    """
    Create one or more subjects.

    Use this tool when the user provides multiple subjects.

    Guidelines for the model:
    - Extract all subject names from the user input.
    - Pass them as a list of strings.
    - Normalize names (e.g., "physics" → "Physics").
    - Avoid duplicates in the list.
    """

    if not names or not isinstance(names, list):
        return {
            "text": "No valid subject names provided.",
            "data": None,
            "error": "Invalid input"
        }

    created = []
    errors = []
    seen = set()

    for name in names:
        if not name or not isinstance(name, str):
            continue

        # Normalize
        clean_name = name.strip().title()

        # Skip empty after cleaning
        if not clean_name:
            continue

        # Deduplicate within request
        if clean_name.lower() in seen:
            continue
        seen.add(clean_name.lower())

        try:
            data = await api_call(
                "POST",
                "/subjects",
                {"name": clean_name}
            )

            created.append({
                "name": clean_name,
                "id": data.get("id") if isinstance(data, dict) else None
            })

        except Exception as e:
            errors.append({
                "name": clean_name,
                "error": str(e)
            })

    # Build response message
    if created and not errors:
        message = f"Successfully created subjects: {', '.join([c['name'] for c in created])}."
    elif created and errors:
        message = (
            f"Partially created subjects: {', '.join([c['name'] for c in created])}. "
            f"Some failed."
        )
    else:
        message = "No subjects were created."

    return {
        "text": message,
        "data": {
            "created": created,
            "errors": errors,
            "total_requested": len(names),
            "total_created": len(created)
        }
    }
# ─── GRADE TOOLS ─────────────────────────────────────────

@mcp.tool()
async def list_grades():
    """List all school grades."""
    data = await api_call("GET", "/grades")
    return format_response("Grades", data)


@mcp.tool()
async def get_grade_details(grade_id: int):
    """Get grade details by ID."""
    data = await api_call("GET", f"/grades/{grade_id}")
    return {
        "text": f"Details for grade {grade_id}",
        "data": data
    }


@mcp.tool()
async def get_grade_curriculum(grade_id: int):
    """Get full curriculum of a grade."""
    data = await api_call("GET", f"/grades/{grade_id}/curriculum")
    return {
        "text": f"Curriculum for grade {grade_id}",
        "data": data
    }


# ─── STUDENT TOOLS ───────────────────────────────────────

@mcp.tool()
async def list_students():
    """List all students."""
    data = await api_call("GET", "/students")
    return format_response("Students", data)


@mcp.tool()
async def enroll_student(name: str, age: int, grade_id: int):
    """Enroll a new student."""
    payload = {
        "name": name,
        "age": age,
        "grade_id": grade_id  # ✅ FIXED
    }
    data = await api_call("POST", "/students", payload)

    return {
        "text": f"Student '{name}' enrolled successfully in grade {grade_id}.",
        "data": data
    }


# ─── TEACHER TOOLS ───────────────────────────────────────

@mcp.tool()
async def list_teachers():
    """Retrieve all teachers."""
    data = await api_call("GET", "/teachers")
    return format_response("Teachers", data)


@mcp.tool()
async def create_teacher(name: str, email: str):
    """Create a teacher."""
    data = await api_call("POST", "/teachers", {
        "name": name,
        "email": email
    })

    return {
        "text": f"Teacher '{name}' created successfully.",
        "data": data
    }


@mcp.tool()
async def get_teacher_assignments(teacher_id: int):
    """Get teacher assignments."""
    data = await api_call("GET", f"/teachers/{teacher_id}/assignments")

    return {
        "text": f"Assignments for teacher {teacher_id}",
        "data": data
    }


# ─── ASSIGNMENT TOOLS ────────────────────────────────────


@tool
async def assign_teacher_to_course(
    grade_id: int = Field(..., description="Grade ID (e.g. 1, 2, 3)"),
    subject_id: int = Field(..., description="Subject ID (e.g. 10 for Math)"),
    teacher_id: int = Field(..., description="Teacher ID (e.g. 5)"),
):
    print("TOOL INPUT:", grade_id, subject_id, teacher_id)
    """
    Assign a teacher to a subject in a grade.

    RULES FOR LLM:
    - Always provide ALL THREE fields: grade_id, subject_id, teacher_id
    - Never call this tool with missing or empty arguments
    - Convert names to IDs before calling this tool
    """

    payload = {
        "grade_id": grade_id,
        "subject_id": subject_id,
        "teacher_id": teacher_id
    }

    data = await api_call("POST", "/assignments", payload)

    return {
        "text": (
            f"Teacher {teacher_id} assigned to "
            f"subject {subject_id} in grade {grade_id}."
        ),
        "data": data
    }

# ─── RUN MCP SERVER ──────────────────────────────────────

if __name__ == "__main__":
    mcp.run()