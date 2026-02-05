"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
import json
from datetime import datetime, timedelta
from typing import Optional

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Session storage (simple in-memory storage)
sessions = {}

# Load teacher credentials from JSON
def load_teachers():
    teachers_file = os.path.join(Path(__file__).parent, "teachers.json")
    try:
        with open(teachers_file, 'r') as f:
            data = json.load(f)
            return {t['username']: t['password'] for t in data['teachers']}
    except FileNotFoundError:
        return {}

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/login")
def login(request: Request, username: str, password: str):
    """Authenticate a teacher and create a session"""
    teachers = load_teachers()
    
    if username not in teachers or teachers[username] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create session token
    token = f"{username}_{datetime.now().timestamp()}"
    sessions[token] = {
        "username": username,
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(hours=8)
    }
    
    return {"token": token, "username": username, "message": "Login successful"}


@app.post("/logout")
def logout(request: Request, token: str):
    """Logout a teacher and invalidate session"""
    if token in sessions:
        del sessions[token]
    return {"message": "Logout successful"}


@app.get("/me")
def get_current_user(request: Request, token: Optional[str] = None):
    """Get current logged-in user information"""
    if not token or token not in sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = sessions[token]
    if datetime.now() > session["expires_at"]:
        del sessions[token]
        raise HTTPException(status_code=401, detail="Session expired")
    
    return {"username": session["username"], "role": "teacher"}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, token: Optional[str] = None):
    """Sign up a student for an activity (teacher only)"""
    # Validate authentication
    if not token or token not in sessions:
        raise HTTPException(status_code=401, detail="Authentication required. Only teachers can signup students.")
    
    # Validate session not expired
    session = sessions[token]
    if datetime.now() > session["expires_at"]:
        del sessions[token]
        raise HTTPException(status_code=401, detail="Session expired")
    
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, token: Optional[str] = None):
    """Unregister a student from an activity (teacher only)"""
    # Validate authentication
    if not token or token not in sessions:
        raise HTTPException(status_code=401, detail="Authentication required. Only teachers can unregister students.")
    
    # Validate session not expired
    session = sessions[token]
    if datetime.now() > session["expires_at"]:
        del sessions[token]
        raise HTTPException(status_code=401, detail="Session expired")
    
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
