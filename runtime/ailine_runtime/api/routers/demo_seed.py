"""Demo seed data -- creates sample materials, plans, progress, and tutor sessions.

Separated from demo.py for maintainability. Contains all seed logic
for populating the demo teacher's dashboard.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog

from .demo_profiles import DEMO_PROFILES

logger = structlog.get_logger("ailine.api.demo.seed")


def seed_demo_data_for_teacher() -> dict[str, Any]:
    """Populate stores with sample data for the demo teacher profile.

    Idempotent: returns existing data if already seeded.
    Returns a dict with status, teacher_id, created counts, and IDs.
    """
    from ...shared.review_store import get_review_store as _get_rs

    teacher_id = DEMO_PROFILES["teacher-ms-johnson"]["id"]

    # Idempotency check
    existing_reviews = _get_rs().list_all(teacher_id)
    if existing_reviews:
        logger.info("demo_seed_skipped_already_seeded", teacher_id=teacher_id)
        return {
            "status": "ok",
            "teacher_id": teacher_id,
            "message": "Demo data already seeded. Call POST /demo/reset first to re-seed.",
            "created": {},
            "ids": {},
        }

    from uuid_utils import uuid7

    from ...domain.entities.plan import ReviewStatus
    from ...domain.entities.progress import MasteryLevel
    from ...domain.entities.tutor import (
        LearnerProfile,
        TutorAgentSpec,
        TutorMaterialsScope,
        TutorMessage,
        TutorPersona,
        TutorSession,
    )
    from ...materials.store import add_material
    from ...shared.progress_store import get_progress_store
    from ...shared.review_store import get_review_store
    from ...tutoring.builder import save_tutor_spec
    from ...tutoring.session import save_session

    now = datetime.now(UTC).isoformat()

    created: dict[str, list[str]] = {
        "materials": [],
        "reviews": [],
        "progress": [],
        "tutors": [],
        "sessions": [],
    }

    # -- Materials --
    mat_photosynthesis = add_material(
        teacher_id=teacher_id,
        subject="Science",
        title="Photosynthesis for Visual Learners",
        content=(
            "Photosynthesis is the process by which green plants convert "
            "sunlight, water, and carbon dioxide into glucose and oxygen. "
            "This visual guide uses diagrams and step-by-step illustrations "
            "to help students with autism spectrum disorder understand the "
            "process through structured visual schedules.\n\n"
            "Key concepts: chloroplast, light energy, CO2 + H2O -> C6H12O6 + O2\n\n"
            "Visual schedule:\n"
            "1. Sun sends light to leaf (yellow arrow)\n"
            "2. Roots absorb water (blue arrow up)\n"
            "3. Leaf takes in CO2 (green arrow in)\n"
            "4. Chloroplast makes sugar (star symbol)\n"
            "5. Leaf releases O2 (white arrow out)"
        ),
        tags=["science", "photosynthesis", "visual", "tea", "5th-grade"],
        created_at=now,
    )
    created["materials"].append(mat_photosynthesis.material_id)

    mat_fractions = add_material(
        teacher_id=teacher_id,
        subject="Math",
        title="Fractions & Decimals Activity Pack",
        content=(
            "Interactive fraction and decimal conversion activities "
            "designed for students with ADHD. Each activity is chunked "
            "into 5-minute segments with built-in movement breaks.\n\n"
            "Activity 1: Pizza Fractions (5 min)\n"
            "- Cut paper pizza into equal slices\n"
            "- Label each slice as a fraction\n"
            "- MOVEMENT BREAK: Stand and stretch\n\n"
            "Activity 2: Decimal Number Line (5 min)\n"
            "- Walk along a number line on the floor\n"
            "- Place decimal cards at correct positions\n"
            "- MOVEMENT BREAK: Jump to your favorite number"
        ),
        tags=["math", "fractions", "decimals", "adhd", "5th-grade"],
        created_at=now,
    )
    created["materials"].append(mat_fractions.material_id)

    # -- Plan reviews --
    review_store = get_review_store()

    plan_id_photo = f"demo-plan-photosynthesis-{uuid7()}"
    review_store.create_review(plan_id_photo, teacher_id)
    review_store.update_review(
        plan_id_photo,
        ReviewStatus.APPROVED,
        notes="Excellent visual adaptations for Alex (TEA). Ready to use.",
    )
    created["reviews"].append(plan_id_photo)

    plan_id_fractions = f"demo-plan-fractions-{uuid7()}"
    review_store.create_review(plan_id_fractions, teacher_id)
    review_store.update_review(
        plan_id_fractions,
        ReviewStatus.APPROVED,
        notes="Great chunked activities for Maya (ADHD). Movement breaks are key.",
    )
    created["reviews"].append(plan_id_fractions)

    plan_id_water = f"demo-plan-water-cycle-{uuid7()}"
    review_store.create_review(plan_id_water, teacher_id)
    created["reviews"].append(plan_id_water)

    # -- Progress records --
    progress_store = get_progress_store()
    progress_data = [
        ("demo-student-alex-tea", "Alex Rivera", "NGSS.5-LS1-1",
         "Photosynthesis and plant growth", MasteryLevel.DEVELOPING,
         "Responds well to visual schedule format"),
        ("demo-student-alex-tea", "Alex Rivera", "CCSS.MATH.5.NF.A.1",
         "Add and subtract fractions", MasteryLevel.MASTERED,
         "Excellent with fraction manipulatives"),
        ("demo-student-maya-adhd", "Maya Chen", "CCSS.MATH.5.NF.A.1",
         "Add and subtract fractions", MasteryLevel.PROFICIENT,
         "Best with 5-minute chunked activities"),
        ("demo-student-maya-adhd", "Maya Chen", "NGSS.5-ESS2-1",
         "Water cycle and weather", MasteryLevel.DEVELOPING,
         "Engaged when activities include movement"),
        ("demo-student-lucas-dyslexia", "Lucas Thompson", "NGSS.5-LS1-1",
         "Photosynthesis and plant growth", MasteryLevel.PROFICIENT,
         "Excels with audio descriptions and large print"),
        ("demo-student-lucas-dyslexia", "Lucas Thompson", "CCSS.MATH.5.NF.A.1",
         "Add and subtract fractions", MasteryLevel.DEVELOPING,
         "Benefits from bionic reading format"),
        ("demo-student-sofia-hearing", "Sofia Martinez", "NGSS.5-ESS2-1",
         "Water cycle and weather", MasteryLevel.MASTERED,
         "Outstanding with visual diagrams and captions"),
        ("demo-student-sofia-hearing", "Sofia Martinez", "NGSS.5-LS1-1",
         "Photosynthesis and plant growth", MasteryLevel.PROFICIENT,
         "Benefits from Libras-annotated content"),
    ]
    for student_id, name, code, desc, level, notes in progress_data:
        p = progress_store.record_progress(
            teacher_id=teacher_id,
            student_id=student_id,
            student_name=name,
            standard_code=code,
            standard_description=desc,
            mastery_level=level,
            notes=notes,
        )
        created["progress"].append(p.progress_id)

    # -- Tutor specs and sessions --
    tutor_id_alex = f"demo-tutor-alex-{uuid7()}"
    spec_alex = TutorAgentSpec(
        tutor_id=tutor_id_alex, created_at=now, teacher_id=teacher_id,
        subject="Science", grade="5th Grade", standard="NGSS", style="socratic",
        tone="calm, patient, encouraging, uses visual metaphors",
        student_profile=LearnerProfile(
            name="Alex Rivera", age=10,
            needs=["autism", "needs_predictability", "visual_schedule"],
            strengths=["math", "pattern_recognition", "visual_memory"],
            accommodations=["visual_schedule", "structured_routine", "advance_notice"],
            language="en",
        ),
        materials_scope=TutorMaterialsScope(
            teacher_id=teacher_id, subject="Science",
            material_ids=[mat_photosynthesis.material_id],
            tags=["science", "visual", "tea"],
        ),
        persona=TutorPersona(
            system_prompt=(
                "You are a patient science tutor for Alex, a 10-year-old "
                "with autism. Use structured visual metaphors, predictable "
                "patterns, and step-by-step explanations. Always maintain "
                "a calm and encouraging tone."
            ),
            response_contract="json",
            notes=["Visual schedule format preferred", "Avoid sudden topic changes"],
        ),
    )
    save_tutor_spec(spec_alex)
    created["tutors"].append(tutor_id_alex)

    session_alex = TutorSession(
        session_id=f"demo-session-alex-{uuid7()}", tutor_id=tutor_id_alex,
        created_at=now,
        messages=[
            TutorMessage(role="user", content="What is photosynthesis?", created_at=now),
            TutorMessage(
                role="assistant",
                content=(
                    "Great question, Alex! Let me explain with a visual schedule:\n\n"
                    "Step 1: The sun sends light energy to the leaf\n"
                    "Step 2: The roots drink water from the soil\n"
                    "Step 3: The leaf breathes in CO2 from the air\n"
                    "Step 4: Inside the leaf, chloroplasts mix everything together\n"
                    "Step 5: The leaf makes sugar (food!) and releases oxygen\n\n"
                    "Think of it like a recipe: sunlight + water + CO2 = sugar + oxygen!"
                ),
                created_at=now,
            ),
            TutorMessage(role="user", content="Why do plants need sunlight?", created_at=now),
            TutorMessage(
                role="assistant",
                content=(
                    "Plants need sunlight the same way you need food for energy.\n\n"
                    "The sunlight is like a battery that powers the leaf's factory "
                    "(the chloroplast). Without sunlight, the factory cannot run, "
                    "and the plant cannot make its food (sugar).\n\n"
                    "Check for understanding: Can you think of what happens to a "
                    "plant if you put it in a dark closet for a week?"
                ),
                created_at=now,
            ),
        ],
    )
    save_session(session_alex)
    created["sessions"].append(session_alex.session_id)

    tutor_id_maya = f"demo-tutor-maya-{uuid7()}"
    spec_maya = TutorAgentSpec(
        tutor_id=tutor_id_maya, created_at=now, teacher_id=teacher_id,
        subject="Math", grade="5th Grade", standard="CCSS", style="coach",
        tone="energetic, fun, uses movement cues, short sentences",
        student_profile=LearnerProfile(
            name="Maya Chen", age=10,
            needs=["adhd", "needs_movement", "chunked_activities"],
            strengths=["creativity", "verbal_expression", "enthusiasm"],
            accommodations=["focus_mode", "movement_breaks", "timer_visible"],
            language="en",
        ),
        materials_scope=TutorMaterialsScope(
            teacher_id=teacher_id, subject="Math",
            material_ids=[mat_fractions.material_id],
            tags=["math", "fractions", "adhd"],
        ),
        persona=TutorPersona(
            system_prompt=(
                "You are a fun, energetic math tutor for Maya, a 10-year-old "
                "with ADHD. Keep activities short (max 5 minutes), include "
                "movement breaks, and celebrate small wins. Use emojis and "
                "enthusiasm to keep engagement high."
            ),
            response_contract="json",
            notes=["5-minute activity chunks", "Include movement breaks"],
        ),
    )
    save_tutor_spec(spec_maya)
    created["tutors"].append(tutor_id_maya)

    session_maya = TutorSession(
        session_id=f"demo-session-maya-{uuid7()}", tutor_id=tutor_id_maya,
        created_at=now,
        messages=[
            TutorMessage(role="user", content="I don't get fractions", created_at=now),
            TutorMessage(
                role="assistant",
                content=(
                    "No worries, Maya! Let's make fractions FUN!\n\n"
                    "Imagine you have a pizza cut into 4 equal slices. "
                    "If you eat 1 slice, you ate 1/4 of the pizza!\n\n"
                    "Quick activity (2 min): Draw a circle, divide it into "
                    "4 parts, and color 1 part. That's 1/4!\n\n"
                    "Ready? Go! (I'll wait)"
                ),
                created_at=now,
            ),
        ],
    )
    save_session(session_maya)
    created["sessions"].append(session_maya.session_id)

    logger.info(
        "demo_seed_complete",
        teacher_id=teacher_id,
        materials=len(created["materials"]),
        reviews=len(created["reviews"]),
        progress=len(created["progress"]),
        tutors=len(created["tutors"]),
        sessions=len(created["sessions"]),
    )

    return {
        "status": "ok",
        "teacher_id": teacher_id,
        "created": {k: len(v) for k, v in created.items()},
        "ids": created,
    }
