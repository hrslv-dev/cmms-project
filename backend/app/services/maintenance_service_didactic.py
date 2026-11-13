# Responsável pelos casos de uso relacionados a mnautenção 
# Definir cardinalidade desses relacionamentos 


class ManutencaoService: 
    def __init__(self, 
          manutencao_repository, 
          tecnico_repository,
          operador_repository, 
          componente_repository,
          maquina_repository
    ):
        self.manutencao_repository = manutencao_repository, 
        self.tecnico_repository = tecnico_repository
        self.operador_repository = operador_repository, 
        self.componente_repository = componente_repository, 
        self.maquina_repository = maquina_repository
        