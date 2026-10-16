from .config import Config
from sqlalchemy import create_engine
from sqlalchemy import QueuePool
from sqlalchemy.engine import URL 

class Engine_factory:
    """Monta URL e engine SQLAlchemy para a conexão PostgreSQL do CMMS."""

    def __init__(self):
        """Inicializador sem estado; a factory pode ser chamada diretamente pela classe."""
        pass

    @staticmethod
    def generate_url(): 
        """Cria e retorna a URL PostgreSQL a partir das variáveis carregadas por `Config`.

        Converte `DB_PORT` para inteiro. Não abre conexão; porta ausente ou inválida
        causa erro durante a conversão.
        """
        creds = Config.load_envar()
        url = URL.create(
            drivername="postgresql", 
            username=creds["DB_USER"], 
            password=creds["DB_PASSWORD"], 
            host=creds["DB_HOST"],
            port=int(creds["DB_PORT"]), 
            database=creds["DB_NAME"] 
        )
        return url 

    def create_db_engine():
        """Retorna uma engine SQLAlchemy configurada com pool e log SQL.

        Define pool de cinco conexões, até dez conexões excedentes, verificação
        de conexão antes do uso (`pool_pre_ping`) e emissão de SQL no console
        (`echo=True`). A engine normalmente só conecta ao banco quando utilizada.
        Este método não recebe `self`; chame-o pela classe.
        """
        url = Engine_factory.generate_url()
        engine = create_engine(
            url,
            pool_size=5, 
            # Quantidade máxima de conexões temporárias caso as 5 pools estiverem ocupadas
            max_overflow=10,
            # Confere se a conexão que está no pool ainda está viva. 
            pool_pre_ping=True, 
            # Boolean que confirma se deve se mostrar as querys SQL no console 
            echo=True) 
        
        return engine 
