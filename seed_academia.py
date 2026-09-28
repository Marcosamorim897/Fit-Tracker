"""Cria as fichas A, B e C da academia no Fit-Tracker pela linha de comando.

Pelo app não é preciso rodar nada: em /fichas há o botão "Importar fichas da
academia". Este script é para popular uma conta direto no banco.

Uso (igual ao seed_plano.py):
    python seed_academia.py --email voce@exemplo.com
    python seed_academia.py --email voce@exemplo.com --substituir

Para gravar no banco de produção (Neon), defina a DATABASE_URL antes de
rodar — no PowerShell:
    $env:DATABASE_URL = "postgresql://..."
"""

from fichas_academia import FICHAS
from seed_plano import main

if __name__ == "__main__":
    main(FICHAS, "Popula as fichas A, B e C da academia.")
