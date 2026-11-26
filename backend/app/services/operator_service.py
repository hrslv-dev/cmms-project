import re
import unicodedata

import sqlalchemy.orm as orm

from app.models.operator_model import OperatorModel
from app.repository.operator_repository import OperatorRepository
from app.services.exceptions import DuplicateOperatorError, InvalidOperatorNameError

# Mesmo limite da coluna ``operators.name VARCHAR(100)``.
NAME_MAX_LENGTH = 100

# Únicos caracteres aceitos além de letras e do espaço. Ligam partes de uma
# mesma palavra: "Ana-Maria", "D'Ávila".
_WORD_JOINERS = "-'"
_ALLOWED_NON_LETTERS = " " + _WORD_JOINERS


class OperatorService:
    """Casos de uso de operadores.

    Regras de ``create_operator`` (somente da aplicação; no banco,
    ``operators.name`` é só ``VARCHAR(100) NOT NULL``):

    1. Normalizar: tirar os espaços das pontas e reduzir espaços repetidos.
    2. Não pode ficar vazio.
    3. Mínimo de duas palavras (nome e sobrenome).
    4. Só letras, espaços, hífen e apóstrofo. Hífen e apóstrofo precisam
       ficar entre letras.
    5. No máximo 100 caracteres.
    6. Sem duplicidade (sem diferenciar maiúsculas de minúsculas).

    Ressalva da regra 6: a checagem é "ler, comparar, gravar". Duas
    transações simultâneas com o mesmo nome podem passar ambas pela leitura.
    Só um índice único no banco fecha essa brecha (decisão de esquema do
    usuário).

    Transação: cada método público é uma unidade de trabalho. Sucesso faz
    ``commit``; qualquer erro faz ``rollback`` e a exceção é relançada.
    """

    def __init__(self, session: orm.Session) -> None:
        self.session = session
        self.operator_repository = OperatorRepository(session)

    def create_operator(self, name: str) -> OperatorModel:
        """Cadastra um operador e devolve o registro gravado (``id``, ``name``).

        Levanta ``InvalidOperatorNameError`` se o nome violar as regras 1 a 5.
        Levanta ``DuplicateOperatorError``, com ``existing_id``, se o nome já
        estiver cadastrado.
        """
        try:
            normalized = self._validate_name(name)
            existing = self.operator_repository.search_by_name_ignore_case(normalized)
            if existing is not None:
                raise DuplicateOperatorError(existing.id, existing.name)
            operator = self.operator_repository.add(OperatorModel(name=normalized))
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        return operator

    def list_operators(self) -> list[OperatorModel]:
        """Lista todos os operadores em ordem alfabética (``id``, ``name``).

        Sem operadores, devolve a lista vazia. Só leitura: não faz ``commit``
        (ver ``MachineService``).
        """
        return self.operator_repository.list_ordered_by_name()

    # ------------------------------------------------------------------ regras

    @staticmethod
    def _validate_name(name: str) -> str:
        """Devolve o nome normalizado ou levanta ``InvalidOperatorNameError``.

        Não acessa o banco: aplica as regras 1 a 5, nessa ordem.
        """
        if not isinstance(name, str):
            raise InvalidOperatorNameError(
                f"O nome do operador deve ser texto, recebido: {name!r}."
            )

        # 1. Normalizar.
        # NFC junta letra + acento soltos em um só caractere: "e" + "́"
        # vira "é". Sem isso, um "José" digitado com acento decomposto (comum
        # em texto colado ou vindo do macOS) seria recusado na regra 4, pois o
        # acento solto não é letra, e não seria igual a "José" na regra 6.
        # ``split()`` sem argumento quebra em qualquer espaço em branco
        # (espaço, tab, quebra de linha) e descarta os das pontas; o ``join``
        # recoloca um único espaço entre as palavras.
        normalized = " ".join(unicodedata.normalize("NFC", name).split())

        # 2. Não pode ficar vazio.
        if not normalized:
            raise InvalidOperatorNameError("O nome do operador não pode ficar vazio.")

        # 3. Mínimo de duas palavras.
        words = normalized.split(" ")
        if len(words) < 2:
            raise InvalidOperatorNameError(
                "Informe nome e sobrenome do operador (mínimo de duas palavras)."
            )

        # 4. Só letras, espaços, hífen e apóstrofo.
        # ``str.isalpha()`` aceita letras acentuadas (é, ç, ã) e recusa
        # dígitos e símbolos.
        invalid = sorted(
            {ch for ch in normalized if not (ch.isalpha() or ch in _ALLOWED_NON_LETTERS)}
        )
        if invalid:
            shown = ", ".join(repr(ch) for ch in invalid)
            raise InvalidOperatorNameError(
                f"Caracteres não permitidos no nome: {shown}. "
                "Use só letras, espaços, hífen (-) e apóstrofo (')."
            )
        # Sem esta checagem, "Ana -" ou "- -" passariam: têm duas "palavras"
        # e só caracteres permitidos. Cada pedaço entre hífens/apóstrofos
        # precisa ser letra; ``"".isalpha()`` é False, o que também recusa
        # hífen na ponta ("Ana-") ou duplicado ("Ana--Maria").
        for word in words:
            if not all(part.isalpha() for part in re.split(r"[-']", word)):
                raise InvalidOperatorNameError(
                    f"Hífen e apóstrofo devem ficar entre letras, como em "
                    f"Ana-Maria ou D'Ávila. Revise {word!r}."
                )

        # 5. No máximo 100 caracteres.
        # ``len`` conta caracteres, como o ``VARCHAR(100)`` do PostgreSQL.
        if len(normalized) > NAME_MAX_LENGTH:
            raise InvalidOperatorNameError(
                f"O nome tem {len(normalized)} caracteres; "
                f"o máximo é {NAME_MAX_LENGTH}."
            )

        return normalized
