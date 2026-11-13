# Responsável pelos casos de uso relacionados a mnautenção 
# Definir cardinalidade desses relacionamentos 


class MaintenanceService: 
    def __init__(self, 
          maintenance_repository, 
          technician_repository,
          operator_repository, 
          subset_repository,
          machine_repository
    ):
        self.maintenance_repository = maintenance_repository, 
        self.technician_repository = technician_repository
        self.operator_repository = operator_repository, 
        self.subset_repository = subset_repository, 
        self.machine_repository = machine_repository
        
