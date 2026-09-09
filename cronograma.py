"""Cronograma de treino introdutório (divisão superior/inferior, 5x por semana).

Fonte única dos dados exibidos em /cronograma e usados na importação de fichas.
Os dias da semana ficam no nome/descrição da ficha porque o modelo WorkoutPlan
não tem campo de dia (e o app cria o schema com db.create_all()).
"""

META = {
    "titulo": "Cronograma de Treino",
    "subtitulo": "Programa para iniciante · Divisão Superior/Inferior",
    "frequencia": "5x por semana",
    "duracao": "~55–60 min",
    "objetivo": "perda de gordura",
    "frequencia_grupo": "2x por semana",
    "ciclo": "Programa introdutório de 8 a 12 semanas · Reavalie ao final do ciclo.",
}

ESTRUTURA_SEMANAL = [
    ("Segunda", "A — Superior (ênfase empurrar)"),
    ("Terça", "B — Inferior (ênfase quadríceps)"),
    ("Quarta", "C — Superior (ênfase puxar)"),
    ("Quinta", "D — Inferior (ênfase posterior/glúteo)"),
    ("Sexta", "E — Full body + condicionamento"),
    ("Sábado / Domingo", "Descanso ativo — caminhada de 30 a 40 min"),
]

AVISO_SEMANA = (
    "Se faltar um dia, apenas retome pela ordem na próxima ida à academia. "
    "Nunca faça dois treinos de perna em dias seguidos."
)

AQUECIMENTO = [
    "5 min de esteira ou bike em ritmo leve",
    "Mobilidade: rotação de ombros, círculos de quadril e agachamento sem carga — 10 repetições cada",
    "1 série leve (cerca de 50% da carga) do primeiro exercício do dia",
]

# Cada treino gera uma ficha (WorkoutPlan) na importação.
TREINOS = [
    {
        "codigo": "A",
        "foco": "Superior (empurrar)",
        "dia": "Segunda",
        "exercicios": [
            ("Supino reto com halteres", "Peitoral", 3, "8–12", 90, None),
            ("Puxada frontal (pulldown)", "Costas", 3, "10–12", 90, None),
            ("Desenvolvimento com halteres", "Ombros", 3, "10–12", 90, "sentado"),
            ("Remada baixa na polia", "Costas", 3, "10–12", 90, None),
            ("Elevação lateral", "Ombros", 3, "12–15", 60, None),
            ("Tríceps na corda", "Tríceps", 2, "12–15", 60, None),
            ("Rosca direta", "Bíceps", 2, "10–12", 60, None),
        ],
    },
    {
        "codigo": "B",
        "foco": "Inferior (quadríceps)",
        "dia": "Terça",
        "exercicios": [
            (
                "Agachamento goblet",
                "Pernas",
                3,
                "8–12",
                120,
                "ou livre, se dominar a técnica",
            ),
            ("Leg press 45°", "Pernas", 3, "10–12", 90, None),
            ("Cadeira extensora", "Pernas", 3, "12–15", 60, None),
            ("Mesa flexora", "Posterior", 3, "10–12", 60, None),
            ("Elevação pélvica (hip thrust)", "Glúteos", 3, "10–12", 90, None),
            ("Panturrilha em pé", "Panturrilha", 3, "12–15", 45, None),
            ("Prancha isométrica", "Abdômen", 3, "30–45s", 45, "isometria"),
        ],
    },
    {
        "codigo": "C",
        "foco": "Superior (puxar)",
        "dia": "Quarta",
        "exercicios": [
            ("Puxada aberta", "Costas", 3, "8–12", 90, "ou barra assistida"),
            ("Supino inclinado na máquina", "Peitoral", 3, "10–12", 90, None),
            ("Remada curvada com halteres", "Costas", 3, "10–12", 90, None),
            ("Crucifixo na máquina (peck deck)", "Peitoral", 2, "12–15", 60, None),
            ("Face pull na polia", "Ombros", 3, "15", 60, None),
            ("Rosca martelo", "Bíceps", 2, "10–12", 60, None),
            ("Tríceps testa", "Tríceps", 2, "10–12", 60, "ou francês"),
        ],
    },
    {
        "codigo": "D",
        "foco": "Inferior (posterior/glúteo)",
        "dia": "Quinta",
        "exercicios": [
            ("Stiff com halteres ou barra", "Posterior", 3, "8–10", 120, None),
            ("Leg press", "Pernas", 3, "10–12", 90, "pés altos na plataforma"),
            ("Mesa flexora", "Posterior", 3, "12–15", 60, None),
            (
                "Afundo / passada com halteres",
                "Pernas",
                3,
                "10 por perna",
                90,
                None,
            ),
            ("Cadeira abdutora", "Glúteos", 2, "15", 45, None),
            ("Panturrilha sentado", "Panturrilha", 3, "15", 45, None),
            ("Abdominal", "Abdômen", 3, "15", 45, "máquina ou solo"),
        ],
    },
    {
        "codigo": "E",
        "foco": "Full body + condicionamento",
        "dia": "Sexta",
        "exercicios": [
            ("Agachamento goblet", "Pernas", 3, "12", 75, None),
            ("Remada na máquina", "Costas", 3, "12", 75, None),
            ("Supino na máquina", "Peitoral", 3, "12", 75, None),
            ("Desenvolvimento na máquina", "Ombros", 3, "12", 75, None),
            ("Rosca + tríceps (bi-set)", "Braços", 2, "12 cada", 60, "bi-set"),
            (
                "Condicionamento: esteira inclinada ou bike",
                "Cardio",
                1,
                "20 min moderado",
                None,
                "ritmo moderado",
            ),
        ],
    },
]

