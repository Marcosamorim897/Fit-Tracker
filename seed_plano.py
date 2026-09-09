"""Cria as fichas do plano superior/inferior de 5 dias no Fit-Tracker.

Uso:
    python seed_plano.py --email voce@exemplo.com
    python seed_plano.py --email voce@exemplo.com --substituir

Sem --substituir, fichas com o mesmo nome são puladas (o script pode rodar
mais de uma vez sem duplicar). Com --substituir, as fichas de mesmo nome são
apagadas e recriadas — o histórico de sessões vinculado a elas fica com
plan_id órfão, então use apenas se ainda não treinou com essas fichas.

Para rodar contra o banco de produção (Neon), exporte a DATABASE_URL antes:
    export DATABASE_URL="postgresql://..."
"""

import argparse
import sys

from app import app
from models import PlanExercise, User, WorkoutPlan, db

# (nome, grupo, séries, reps, descanso em segundos, observação)
PLANO = [
    {
        "name": "Treino A — Superior (empurrar)",
        "description": "Segunda. Ênfase em empurrar, com puxada para equilibrar o volume.",
        "exercises": [
            ("Supino reto com halteres", "Peito", 3, "8-12", 90, "Incremento: +2,5 kg"),
            ("Puxada frontal", "Costas", 3, "10-12", 90, "Incremento: +5 kg"),
            ("Desenvolvimento com halteres", "Ombros", 3, "10-12", 90, "Incremento: +2 kg"),
            ("Remada baixa na polia", "Costas", 3, "10-12", 90, "Incremento: +5 kg"),
            ("Elevação lateral", "Ombros", 3, "12-15", 60, "Incremento: +1 kg"),
            ("Tríceps na corda", "Tríceps", 2, "12-15", 60, "Incremento: +2,5 kg"),
            ("Rosca direta", "Bíceps", 2, "10-12", 60, "Incremento: +2 kg"),
        ],
    },
    {
        "name": "Treino B — Inferior (quadríceps)",
        "description": "Terça. Ênfase em quadríceps.",
        "exercises": [
            ("Agachamento goblet", "Quadríceps", 3, "8-12", 120, "Livre só quando a técnica estiver sólida"),
            ("Leg press 45°", "Quadríceps", 3, "10-12", 90, "Incremento: +10 kg"),
            ("Cadeira extensora", "Quadríceps", 3, "12-15", 60, "Incremento: +5 kg"),
            ("Mesa flexora", "Posterior", 3, "10-12", 60, "Incremento: +5 kg"),
            ("Elevação pélvica", "Glúteo", 3, "10-12", 90, "Incremento: +5 kg"),
            ("Panturrilha em pé", "Panturrilha", 3, "12-15", 45, "Incremento: +5 kg"),
            ("Prancha isométrica", "Core", 3, "30-45s", 45, "Progrida no tempo, não na carga"),
        ],
    },
    {
        "name": "Treino C — Superior (puxar)",
        "description": "Quarta. Ênfase em puxar, com empurrar para equilibrar o volume.",
        "exercises": [
            ("Puxada aberta", "Costas", 3, "8-12", 90, "Incremento: +5 kg"),
            ("Supino inclinado na máquina", "Peito", 3, "10-12", 90, "Incremento: +5 kg"),
            ("Remada curvada com halteres", "Costas", 3, "10-12", 90, "Incremento: +2,5 kg"),
            ("Crucifixo na máquina", "Peito", 2, "12-15", 60, "Incremento: +5 kg"),
            ("Face pull na polia", "Ombros", 3, "15", 60, "Foco em saúde do ombro"),
            ("Rosca martelo", "Bíceps", 2, "10-12", 60, "Incremento: +2 kg"),
            ("Tríceps testa", "Tríceps", 2, "10-12", 60, "Incremento: +2,5 kg"),
        ],
    },
    {
        "name": "Treino D — Inferior (posterior e glúteo)",
        "description": "Quinta. Ênfase em posterior de coxa e glúteo.",
        "exercises": [
            ("Stiff com halteres", "Posterior", 3, "8-10", 120, "Coluna neutra; amplitude sem arredondar"),
            ("Leg press pés altos", "Posterior", 3, "10-12", 90, "Incremento: +10 kg"),
            ("Mesa flexora", "Posterior", 3, "12-15", 60, "Incremento: +5 kg"),
            ("Afundo com halteres", "Quadríceps", 3, "10 por perna", 90, "Incremento: +2 kg"),
            ("Cadeira abdutora", "Glúteo", 2, "15", 45, "Incremento: +5 kg"),
            ("Panturrilha sentado", "Panturrilha", 3, "15", 45, "Incremento: +5 kg"),
            ("Abdominal", "Core", 3, "15", 45, None),
        ],
    },
    {
        "name": "Treino E — Full body e condicionamento",
        "description": "Sexta. Corpo todo em volume menor, fechando com 20 min de cardio.",
        "exercises": [
            ("Agachamento goblet", "Quadríceps", 3, "12", 75, "Incremento: +2,5 kg"),
            ("Remada na máquina", "Costas", 3, "12", 75, "Incremento: +5 kg"),
            ("Supino na máquina", "Peito", 3, "12", 75, "Incremento: +5 kg"),
            ("Desenvolvimento na máquina", "Ombros", 3, "12", 75, "Incremento: +2,5 kg"),
            ("Rosca e tríceps em bi-set", "Braços", 2, "12", 60, "Sem descanso entre os dois"),
            ("Esteira inclinada", "Cardio", 1, "20 min", 0, "Ritmo moderado, dá para conversar"),
        ],
    },
]


def seed(email, substituir=False):
    user = User.query.filter_by(email=email).first()
    if not user:
        emails = [u.email for u in User.query.all()]
        print(f"Usuário não encontrado: {email}")
        if emails:
            print("Cadastrados neste banco: " + ", ".join(emails))
        return 1

    criadas, puladas = 0, 0

    for ficha in PLANO:
        existente = WorkoutPlan.query.filter_by(
            user_id=user.id, name=ficha["name"]
        ).first()

        if existente:
            if not substituir:
                print(f"pulada    {ficha['name']} (já existe)")
                puladas += 1
                continue
            db.session.delete(existente)
            db.session.flush()

        plan = WorkoutPlan(
            user_id=user.id,
            name=ficha["name"],
            description=ficha["description"],
            active=True,
        )
        db.session.add(plan)
        db.session.flush()

        for pos, (nome, grupo, series, reps, descanso, obs) in enumerate(ficha["exercises"]):
            db.session.add(
                PlanExercise(
                    plan_id=plan.id,
                    name=nome,
                    muscle_group=grupo,
                    target_sets=series,
                    target_reps=reps,
                    rest_seconds=descanso,
                    notes=obs,
                    position=pos,
                )
            )

        print(f"criada    {ficha['name']} ({len(ficha['exercises'])} exercícios)")
        criadas += 1

    db.session.commit()
    print(f"\n{criadas} ficha(s) criada(s), {puladas} pulada(s), usuário {user.name}.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Popula as fichas do plano de 5 dias.")
    parser.add_argument("--email", required=True, help="E-mail da conta no Fit-Tracker")
    parser.add_argument(
        "--substituir",
        action="store_true",
        help="Apaga e recria fichas de mesmo nome",
    )
    args = parser.parse_args()

    with app.app_context():
        sys.exit(seed(args.email, args.substituir))


if __name__ == "__main__":
    main()
