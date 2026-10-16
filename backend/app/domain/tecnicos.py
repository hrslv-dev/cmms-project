"""Cadastro de técnicos usado pelo CMMS.

Este arquivo descreve como cada técnico será guardado no banco de dados. Pense
na tabela como uma planilha: cada linha representa um técnico e cada coluna
guarda uma informação dele. O SQLAlchemy lê a classe abaixo e prepara essa
estrutura para que o restante do sistema possa salvar e consultar os cadastros.
"""

from sqlalchemy import CheckConstraint, Integer, PrimaryKeyConstraint, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Identity
from .base import Base


class Tecnico(Base):
    """Representa uma linha da tabela de técnicos.

    A herança de ``Base`` permite que o SQLAlchemy reconheça esta classe como
    algo que deve ser guardado no banco. ``__tablename__`` indica o nome da
    tabela onde os dados ficam. As declarações ``Mapped`` e ``mapped_column``
    descrevem as colunas e as regras que cada valor precisa respeitar.

    Atributos:
        id: Número único do técnico. O banco escolhe o próximo número quando
            um novo cadastro é salvo, então a pessoa que usa o sistema não
            precisa inventar nem digitar esse número.
        nome: Nome do técnico. É obrigatório; o banco não aceita gravar um
            cadastro sem esse valor.
        funcao: Função do técnico. Também é obrigatória e só pode ser
            ``Mecânico`` ou ``Eletricista``.

    Regras aplicadas pelo banco:
        ``pk_tecnicos`` identifica o ``id`` como chave primária. Isso faz com
        que cada cadastro tenha um número próprio, sem repetição.
        ``chk_tencicos_funcao`` confere a função antes de aceitar a gravação.
        Assim, a regra continua valendo mesmo se os dados forem enviados por
        outra parte do sistema que não seja esta classe.

    Em resumo, esta classe funciona como um formulário com três campos; as
    regras descritas aqui são conferidas pelo próprio banco ao salvar os dados.
    """

    __tablename__ = "tecnicos"
    __table_args__ = (
        CheckConstraint(
            "funcao IN ('Mecânico', 'Eletricista')",
            name="chk_tecnicos_funcao",
        ),
        PrimaryKeyConstraint("id", name="pk_tecnicos"),
    )

    id: Mapped[int] = mapped_column(Integer, Identity, nullable=False)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    funcao: Mapped[str] = mapped_column(String(200), nullable=False)
