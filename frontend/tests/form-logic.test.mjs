// Executar na pasta frontend: TZ=America/Sao_Paulo node --test tests/
// O fuso é fixado para o resultado não depender da máquina.

import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildMaintenanceBody, clockOffsetMs, clockWarning, durationMinutes, formatDuration,
  localParts, missingFields, periodWarnings, timeZoneWarning, toIsoWithOffset,
} from "../static/js/form-logic.js";

test("fuso fixado para os testes", () => {
  assert.equal(Intl.DateTimeFormat().resolvedOptions().timeZone, "America/Sao_Paulo");
});

test("data e hora viram ISO com o fuso do aparelho", () => {
  assert.equal(toIsoWithOffset("2026-11-24", "14:10"), "2026-11-24T14:10:00-03:00");
});

test("data incompleta ou inexistente não vira ISO", () => {
  for (const [date, time] of [["", "14:10"], ["2026-11-24", ""], ["2026-02-30", "08:00"],
                              ["24/11/2026", "14:10"], [undefined, undefined]]) {
    assert.equal(toIsoWithOffset(date, time), null, `${date} ${time}`);
  }
});

test("duração em minutos, inclusive cruzando a meia-noite", () => {
  const a = toIsoWithOffset("2026-11-23", "22:00");
  assert.equal(durationMinutes(a, toIsoWithOffset("2026-11-24", "02:30")), 270);
  assert.equal(durationMinutes(a, a), 0);
  assert.equal(durationMinutes(a, toIsoWithOffset("2026-11-23", "21:00")), -60);
  assert.equal(durationMinutes(a, null), null);
});

test("duração formatada para leitura", () => {
  assert.equal(formatDuration(0), "0 min");
  assert.equal(formatDuration(150), "2 h 30 min");
  assert.equal(formatDuration(1440 + 180), "1 d 3 h");
  assert.equal(formatDuration(null), "—");
  assert.equal(formatDuration(-5), "—");
});

test("avisos de horário", () => {
  const start = toIsoWithOffset("2026-11-24", "08:00");
  const now = Date.parse("2026-11-24T12:00:00-03:00");
  const at = (time) => periodWarnings(start, toIsoWithOffset("2026-11-24", time), now);
  assert.deepEqual(at("07:59"), { endBeforeStart: true, longDuration: false, endInFuture: false });
  assert.deepEqual(at("08:00"), { endBeforeStart: false, longDuration: false, endInFuture: false });
  assert.equal(at("13:00").endInFuture, true);
  const long = periodWarnings(start, toIsoWithOffset("2026-11-24", "20:01"), Date.parse("2026-11-25T00:00:00-03:00"));
  assert.equal(long.longDuration, true);
});

test("'Agora' usa o instante recebido, no horário local", () => {
  assert.deepEqual(localParts(Date.parse("2026-11-24T17:05:00Z")), { date: "2026-11-24", time: "14:05" });
});

test("diferença de relógio pelo cabeçalho Date", () => {
  const sent = Date.parse("2026-11-24T12:00:00Z");
  assert.equal(clockOffsetMs("Tue, 24 Nov 2026 12:10:00 GMT", sent, sent + 2000), 10 * 60000 - 1000);
  assert.equal(clockOffsetMs(null, sent, sent), null);
  assert.equal(clockOffsetMs("inválido", sent, sent), null);
});

test("aviso de relógio só acima de 2 minutos, com o sentido certo", () => {
  assert.equal(clockWarning(null), null);
  assert.equal(clockWarning(2 * 60000), null);
  assert.match(clockWarning(-10 * 60000), /10 min adiantado/);
  assert.match(clockWarning(10 * 60000), /10 min atrasado/);
});

test("aviso de fuso só fora de America/Sao_Paulo", () => {
  assert.equal(timeZoneWarning("America/Sao_Paulo"), null);
  assert.match(timeZoneWarning("UTC"), /"UTC"/);
});

const filled = {
  maintenanceType: "Corretiva", machineId: "1", problem: "Mecânico", technicianId: "2",
  operatorId: "", startDate: "2026-11-24", startTime: "14:10", endDate: "2026-11-24",
  endTime: "16:40", service: "Reparo", subsetIds: new Set(["4", "3"]), description: "  ",
};

test("pendências em ordem; problema só exigido em Corretiva", () => {
  assert.deepEqual(missingFields(filled), []);
  assert.deepEqual(missingFields({ ...filled, problem: null }), ["problema"]);
  assert.deepEqual(missingFields({ ...filled, maintenanceType: "Preventiva", problem: null }), []);
  assert.deepEqual(missingFields({ subsetIds: new Set() }), [
    "tipo de manutenção", "máquina", "técnico", "início", "fim", "serviço realizado",
  ]);
});

test("corpo enviado: números, ISO com fuso e campos vazios omitidos", () => {
  assert.deepEqual(buildMaintenanceBody(filled), {
    machine_id: 1, technician_id: 2,
    started_at: "2026-11-24T14:10:00-03:00", finished_at: "2026-11-24T16:40:00-03:00",
    service: "Reparo", maintenance_type: "Corretiva", subset_ids: [4, 3], problem: "Mecânico",
  });
});

test("Preventiva nunca envia problema, nem vazio", () => {
  const body = buildMaintenanceBody({ ...filled, maintenanceType: "Preventiva" });
  assert.equal("problem" in body, false);
});

test("operador e descrição entram só quando preenchidos", () => {
  const body = buildMaintenanceBody({ ...filled, operatorId: "5", description: " Troca " });
  assert.equal(body.operator_id, 5);
  assert.equal(body.description, "Troca");
});

import { errorPlacements, formatLocalDateTime, isoDurationToMinutes } from "../static/js/form-logic.js";

test("data e hora do resumo", () => {
  assert.equal(formatLocalDateTime("2026-11-25", "14:10"), "25/11/2026 14:10");
  assert.equal(formatLocalDateTime("2026-11-25", ""), "—");
});

test("duração ISO 8601 devolvida pela API", () => {
  assert.equal(isoDurationToMinutes("PT2H30M"), 150);
  assert.equal(isoDurationToMinutes("P1DT2H"), 1560);
  assert.equal(isoDurationToMinutes("PT0S"), 0);
  assert.equal(isoDurationToMinutes("PT30S"), 1);
  assert.equal(isoDurationToMinutes("2h"), null);
  assert.equal(isoDurationToMinutes(undefined), null);
});

test("erros de validação vão para a seção do campo; sem campo, para o topo", () => {
  const placed = errorPlacements("validation_error", "Confira os campos informados.", {
    errors: [{ field: "subset_ids.1", message: "a" }, { field: "finished_at", message: "b" },
             { field: null, message: "c" }, { field: "desconhecido", message: "d" }],
  });
  assert.deepEqual(placed.map((p) => p.section), ["subset_ids", "period", null, null]);
});

test("erros de regra vão para a seção ligada ao code", () => {
  assert.equal(errorPlacements("not_found", "m", { resource: "machine", id: 9 })[0].section, "machine_id");
  assert.equal(errorPlacements("not_found", "m", { resource: "maintenance" })[0].section, null);
  assert.equal(errorPlacements("subset_machine_mismatch", "m", {})[0].section, "subset_ids");
  assert.equal(errorPlacements("invalid_maintenance_period", "m")[0].section, "period");
  assert.equal(errorPlacements("code_novo", "m")[0].section, null);
});
