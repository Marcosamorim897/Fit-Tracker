from datetime import datetime, date

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    height_cm = db.Column(db.Float)
    birth_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    measurements = db.relationship(
        "Measurement", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    plans = db.relationship(
        "WorkoutPlan", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    sessions = db.relationship(
        "WorkoutSession", backref="user", lazy=True, cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def age(self):
        if not self.birth_date:
            return None
        today = date.today()
        years = today.year - self.birth_date.year
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            years -= 1
        return years


class Measurement(db.Model):
    __tablename__ = "measurements"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    weight_kg = db.Column(db.Float)
    chest_cm = db.Column(db.Float)
    waist_cm = db.Column(db.Float)
    hips_cm = db.Column(db.Float)
    arm_right_cm = db.Column(db.Float)
    arm_left_cm = db.Column(db.Float)
    thigh_right_cm = db.Column(db.Float)
    thigh_left_cm = db.Column(db.Float)
    calf_cm = db.Column(db.Float)
    body_fat_pct = db.Column(db.Float)
    notes = db.Column(db.Text)

    def bmi(self, height_cm):
        if not self.weight_kg or not height_cm:
            return None
        h = height_cm / 100
        return round(self.weight_kg / (h * h), 1)


class WorkoutPlan(db.Model):
    __tablename__ = "workout_plans"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    exercises = db.relationship(
        "PlanExercise",
        backref="plan",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="PlanExercise.position",
    )
    sessions = db.relationship("WorkoutSession", backref="plan", lazy=True)


class PlanExercise(db.Model):
    __tablename__ = "plan_exercises"

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("workout_plans.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    muscle_group = db.Column(db.String(60))
    target_sets = db.Column(db.Integer, default=3)
    target_reps = db.Column(db.String(30), default="10")
    rest_seconds = db.Column(db.Integer)
    notes = db.Column(db.String(255))
    position = db.Column(db.Integer, default=0)

    set_logs = db.relationship("SetLog", backref="exercise", lazy=True)


class WorkoutSession(db.Model):
    __tablename__ = "workout_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey("workout_plans.id"))
    date = db.Column(db.Date, nullable=False, default=date.today)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    set_logs = db.relationship(
        "SetLog", backref="session", lazy=True, cascade="all, delete-orphan"
    )

    @property
    def total_volume(self):
        return sum((s.reps or 0) * (s.weight_kg or 0) for s in self.set_logs)


class SetLog(db.Model):
    __tablename__ = "set_logs"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.Integer, db.ForeignKey("workout_sessions.id"), nullable=False
    )
    plan_exercise_id = db.Column(db.Integer, db.ForeignKey("plan_exercises.id"))
    exercise_name = db.Column(db.String(120), nullable=False)
    set_number = db.Column(db.Integer, nullable=False, default=1)
    reps = db.Column(db.Integer)
    weight_kg = db.Column(db.Float)
