// Funções puras da Tela 1: sem DOM e sem rede, testadas com `node --test`.

export const LONG_DURATION_MINUTES = 12 * 60;
export const CLOCK_SKEW_WARNING_MS = 2 * 60 * 1000;
export const EXPECTED_TIME_ZONE = "America/Sao_Paulo";

const pad = (n) => String(n).padStart(2, "0");

/**
 * Junta data ("2026-11-24") e hora ("14:10") do aparelho em ISO 8601 com o
 * fuso dele ("2026-11-24T14:10:00-03:00"). Devolve null se faltar algo ou se a
 * data não existir (30/02).
 */
export function toIsoWithOffset(date, time) {
  const d = /^(\d{4})-(\d{2})-(\d{2})$/.exec(date ?? "");
  const t = /^(\d{2}):(\d{2})$/.exec(time ?? "");
  if (!d || !t) return null;
  const [year, month, day, hour, minute] = [...d.slice(1), ...t.slice(1)].map(Number);
  const local = new Date(year, month - 1, day, hour, minute);
  if (local.getFullYear() !== year || local.getMonth() !== month - 1
      || local.getDate() !== day || local.getHours() !== hour) {
    return null;
  }
  const offset = -local.getTimezoneOffset(); // minutos a leste de UTC
  const sign = offset >= 0 ? "+" : "-";
  const abs = Math.abs(offset);
  return `${date}T${time}:00${sign}${pad(Math.floor(abs / 60))}:${pad(abs % 60)}`;
}

/** Minutos entre dois ISO; null se algum faltar. Negativo se o fim vier antes. */
export function durationMinutes(startIso, endIso) {
  if (!startIso || !endIso) return null;
  return Math.round((Date.parse(endIso) - Date.parse(startIso)) / 60000);
}

/** "2 h 30 min", "45 min", "1 d 3 h". Só para exibir. */
export function formatDuration(minutes) {
  if (minutes === null || minutes < 0) return "—";
  const days = Math.floor(minutes / 1440);
  const hours = Math.floor((minutes % 1440) / 60);
  const mins = minutes % 60;
  const parts = [];
  if (days) parts.push(`${days} d`);
  if (hours) parts.push(`${hours} h`);
  if (mins || parts.length === 0) parts.push(`${mins} min`);
  return parts.join(" ");
}

/**
 * Avisos de horário, calculados só na tela.
 * - endBeforeStart: erro, a API recusaria;
 * - longDuration: alerta, a API aceita;
 * - endInFuture: o fim passa do horário atual (corrigido pelo relógio do servidor).
 */
export function periodWarnings(startIso, endIso, nowMs) {
  const minutes = durationMinutes(startIso, endIso);
  return {
    endBeforeStart: minutes !== null && minutes < 0,
    longDuration: minutes !== null && minutes > LONG_DURATION_MINUTES,
    endInFuture: endIso !== null && endIso !== undefined && Date.parse(endIso) > nowMs + 60000,
  };
}

/** Data e hora locais de um instante, para preencher os campos ("Agora"). */
export function localParts(ms) {
  const d = new Date(ms);
  return {
    date: `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`,
    time: `${pad(d.getHours())}:${pad(d.getMinutes())}`,
  };
}

/**
 * Diferença entre o relógio do aparelho e o do servidor, a partir do
 * cabeçalho HTTP `Date` (precisão de 1 s). Positivo: servidor à frente.
 * Usa o meio da requisição para descontar o tempo de rede.
 */
export function clockOffsetMs(serverDateHeader, sentAtMs, receivedAtMs) {
  const server = Date.parse(serverDateHeader ?? "");
  if (Number.isNaN(server)) return null;
  return server - (sentAtMs + receivedAtMs) / 2;
}

/** Texto do aviso de relógio, ou null se a diferença for pequena. */
export function clockWarning(offsetMs) {
  if (offsetMs === null || Math.abs(offsetMs) <= CLOCK_SKEW_WARNING_MS) return null;
  const minutes = Math.round(Math.abs(offsetMs) / 60000);
  const direction = offsetMs < 0 ? "adiantado" : "atrasado";
  return `O relógio deste aparelho está ${minutes} min ${direction} em relação ao servidor. `
    + "Ajuste a hora do aparelho antes de registrar.";
}

