"""Demo profiles -- pre-configured personas for hackathon judges.

Separated from demo.py for maintainability.
"""

from __future__ import annotations

from typing import Any

DEMO_PROFILES: dict[str, dict[str, Any]] = {
    "teacher-ms-johnson": {
        "id": "demo-teacher-ms-johnson",
        "name": "Ms. Sarah Johnson",
        "role": "teacher",
        "school": "Lincoln Elementary School",
        "subject": "Science & Math",
        "grade": "5th Grade",
        "location": "Austin, TX, USA",
        "avatar_emoji": "\U0001f469\u200d\U0001f3eb",
        "description": (
            "5th grade Science teacher, 12 years experience, "
            "focused on inclusive STEM education"
        ),
    },
    "student-alex-tea": {
        "id": "demo-student-alex-tea",
        "name": "Alex Rivera",
        "role": "student",
        "grade": "5th Grade",
        "accessibility": "tea",
        "accessibility_label": "Autism Spectrum (ASD)",
        "avatar_emoji": "\U0001f9d2",
        "description": (
            "Excels in math, needs structured visual schedules "
            "and predictable routines"
        ),
    },
    "student-maya-adhd": {
        "id": "demo-student-maya-adhd",
        "name": "Maya Chen",
        "role": "student",
        "grade": "5th Grade",
        "accessibility": "tdah",
        "accessibility_label": "ADHD",
        "avatar_emoji": "\U0001f467",
        "description": (
            "Creative and energetic, benefits from focus mode "
            "and chunked activities"
        ),
    },
    "student-lucas-dyslexia": {
        "id": "demo-student-lucas-dyslexia",
        "name": "Lucas Thompson",
        "role": "student",
        "grade": "5th Grade",
        "accessibility": "dyslexia",
        "accessibility_label": "Dyslexia",
        "avatar_emoji": "\U0001f466",
        "description": (
            "Strong verbal skills, needs large print and "
            "bionic reading support"
        ),
    },
    "student-sofia-hearing": {
        "id": "demo-student-sofia-hearing",
        "name": "Sofia Martinez",
        "role": "student",
        "grade": "5th Grade",
        "accessibility": "hearing",
        "accessibility_label": "Hearing Impairment",
        "avatar_emoji": "\U0001f467",
        "description": (
            "Uses sign language, excels with visual content "
            "and captions"
        ),
    },
    "parent-david": {
        "id": "demo-parent-david",
        "name": "David Rivera",
        "role": "parent",
        "child": "Alex Rivera",
        "avatar_emoji": "\U0001f468",
        "description": "Alex's father, actively involved in education planning",
    },
    "admin-principal": {
        "id": "demo-admin-principal",
        "name": "Dr. Robert Williams",
        "role": "school_admin",
        "school": "Lincoln Elementary School",
        "avatar_emoji": "\U0001f3eb",
        "description": "School principal, oversees all teachers and curriculum",
    },
    "admin-super": {
        "id": "demo-admin-super",
        "name": "System Administrator",
        "role": "super_admin",
        "avatar_emoji": "\U0001f6e1\ufe0f",
        "description": "Platform administrator with full system access",
    },
}
