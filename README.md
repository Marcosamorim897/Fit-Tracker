#  FitTracker

Aplicação web para controle de treinos e saúde: monte suas fichas de treino,
registre repetições e cargas a cada sessão e acompanhe sua evolução com
gráficos, medidas corporais, IMC e calendário.

## Funcionalidades

- **Cadastro e login** — contas com senha criptografada (hash), cada usuário vê apenas os próprios dados
- **Fichas de treino** — crie fichas (ex.: Treino A / B / C) com exercícios, séries, repetições, descanso e observações
- **Cronograma pronto** — em `/cronograma`, o programa introdutório completo (divisão superior/inferior, 5x por semana): estrutura semanal, aquecimento, cardio, dupla progressão e regras de ouro, com um botão que importa os 5 treinos como fichas na sua conta
- **Registro de execução** — durante o treino, anote as repetições e os pesos de cada série; o app mostra a última carga usada como referência
- **Histórico de treinos** — todas as sessões registradas, com volume total (reps × kg) e detalhe por exercício
- **Medidas corporais** — peso, peitoral, cintura, quadril, braços, coxas, panturrilha e % de gordura, com histórico
- **Gráficos de evolução** — peso corporal, IMC, cintura, gordura e progressão de carga/volume por exercício (Chart.js)
- **IMC e resumo corporal** — cálculo automático com classificação
- **Calendário de treinos** — visão mensal dos dias treinados

## Tecnologias

- **Backend:** Python 3 + Flask, Flask-SQLAlchemy (SQLite), Flask-Login
- **Frontend:** HTML/CSS/JS puro (templates Jinja) + Chart.js

## Como rodar

```bash
# 1. Crie e ative um ambiente virtual
python3 -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Rode o servidor
python app.py
```

Acesse **http://127.0.0.1:5000**, crie sua conta e comece a treinar. 

O banco (`fittracker.db`, SQLite) é criado automaticamente na primeira execução
e fica fora do controle de versão.

## Configuração (opcional)

| Variável       | Descrição                                              |
| -------------- | ------------------------------------------------------ |
| `SECRET_KEY`   | Chave de sessão do Flask (defina uma em produção!)     |
| `DATABASE_URL` | URL do banco (padrão: SQLite local; aceita Postgres)   |

## Estrutura

```
├── app.py           # Rotas e configuração do Flask
├── models.py        # Modelos do banco (SQLAlchemy)
├── cronograma.py    # Dados do cronograma de treino (página + importação de fichas)
├── templates/       # Páginas HTML (Jinja)
├── static/
│   ├── css/style.css
│   └── js/progress.js   # Gráficos (Chart.js)
└── requirements.txt
```
