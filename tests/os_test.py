"""Rascunho de carregamento de ambiente; não contém asserts nem testes.

Ao importar ou executar este módulo, `load_dotenv()` procura um arquivo `.env`
com base no contexto de execução e carrega seus valores no ambiente do processo.
"""

import os

from dotenv import load_dotenv

load_dotenv()