CARDIO = [
    "3 a 4x por semana, 20–25 min, logo após a musculação ou em horário separado",
    "Intensidade moderada: você consegue conversar, mas com algum esforço "
    "(esteira inclinada, bike, elíptico)",
    "Nos dias de descanso: caminhada de 30–40 min",
    "Evite HIIT no início — você ainda está construindo base e capacidade de recuperação",
]

PROGRESSAO = [
    'Escolha uma carga em que você termine a série com 2 a 3 repetições ainda "na reserva".',
    "Quando conseguir atingir o topo da faixa de repetições em todas as séries "
    "(ex.: 3×12 quando a meta é 8–12), aumente a carga na sessão seguinte.",
    "Incremento: 2,5–5 kg em exercícios de perna e costas; 1–2 kg em ombro e braço.",
    "Ao subir a carga, as repetições caem para o piso da faixa — e o ciclo recomeça.",
]

AVISO_PROGRESSAO = (
    "Anote tudo: carga, séries e repetições de cada treino. "
    "Sem registro não existe progressão controlada."
)

REGRAS_DE_OURO = [
    (
        "Técnica antes de carga.",
        "Nas primeiras 2–3 semanas, use cargas leves e foque em aprender o movimento.",
    ),
    (
        "Não treine até a falha em todas as séries.",
        "Pare com 1–3 repetições na reserva.",
    ),
    (
        "Deload a cada 6–8 semanas:",
        "uma semana com cerca de 60% do volume normal.",
    ),
    ("Sono de 7 a 9 horas.", "É onde a recuperação acontece de fato."),
    (
        "Dor articular não é dor muscular.",
        "Dor em articulação = pare o exercício e revise a execução.",
    ),
]

PERDA_DE_GORDURA = [
    "O treino cria o estímulo para preservar (e ganhar) músculo, mas a perda de gordura "
    "é determinada principalmente pela alimentação. Vale procurar um nutricionista para "
    "montar essa parte com base no seu caso — é o complemento que faz este cronograma render.",
    "Também vale pedir a um educador físico da sua academia para observar sua execução "
    "nos exercícios principais (agachamento, stiff, supino e remada) nas primeiras semanas.",
]


def nome_ficha(treino):
    """Nome da ficha no app, ex.: 'Treino A — Superior (empurrar)'."""
    return f"Treino {treino['codigo']} — {treino['foco']}"


def descricao_ficha(treino):
    """Descrição da ficha: guarda o dia da semana, que não tem campo próprio."""
    return f"{treino['dia']} · cronograma introdutório (5x/semana)"
