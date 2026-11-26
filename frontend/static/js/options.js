// Listas fixas do backend (backend/app/services/enums.py), na mesma ordem.
// Mantidas em formato JSON: backend/tests/unit/test_frontend.py compara com os
// Enums e falha se um lado mudar sozinho.

export const MAINTENANCE_TYPES = ["Corretiva", "Preventiva"];

export const SERVICES = [
  "Inspeção",
  "Lubrificação",
  "Substituição",
  "Ajuste",
  "Limpeza",
  "Reparo",
  "Instalação",
  "Configuração",
  "Calibração",
  "Modificação"
];

export const PROBLEMS = ["Mecânico", "Elétrico", "Outro"];
