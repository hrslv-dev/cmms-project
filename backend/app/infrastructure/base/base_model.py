import sqlalchemy as sq
import sqlalchemy.orm as orm


class Base(orm.DeclarativeBase):
    """Base declarativa compartilhada por todos os models do CMMS.

    As sete tabelas do banco têm a mesma chave primária
    (``id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY``). Por ser comum a
    todas, a coluna é declarada uma única vez aqui; o SQLAlchemy cria uma cópia
    dela para a tabela de cada model que herda de ``Base``.

    ``Identity(always=True)`` informa ao ORM que o valor é gerado pelo banco:
    o ``INSERT`` não envia ``id`` e o valor gerado é lido de volta no ``flush``.
    Como a identidade é ``ALWAYS``, o PostgreSQL rejeita um ``id`` informado
    manualmente — por isso, nunca atribua ``id`` ao criar um objeto.
    """

    id: orm.Mapped[int] = orm.mapped_column(
        sq.Integer,
        sq.Identity(always=True),
        primary_key=True,
        # Mantém ``id`` como primeira coluna de cada tabela, como no banco.
        sort_order=-1,
    )
