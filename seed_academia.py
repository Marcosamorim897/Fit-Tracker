"""Cria as fichas A, B e C da academia (3x12) no Fit-Tracker.

Uso (igual ao seed_plano.py):
    python seed_academia.py --email voce@exemplo.com
    python seed_academia.py --email voce@exemplo.com --substituir

Fichas com o mesmo nome são puladas, então o script pode rodar mais de uma
vez sem duplicar. Para gravar no banco de produção (Neon), defina a
DATABASE_URL antes de rodar — no PowerShell:
    $env:DATABASE_URL = "postgresql://..."

O descanso entre exercícios (2 min) não tem campo próprio no modelo, por isso
fica na descrição da ficha. As cargas ficam em branco: são anotadas a cada
treino. Pulley frente com barra (B) e com triângulo (C) têm nomes distintos
para que o gráfico de progresso não misture as duas pegadas.
"""

from seed_plano import main

AQUECIMENTO = "1 série de aquecimento com 50% da carga máxima (8 reps)."
DESCRICAO = "Ficha da academia · 3x12 · descanso de 1 min entre séries e 2 min entre exercícios."

# (nome, grupo, séries, reps, descanso em segundos, observação)
FICHAS = [
    {
        "name": "Ficha A — Pernas",
        "description": DESCRICAO,
        "exercises": [
            ("Gêmeos em pé", "Panturrilha", 3, "12", 60, AQUECIMENTO),
            ("Cadeira abdutora", "Glúteos", 3, "12", 60, None),
            ("Mesa flexora", "Posterior", 3, "12", 60, AQUECIMENTO),
            ("Leg press (45° ou 180°)", "Quadríceps", 3, "12", 60, None),
            ("Cadeira adutora", "Adutores", 3, "12", 60, None),
            ("Cadeira flexora", "Posterior", 3, "12", 60, None),
            ("Cadeira extensora", "Quadríceps", 3, "12", 60, None),
        ],
    },
    {
        "name": "Ficha B — Superiores",
        "description": DESCRICAO,
        "exercises": [
            ("Supino reto na máquina", "Peitoral", 3, "12", 60, AQUECIMENTO),
            ("Pulley frente (barra)", "Costas", 3, "12", 60, AQUECIMENTO + " Com barra."),
            ("Crucifixo na máquina", "Peitoral", 3, "12", 60, None),
            (
                "Remada baixa",
                "Costas",
                3,
                "12",
                60,
                "Com triângulo: costas retas, puxando na direção do umbigo.",
            ),
            ("Desenvolvimento de ombros", "Ombros", 3, "12", 60, "Com halteres."),
            ("Tríceps na polia", "Tríceps", 3, "12", 60, None),
            ("Rosca direta", "Bíceps", 3, "12", 60, "Com halteres."),
        ],
    },
    {
        "name": "Ficha C — Superiores",
        "description": DESCRICAO,
        "exercises": [
            (
                "Pulley frente (triângulo)",
                "Costas",
                3,
                "12",
                60,
                AQUECIMENTO + " Com triângulo.",
            ),
            ("Remada na máquina", "Costas", 3, "12", 60, "Pegada pronada (mão por cima)."),
            (
                "Supino inclinado na máquina",
                "Peitoral",
                3,
                "12",
                60,
                "Sentado: o braço vai na diagonal para cima. Deitado: banco inclinado "
                "para cima. " + AQUECIMENTO,
            ),
            ("Rosca Scott na máquina", "Bíceps", 3, "12", 60, None),
            (
                "Tríceps francês na polia",
                "Tríceps",
                3,
                "12",
                60,
                "Polia na linha da cintura; o braço não deve passar da cabeça.",
            ),
            ("Desenvolvimento de ombro lateral", "Ombros", 3, "12", 60, "Máquina ou halter."),
            ("Desenvolvimento de ombro frontal", "Ombros", 3, "12", 60, "Halter ou anilha."),
        ],
    },
]


if __name__ == "__main__":
    main(FICHAS, "Popula as fichas A, B e C da academia.")
