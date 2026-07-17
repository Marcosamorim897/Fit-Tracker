import calendar
import os
from collections import defaultdict
from datetime import date, datetime, timedelta

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from models import (
    Measurement,
    PlanExercise,
    SetLog,
    User,
    WhatsAppLink,
    WhatsAppLinkCode,
    WorkoutPlan,
    WorkoutSession,
    db,
)
from whatsapp_bot import wa

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "troque-esta-chave-em-producao")

# Render/Heroku fornecem URLs "postgres://", mas o SQLAlchemy exige "postgresql://"
_db_url = os.environ.get(
    "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "fittracker.db")
)
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = _db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# Bancos serverless (Neon) fecham conexões ociosas; sem isso, a primeira
# operação após ~5 min de inatividade falha com 500.
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 280,
}

db.init_app(app)
app.register_blueprint(wa)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Faça login para acessar esta página."
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def parse_float(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return None


def parse_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_date(value, default=None):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return default


def bmi_class(bmi):
    if bmi is None:
        return None
    if bmi < 18.5:
        return "Abaixo do peso"
    if bmi < 25:
        return "Peso normal"
    if bmi < 30:
        return "Sobrepeso"
    if bmi < 35:
        return "Obesidade grau I"
    if bmi < 40:
        return "Obesidade grau II"
    return "Obesidade grau III"


# ---------------------------------------------------------------- pwa


@app.route("/sw.js")
def service_worker():
    # servido da raiz para que o service worker tenha escopo "/"
    resp = send_from_directory(
        os.path.join(BASE_DIR, "static", "js"), "sw.js", mimetype="text/javascript"
    )
    # sem cache: atualizações do sw.js valem já no próximo carregamento
    resp.headers["Cache-Control"] = "no-cache"
    return resp


# ---------------------------------------------------------------- auth


@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/cadastro", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if not name or not email or not password:
            flash("Preencha nome, e-mail e senha.", "danger")
        elif len(password) < 6:
            flash("A senha precisa ter pelo menos 6 caracteres.", "danger")
        elif password != confirm:
            flash("As senhas não conferem.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("Já existe uma conta com esse e-mail.", "danger")
        else:
            user = User(
                name=name,
                email=email,
                height_cm=parse_float(request.form.get("height_cm")),
                birth_date=parse_date(request.form.get("birth_date")),
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash(f"Bem-vindo(a), {user.name}! Conta criada com sucesso.", "success")
            return redirect(url_for("dashboard"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=bool(request.form.get("remember")))
            return redirect(request.args.get("next") or url_for("dashboard"))
        flash("E-mail ou senha incorretos.", "danger")
    return render_template("login.html")


@app.route("/sair")
@login_required
def logout():
    logout_user()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("index"))


@app.route("/perfil", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        current_user.name = request.form.get("name", current_user.name).strip()
        current_user.height_cm = parse_float(request.form.get("height_cm"))
        current_user.birth_date = parse_date(request.form.get("birth_date"))
        new_password = request.form.get("new_password", "")
        if new_password:
            if len(new_password) < 6:
                flash("A nova senha precisa ter pelo menos 6 caracteres.", "danger")
                return redirect(url_for("profile"))
            current_user.set_password(new_password)
        db.session.commit()
        flash("Perfil atualizado.", "success")
        return redirect(url_for("profile"))
    return render_template("profile.html")


@app.route("/whatsapp", methods=["GET", "POST"])
@login_required
def whatsapp_link():
    import secrets

    link = WhatsAppLink.query.filter_by(user_id=current_user.id).first()
    code = None
    if request.method == "POST":
        if request.form.get("action") == "unlink":
            if link:
                db.session.delete(link)
                db.session.commit()
                flash("WhatsApp desvinculado.", "info")
            return redirect(url_for("whatsapp_link"))
        WhatsAppLinkCode.query.filter_by(user_id=current_user.id).delete()
        code = f"{secrets.randbelow(1_000_000):06d}"
        db.session.add(
            WhatsAppLinkCode(
                user_id=current_user.id,
                code=code,
                expires_at=datetime.utcnow() + timedelta(minutes=15),
            )
        )
        db.session.commit()
    return render_template(
        "whatsapp.html",
        link=link,
        code=code,
        bot_number=os.environ.get("WA_BOT_NUMBER"),
    )


# ---------------------------------------------------------------- dashboard


@app.route("/painel")
@login_required
def dashboard():
    last_measure = (
        Measurement.query.filter_by(user_id=current_user.id)
        .order_by(Measurement.date.desc())
        .first()
    )
    recent_sessions = (
        WorkoutSession.query.filter_by(user_id=current_user.id)
        .order_by(WorkoutSession.date.desc(), WorkoutSession.id.desc())
        .limit(5)
        .all()
    )
    active_plans = WorkoutPlan.query.filter_by(
        user_id=current_user.id, active=True
    ).all()

    total_sessions = WorkoutSession.query.filter_by(user_id=current_user.id).count()
    month_start = date.today().replace(day=1)
    sessions_month = (
        WorkoutSession.query.filter_by(user_id=current_user.id)
        .filter(WorkoutSession.date >= month_start)
        .count()
    )

    bmi = last_measure.bmi(current_user.height_cm) if last_measure else None
    return render_template(
        "dashboard.html",
        last_measure=last_measure,
        recent_sessions=recent_sessions,
        active_plans=active_plans,
        total_sessions=total_sessions,
        sessions_month=sessions_month,
        bmi=bmi,
        bmi_label=bmi_class(bmi),
    )


# ---------------------------------------------------------------- medidas


MEASURE_FIELDS = [
    ("weight_kg", "Peso (kg)"),
    ("chest_cm", "Peitoral (cm)"),
    ("waist_cm", "Cintura (cm)"),
    ("hips_cm", "Quadril (cm)"),
    ("arm_right_cm", "Braço dir. (cm)"),
    ("arm_left_cm", "Braço esq. (cm)"),
    ("thigh_right_cm", "Coxa dir. (cm)"),
    ("thigh_left_cm", "Coxa esq. (cm)"),
    ("calf_cm", "Panturrilha (cm)"),
    ("body_fat_pct", "Gordura corporal (%)"),
]


@app.route("/medidas", methods=["GET", "POST"])
@login_required
def measurements():
    if request.method == "POST":
        m = Measurement(
            user_id=current_user.id,
            date=parse_date(request.form.get("date"), date.today()),
            notes=request.form.get("notes", "").strip() or None,
        )
        for field, _label in MEASURE_FIELDS:
            setattr(m, field, parse_float(request.form.get(field)))
        db.session.add(m)
        db.session.commit()
        flash("Medidas registradas.", "success")
        return redirect(url_for("measurements"))

    items = (
        Measurement.query.filter_by(user_id=current_user.id)
        .order_by(Measurement.date.desc(), Measurement.id.desc())
        .all()
    )
    return render_template(
        "measurements.html", items=items, fields=MEASURE_FIELDS, today=date.today()
    )


@app.route("/medidas/<int:measure_id>/excluir", methods=["POST"])
@login_required
def delete_measurement(measure_id):
    m = Measurement.query.filter_by(
        id=measure_id, user_id=current_user.id
    ).first_or_404()
    db.session.delete(m)
    db.session.commit()
    flash("Registro de medidas excluído.", "info")
    return redirect(url_for("measurements"))


# ---------------------------------------------------------------- fichas


@app.route("/fichas")
@login_required
def plans():
    items = (
        WorkoutPlan.query.filter_by(user_id=current_user.id)
        .order_by(WorkoutPlan.active.desc(), WorkoutPlan.created_at.desc())
        .all()
    )
    return render_template("plans.html", items=items)


@app.route("/fichas/nova", methods=["GET", "POST"])
@login_required
def new_plan():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Dê um nome para a ficha.", "danger")
        else:
            plan = WorkoutPlan(
                user_id=current_user.id,
                name=name,
                description=request.form.get("description", "").strip() or None,
            )
            db.session.add(plan)
            db.session.commit()
            flash("Ficha criada. Agora adicione os exercícios.", "success")
            return redirect(url_for("plan_detail", plan_id=plan.id))
    return render_template("plan_form.html", plan=None)


@app.route("/fichas/<int:plan_id>", methods=["GET", "POST"])
@login_required
def plan_detail(plan_id):
    plan = WorkoutPlan.query.filter_by(
        id=plan_id, user_id=current_user.id
    ).first_or_404()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Informe o nome do exercício.", "danger")
        else:
            ex = PlanExercise(
                plan_id=plan.id,
                name=name,
                muscle_group=request.form.get("muscle_group", "").strip() or None,
                target_sets=parse_int(request.form.get("target_sets")) or 3,
                target_reps=request.form.get("target_reps", "").strip() or "10",
                rest_seconds=parse_int(request.form.get("rest_seconds")),
                notes=request.form.get("notes", "").strip() or None,
                position=len(plan.exercises),
            )
            db.session.add(ex)
            db.session.commit()
            flash("Exercício adicionado.", "success")
        return redirect(url_for("plan_detail", plan_id=plan.id))
    return render_template("plan_detail.html", plan=plan)


@app.route("/fichas/<int:plan_id>/editar", methods=["GET", "POST"])
@login_required
def edit_plan(plan_id):
    plan = WorkoutPlan.query.filter_by(
        id=plan_id, user_id=current_user.id
    ).first_or_404()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Dê um nome para a ficha.", "danger")
        else:
            plan.name = name
            plan.description = request.form.get("description", "").strip() or None
            plan.active = bool(request.form.get("active"))
            db.session.commit()
            flash("Ficha atualizada.", "success")
            return redirect(url_for("plan_detail", plan_id=plan.id))
    return render_template("plan_form.html", plan=plan)


@app.route("/fichas/<int:plan_id>/excluir", methods=["POST"])
@login_required
def delete_plan(plan_id):
    plan = WorkoutPlan.query.filter_by(
        id=plan_id, user_id=current_user.id
    ).first_or_404()
    db.session.delete(plan)
    db.session.commit()
    flash("Ficha excluída.", "info")
    return redirect(url_for("plans"))


@app.route("/exercicios/<int:exercise_id>/excluir", methods=["POST"])
@login_required
def delete_exercise(exercise_id):
    ex = PlanExercise.query.get_or_404(exercise_id)
    if ex.plan.user_id != current_user.id:
        return "Não autorizado", 403
    plan_id = ex.plan_id
    db.session.delete(ex)
    db.session.commit()
    flash("Exercício removido da ficha.", "info")
    return redirect(url_for("plan_detail", plan_id=plan_id))


# ---------------------------------------------------------------- treinos


@app.route("/treinar", methods=["GET"])
@login_required
def choose_workout():
    active_plans = WorkoutPlan.query.filter_by(
        user_id=current_user.id, active=True
    ).all()
    return render_template("choose_workout.html", plans=active_plans)


@app.route("/treinar/<int:plan_id>", methods=["GET", "POST"])
@login_required
def log_workout(plan_id):
    plan = WorkoutPlan.query.filter_by(
        id=plan_id, user_id=current_user.id
    ).first_or_404()
    if request.method == "POST":
        session = WorkoutSession(
            user_id=current_user.id,
            plan_id=plan.id,
            date=parse_date(request.form.get("date"), date.today()),
            notes=request.form.get("notes", "").strip() or None,
        )
        db.session.add(session)

        any_set = False
        for ex in plan.exercises:
            for set_number in range(1, (ex.target_sets or 3) + 1):
                reps = parse_int(request.form.get(f"reps_{ex.id}_{set_number}"))
                weight = parse_float(request.form.get(f"weight_{ex.id}_{set_number}"))
                if reps is None and weight is None:
                    continue
                any_set = True
                db.session.add(
                    SetLog(
                        session=session,
                        plan_exercise_id=ex.id,
                        exercise_name=ex.name,
                        set_number=set_number,
                        reps=reps,
                        weight_kg=weight,
                    )
                )
        if not any_set:
            db.session.rollback()
            flash("Preencha pelo menos uma série antes de salvar.", "danger")
            return redirect(url_for("log_workout", plan_id=plan.id))

        db.session.commit()
        flash("Treino registrado! 💪", "success")
        return redirect(url_for("session_detail", session_id=session.id))

    # última carga usada em cada exercício, para referência
    last_sets = {}
    for ex in plan.exercises:
        last = (
            SetLog.query.join(WorkoutSession)
            .filter(
                SetLog.plan_exercise_id == ex.id,
                WorkoutSession.user_id == current_user.id,
            )
            .order_by(WorkoutSession.date.desc(), SetLog.id.desc())
            .first()
        )
        if last:
            last_sets[ex.id] = last
    return render_template(
        "log_workout.html", plan=plan, last_sets=last_sets, today=date.today()
    )


@app.route("/historico")
@login_required
def history():
    sessions = (
        WorkoutSession.query.filter_by(user_id=current_user.id)
        .order_by(WorkoutSession.date.desc(), WorkoutSession.id.desc())
        .all()
    )
    return render_template("history.html", sessions=sessions)


@app.route("/historico/<int:session_id>")
@login_required
def session_detail(session_id):
    session = WorkoutSession.query.filter_by(
        id=session_id, user_id=current_user.id
    ).first_or_404()
    grouped = defaultdict(list)
    for s in session.set_logs:
        grouped[s.exercise_name].append(s)
    return render_template(
        "session_detail.html", session=session, grouped=dict(grouped)
    )


@app.route("/historico/<int:session_id>/excluir", methods=["POST"])
@login_required
def delete_session(session_id):
    session = WorkoutSession.query.filter_by(
        id=session_id, user_id=current_user.id
    ).first_or_404()
    db.session.delete(session)
    db.session.commit()
    flash("Treino excluído do histórico.", "info")
    return redirect(url_for("history"))


# ---------------------------------------------------------------- calendário


@app.route("/calendario")
@app.route("/calendario/<int:year>/<int:month>")
@login_required
def calendar_view(year=None, month=None):
    today = date.today()
    year = year or today.year
    month = month or today.month

    first = date(year, month, 1)
    prev_month = (first - timedelta(days=1)).replace(day=1)
    next_month = (first + timedelta(days=32)).replace(day=1)

    sessions = (
        WorkoutSession.query.filter_by(user_id=current_user.id)
        .filter(WorkoutSession.date >= first, WorkoutSession.date < next_month)
        .all()
    )
    by_day = defaultdict(list)
    for s in sessions:
        by_day[s.date.day].append(s)

    weeks = calendar.Calendar(firstweekday=6).monthdayscalendar(year, month)
    month_names = [
        "",
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
    ]
    return render_template(
        "calendar.html",
        weeks=weeks,
        by_day=by_day,
        year=year,
        month=month,
        month_name=month_names[month],
        prev_month=prev_month,
        next_month=next_month,
        today=today,
    )


# ---------------------------------------------------------------- progresso


@app.route("/progresso")
@login_required
def progress():
    exercise_names = [
        row[0]
        for row in db.session.query(SetLog.exercise_name)
        .join(WorkoutSession)
        .filter(WorkoutSession.user_id == current_user.id)
        .distinct()
        .order_by(SetLog.exercise_name)
        .all()
    ]
    return render_template("progress.html", exercise_names=exercise_names)


@app.route("/api/progresso/medidas")
@login_required
def api_measurements():
    items = (
        Measurement.query.filter_by(user_id=current_user.id)
        .order_by(Measurement.date)
        .all()
    )
    return jsonify(
        {
            "labels": [m.date.strftime("%d/%m/%Y") for m in items],
            "weight": [m.weight_kg for m in items],
            "bmi": [m.bmi(current_user.height_cm) for m in items],
            "waist": [m.waist_cm for m in items],
            "body_fat": [m.body_fat_pct for m in items],
        }
    )


@app.route("/api/progresso/exercicio")
@login_required
def api_exercise_progress():
    name = request.args.get("nome", "")
    rows = (
        db.session.query(WorkoutSession.date, SetLog.weight_kg, SetLog.reps)
        .join(SetLog, SetLog.session_id == WorkoutSession.id)
        .filter(
            WorkoutSession.user_id == current_user.id,
            SetLog.exercise_name == name,
        )
        .order_by(WorkoutSession.date)
        .all()
    )
    by_date = {}
    for d, weight, reps in rows:
        entry = by_date.setdefault(d, {"max_weight": 0, "volume": 0})
        if weight:
            entry["max_weight"] = max(entry["max_weight"], weight)
            entry["volume"] += (reps or 0) * weight
    return jsonify(
        {
            "labels": [d.strftime("%d/%m/%Y") for d in by_date],
            "max_weight": [v["max_weight"] for v in by_date.values()],
            "volume": [v["volume"] for v in by_date.values()],
        }
    )


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