/** Texto do aviso de fuso, ou null se for o esperado. */
export function timeZoneWarning(timeZone) {
  if (!timeZone || timeZone === EXPECTED_TIME_ZONE) return null;
  return `Este aparelho está no fuso "${timeZone}". Confira se a data e a hora estão certas.`;
}

/** Campos obrigatórios ainda vazios, na ordem da tela. */
export function missingFields(state) {
  const missing = [];
  if (!state.maintenanceType) missing.push("tipo de manutenção");
  if (!state.machineId) missing.push("máquina");
  if (state.maintenanceType === "Corretiva" && !state.problem) missing.push("problema");
  if (!state.technicianId) missing.push("técnico");
  if (!toIsoWithOffset(state.startDate, state.startTime)) missing.push("início");
  if (!toIsoWithOffset(state.endDate, state.endTime)) missing.push("fim");
  if (!state.service) missing.push("serviço realizado");
  return missing;
}

/**
 * Corpo de POST /maintenances. Omite o que não foi preenchido, nunca envia ""
 * e só envia `problem` em Corretiva.
 */
export function buildMaintenanceBody(state) {
  const body = {
    machine_id: Number(state.machineId),
    technician_id: Number(state.technicianId),
    started_at: toIsoWithOffset(state.startDate, state.startTime),
    finished_at: toIsoWithOffset(state.endDate, state.endTime),
    service: state.service,
    maintenance_type: state.maintenanceType,
    subset_ids: [...state.subsetIds].map(Number),
  };
  if (state.operatorId) body.operator_id = Number(state.operatorId);
  if (state.maintenanceType === "Corretiva" && state.problem) body.problem = state.problem;
  const description = (state.description ?? "").trim();
  if (description) body.description = description;
  return body;
}

/** "25/11/2026 14:10" para o resumo; "—" se faltar algo. */
export function formatLocalDateTime(date, time) {
  const d = /^(\d{4})-(\d{2})-(\d{2})$/.exec(date ?? "");
  if (!d || !/^\d{2}:\d{2}$/.test(time ?? "")) return "—";
  return `${d[3]}/${d[2]}/${d[1]} ${time}`;
}

/** Minutos de uma duração ISO 8601 da API ("PT2H30M", "P1DT2H", "PT0S"). */
export function isoDurationToMinutes(value) {
  const m = /^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?)?$/.exec(value ?? "");
  if (!m || value === "P" || value === "PT") return null;
  const [days, hours, minutes, seconds] = m.slice(1).map((v) => Number(v ?? 0));
  return days * 1440 + hours * 60 + minutes + Math.round(seconds / 60);
}

// Campo da API -> seção da tela que mostra o erro.
const FIELD_SECTIONS = {
  maintenance_type: "maintenance_type", machine_id: "machine_id", subset_ids: "subset_ids",
  problem: "problem", technician_id: "technician_id", operator_id: "operator_id",
  started_at: "period", finished_at: "period", service: "service", description: "description",
};
const RESOURCE_SECTIONS = {
  machine: "machine_id", subset: "subset_ids", technician: "technician_id", operator: "operator_id",
};

/**
 * Onde mostrar cada erro da API: lista de {section, message}. `section` null
 * significa "no topo do formulário". Decide pelo `code`, nunca pelo texto.
 */
export function errorPlacements(code, message, details = {}) {
  if (code === "validation_error") {
    const errors = details.errors?.length ? details.errors : [{ field: null, message }];
    return errors.map((error) => ({
      section: FIELD_SECTIONS[String(error.field ?? "").split(".")[0]] ?? null,
      message: error.message,
    }));
  }
  const section = {
    not_found: RESOURCE_SECTIONS[details.resource],
    subset_machine_mismatch: "subset_ids",
    invalid_maintenance_period: "period",
    invalid_problem: "problem",
    invalid_service: "service",
    invalid_maintenance_type: "maintenance_type",
    invalid_description: "description",
  }[code];
  return [{ section: section ?? null, message }];
}
