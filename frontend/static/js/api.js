// Acesso à API. Três tipos de falha, tratados separadamente pela tela:
// - ApiError: a API respondeu com {code, message, details};
// - NetworkError: a resposta não chegou (sem conexão, servidor desligado, tempo esgotado);
// - UnexpectedResponseError: chegou algo fora do formato da API (ex.: 502 de um proxy).

import { clockOffsetMs } from "./form-logic.js";

const TIMEOUT_MS = 15000;

export class ApiError extends Error {
  constructor(status, body) {
    super(body.message);
    this.name = "ApiError";
    this.status = status;
    this.code = body.code;
    this.details = body.details ?? {};
  }
}

export class NetworkError extends Error {
  /** @param {"offline" | "timeout"} kind */
  constructor(kind) {
    super(kind === "timeout"
      ? "O servidor demorou demais para responder."
      : "Sem conexão com o servidor.");
    this.name = "NetworkError";
    this.kind = kind;
  }
}

export class UnexpectedResponseError extends Error {
  constructor(status) {
    super(`O servidor respondeu de forma inesperada (código ${status}).`);
    this.name = "UnexpectedResponseError";
    this.status = status;
  }
}

let offsetMs = null;
const clockListeners = new Set();

/** Diferença servidor − aparelho (ms), da última resposta; null se desconhecida. */
export const getClockOffset = () => offsetMs;

/** Avisa quando a diferença de relógio for medida. */
export function onClockOffset(listener) {
  clockListeners.add(listener);
  return () => clockListeners.delete(listener);
}

/** Agora, pelo relógio do servidor (ou do aparelho, se ainda não medido). */
export const serverNow = () => Date.now() + (offsetMs ?? 0);

async function request(method, path, body) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  const sentAt = Date.now();
  let response;
  try {
    response = await fetch(path, {
      method,
      headers: body === undefined ? {} : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    });
  } catch (error) {
    throw new NetworkError(error?.name === "AbortError" ? "timeout" : "offline");
  } finally {
    clearTimeout(timer);
  }

  const measured = clockOffsetMs(response.headers.get("Date"), sentAt, Date.now());
  if (measured !== null) {
    offsetMs = measured;
    clockListeners.forEach((listener) => listener(offsetMs));
  }

  let data;
  try {
    data = await response.json();
  } catch {
    throw new UnexpectedResponseError(response.status);
  }
  if (response.ok) return data;
  if (data && typeof data.code === "string" && typeof data.message === "string") {
    throw new ApiError(response.status, data);
  }
  throw new UnexpectedResponseError(response.status);
}

export const api = {
  listMachines: () => request("GET", "/machines"),
  listSubsets: (machineId) => request("GET", `/machines/${encodeURIComponent(machineId)}/subsets`),
  listTechnicians: () => request("GET", "/technicians"),
  listOperators: () => request("GET", "/operators"),
  createOperator: (name) => request("POST", "/operators", { name }),
  createMaintenance: (body) => request("POST", "/maintenances", body),
};
