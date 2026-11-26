// Tela 1: liga os dados da API aos campos. Regras de negócio ficam na API;
// aqui só se evita enviar o que ela já recusaria e se explicam os erros.

import {
  api, ApiError, getClockOffset, NetworkError, onClockOffset, serverNow,
} from "./api.js";
import {
  buildMaintenanceBody, clockWarning, durationMinutes, errorPlacements, formatDuration,
  formatLocalDateTime, isoDurationToMinutes, localParts, missingFields, periodWarnings,
  timeZoneWarning, toIsoWithOffset,
} from "./form-logic.js";
import { MAINTENANCE_TYPES, PROBLEMS, SERVICES } from "./options.js";

const $ = (id) => document.getElementById(id);

const state = {
  maintenanceType: null,
  machineId: null,
  subsetIds: new Set(),
  problem: null,
  technicianId: "",
  operatorId: "",
  startDate: "", startTime: "", endDate: "", endTime: "",
  service: null,
  description: "",
};

// Nomes para o resumo: a tela mostra nomes, a API recebe ids.
const names = { machines: new Map(), subsets: new Map(), technicians: new Map(), operators: new Map() };
let triedToSave = false;
let saved = false;

// ------------------------------------------------------------ utilidades

/** Caixa de mensagem. Texto sempre por textContent: nada vindo da API vira HTML. */
function message(kind, text, action) {
  const box = document.createElement("div");
  box.className = `message message-${kind}`;
  box.setAttribute("role", kind === "error" ? "alert" : "status");
  const span = document.createElement("span");
  span.textContent = text;
  box.append(span);
  if (action) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "btn btn-secondary";
    button.textContent = action.label;
    button.addEventListener("click", action.onClick);
    box.append(button);
  }
  return box;
}

const show = (container, ...boxes) => container.replaceChildren(...boxes);

/** Texto para o técnico, conforme o tipo de falha. */
function describeError(error) {
  if (error instanceof ApiError) return error.message;
  if (error instanceof NetworkError) {
    return error.kind === "timeout"
      ? "O servidor demorou demais para responder. Os dados continuam na tela; tente de novo."
      : "Sem conexão com o servidor. Os dados continuam na tela; tente de novo.";
  }
  return error.message || "Algo deu errado. Tente de novo.";
}

/** Executa uma ação uma vez só: toques repetidos enquanto ela roda são ignorados. */
function once(button, busyLabel, action) {
  return async (...args) => {
    if (button.disabled) return;
    const label = button.textContent;
    button.disabled = true;
    button.setAttribute("aria-busy", "true");
    button.textContent = busyLabel;
    try {
      await action(...args);
    } finally {
      button.disabled = false;
      button.removeAttribute("aria-busy");
      button.textContent = label;
    }
  };
}

/** Opção nativa (rádio ou caixa de seleção) com aparência de botão. */
function choice({ type, name, value, label, checked, onChange, withCheck }) {
  const wrapper = document.createElement("label");
  wrapper.className = "choice";
  const input = document.createElement("input");
  input.type = type;
  input.name = name;
  input.value = value;
  input.checked = checked;
  input.addEventListener("change", () => onChange(input));
  const span = document.createElement("span");
  if (withCheck) {
    const check = document.createElement("span");
    check.className = "check";
    check.setAttribute("aria-hidden", "true");
    check.textContent = "✓";
    span.append(check);
  }
  span.append(label);
  wrapper.append(input, span);
  return wrapper;
}

/** Depois de cada alteração: limpa o erro daquela seção e atualiza o resumo. */
function changed(...sections) {
  sections.forEach(clearError);
  renderSummary();
}

// ----------------------------------------------------- erros por seção

const ERROR_INPUTS = {
  technician_id: ["technician"], operator_id: ["operator"],
  period: ["start-date", "start-time", "end-date", "end-time"], description: ["description"],
};

function setError(section, text) {
  show($(`error-${section}`), document.createTextNode(text));
  for (const id of ERROR_INPUTS[section] ?? []) $(id).setAttribute("aria-invalid", "true");
}

function clearError(section) {
  $(`error-${section}`)?.replaceChildren();
  for (const id of ERROR_INPUTS[section] ?? []) $(id).removeAttribute("aria-invalid");
}

function clearAllErrors() {
  $("form-error").replaceChildren();
  for (const element of document.querySelectorAll("[id^='error-']")) {
    clearError(element.id.slice("error-".length));
  }
}

/** Leva o foco (e a tela) até a seção, para o técnico ver o que corrigir. */
function focusSection(section) {
  const target = (section && $(`section-${section}`)) || $("form-error");
  target.scrollIntoView({ behavior: "smooth", block: "center" });
  target.focus({ preventScroll: true });
}

// ----------------------------------------------------------- cabeçalho

function setupTheme() {
  const root = document.documentElement;
  const toggle = $("theme-toggle");
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)");
  let stored = null;
  try { stored = localStorage.getItem("theme"); } catch { /* sem armazenamento */ }
  if (stored === "dark" || stored === "light") root.dataset.theme = stored;

  const isDark = () => (root.dataset.theme ?? (prefersDark.matches ? "dark" : "light")) === "dark";
  const render = () => {
    toggle.setAttribute("aria-pressed", String(isDark()));
    $("theme-label").textContent = isDark() ? "Modo claro" : "Modo escuro";
  };
  toggle.addEventListener("click", () => {
    root.dataset.theme = isDark() ? "light" : "dark";
    try { localStorage.setItem("theme", root.dataset.theme); } catch { /* idem */ }
    render();
  });
  prefersDark.addEventListener("change", render);
  render();
}

function setupLogo() {
  const img = $("brand-logo");
  const useImage = () => { img.hidden = false; $("brand-text").hidden = true; };
  if (img.complete && img.naturalWidth > 0) useImage();
  else img.addEventListener("load", useImage);
}

// ------------------------------------------------- avisos de relógio e fuso

const banners = { clock: null, timeZone: null };

function renderBanners() {
  const boxes = [banners.timeZone, banners.clock].filter(Boolean).map((text) => {
    const box = message("warn", text);
    box.classList.add("banner");
    return box;
  });
  show($("banners"), ...boxes);
}

function setupClockChecks() {
  banners.timeZone = timeZoneWarning(Intl.DateTimeFormat().resolvedOptions().timeZone);
  onClockOffset((offset) => {
    const text = clockWarning(offset);
    if (text !== banners.clock) {
      banners.clock = text;
      renderBanners();
    }
    renderPeriod(); // "fim no futuro" depende do relógio do servidor
  });
  renderBanners();
}

// ------------------------------------------------- tipo, problema, serviço

function renderTypes() {
  $("types").replaceChildren(...MAINTENANCE_TYPES.map((type) => choice({
    type: "radio", name: "maintenance_type", value: type, label: type,
    checked: state.maintenanceType === type,
    onChange: (input) => {
      state.maintenanceType = input.value;
      if (input.value !== "Corretiva") {
        state.problem = null; // nunca enviar problema escondido
        renderProblems();
      }
      $("section-problem").hidden = input.value !== "Corretiva";
      changed("maintenance_type", "problem");
    },
  })));
}

function renderProblems() {
  $("problems").replaceChildren(...PROBLEMS.map((problem) => choice({
    type: "radio", name: "problem", value: problem, label: problem,
    checked: state.problem === problem,
    onChange: (input) => { state.problem = input.value; changed("problem"); },
  })));
}

function renderServices() {
  $("services").replaceChildren(...SERVICES.map((service) => choice({
    type: "radio", name: "service", value: service, label: service,
    checked: state.service === service,
    onChange: (input) => { state.service = input.value; changed("service"); },
  })));
}

function setupDescription() {
  const open = $("description-open");
  open.addEventListener("click", () => {
    $("description-area").hidden = false;
    open.hidden = true;
    open.setAttribute("aria-expanded", "true");
    $("description").focus();
  });
  $("description").addEventListener("input", (event) => {
    state.description = event.target.value;
    changed("description");
  });
}

// ------------------------------------------------------ listas da API

/** Carrega uma lista mostrando "Carregando…" e, em falha, "Tentar de novo". */
async function loadList(statusElement, loadingText, load, render, onError) {
  statusElement.replaceChildren();
  statusElement.textContent = loadingText;
  try {
    const items = await load();
    statusElement.textContent = "";
    render(items);
  } catch (error) {
    statusElement.textContent = "";
    onError?.();
    show(statusElement, message("error", describeError(error), {
      label: "Tentar de novo",
      onClick: () => loadList(statusElement, loadingText, load, render, onError),
    }));
  }
}

const remember = (map, items) => {
  map.clear();
  items.forEach((item) => map.set(String(item.id), item.name));
};

function loadMachines() {
  return loadList($("machines-status"), "Carregando máquinas…", api.listMachines, (machines) => {
    remember(names.machines, machines);
    if (machines.length === 0) $("machines-status").textContent = "Nenhuma máquina cadastrada.";
    $("machines").replaceChildren(...machines.map((machine) => choice({
      type: "radio", name: "machine_id", value: String(machine.id), label: machine.name,
      checked: state.machineId === String(machine.id),
      onChange: (input) => selectMachine(input.value),
    })));
    renderSummary();
  });
}

let subsetRequest = 0;

function selectMachine(machineId) {
  state.machineId = machineId;
  state.subsetIds.clear(); // subconjuntos dependem da máquina
  changed("machine_id", "subset_ids");
  loadSubsets();
}

function loadSubsets() {
  const request = ++subsetRequest; // descarta respostas de uma máquina anterior
  $("subsets").replaceChildren();
  $("subsets-status").replaceChildren();
  if (!state.machineId) {
    $("subsets-hint").textContent = "Escolha a máquina para ver os subconjuntos.";
    return Promise.resolve();
  }
  $("subsets-hint").textContent = "Opcional. Selecione um ou mais.";
  return loadList(
    $("subsets-status"), "Carregando subconjuntos…",
    () => api.listSubsets(state.machineId),
    (subsets) => {
      if (request !== subsetRequest) return;
      remember(names.subsets, subsets);
      if (subsets.length === 0) {
        $("subsets-status").textContent = "Esta máquina não tem subconjuntos cadastrados.";
      }
      $("subsets").replaceChildren(...subsets.map((subset) => choice({
        type: "checkbox", name: "subset_ids", value: String(subset.id), label: subset.name,
        checked: state.subsetIds.has(String(subset.id)), withCheck: true,
        onChange: (input) => {
          if (input.checked) state.subsetIds.add(input.value);
          else state.subsetIds.delete(input.value);
          changed("subset_ids");
        },
      })));
      // Um subconjunto que sumiu da lista não pode continuar selecionado.
      for (const id of [...state.subsetIds]) if (!names.subsets.has(id)) state.subsetIds.delete(id);
      renderSummary();
    },
  );
}

function fillSelect(select, items, emptyLabel, selected) {
  const empty = new Option(emptyLabel, "");
  select.replaceChildren(empty, ...items.map((item) => new Option(item.name, String(item.id))));
  select.value = items.some((item) => String(item.id) === selected) ? selected : "";
}

function loadTechnicians() {
  const select = $("technician");
  return loadList($("technician-status"), "Carregando técnicos…", api.listTechnicians, (technicians) => {
    remember(names.technicians, technicians);
    fillSelect(select, technicians,
      technicians.length ? "Selecione o técnico" : "Nenhum técnico cadastrado", state.technicianId);
    state.technicianId = select.value;
    renderSummary();
  }, () => fillSelect(select, [], "Lista indisponível", ""));
}

function loadOperators() {
  const select = $("operator");
  return loadList($("operator-status"), "Carregando operadores…", api.listOperators, (operators) => {
    remember(names.operators, operators);
    fillSelect(select, operators, "Nenhum", state.operatorId);
    state.operatorId = select.value;
    renderSummary();
  }, () => {
    if (!state.operatorId) fillSelect(select, [], "Lista indisponível", "");
  });
}

// ------------------------------------------------------- novo operador

function setupNewOperator() {
  const panel = $("new-operator");
  const open = $("new-operator-open");
  const input = $("new-operator-name");
  const feedback = $("new-operator-message");
  const add = $("new-operator-add");

  const setOpen = (isOpen) => {
    panel.hidden = !isOpen;
    open.hidden = isOpen;
    open.setAttribute("aria-expanded", String(isOpen));
    feedback.replaceChildren();
    input.removeAttribute("aria-invalid");
    if (isOpen) {
      input.value = "";
      $("people-feedback").replaceChildren();
      input.focus();
    } else {
      open.focus();
    }
  };

  const select = async (operatorId, text) => {
    state.operatorId = String(operatorId);
    await loadOperators();
    $("operator").value = state.operatorId;
    changed("operator_id");
    setOpen(false);
    show($("people-feedback"), message("ok", text));
  };

  const submit = once(add, "Adicionando…", async () => {
    feedback.replaceChildren();
    input.removeAttribute("aria-invalid");
    try {
      const operator = await api.createOperator(input.value);
      await select(operator.id, `Operador ${operator.name} adicionado e selecionado.`);
    } catch (error) {
      if (error instanceof ApiError && error.code === "duplicate_operator") {
        const { existing_id: id, existing_name: name } = error.details;
        show(feedback, message("warn", `${name} já está cadastrado(a).`, {
          label: "Usar este cadastro",
          onClick: () => select(id, `Operador ${name} selecionado.`),
        }));
        return;
      }
      if (error instanceof ApiError) input.setAttribute("aria-invalid", "true");
      const text = error instanceof ApiError && error.code === "validation_error"
        ? error.details.errors?.[0]?.message ?? error.message
        : describeError(error);
      show(feedback, message("error", text));
      input.focus();
    }
  });

  open.addEventListener("click", () => setOpen(true));
  $("new-operator-cancel").addEventListener("click", () => setOpen(false));
  add.addEventListener("click", submit);
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") { event.preventDefault(); submit(); }
    if (event.key === "Escape") { event.preventDefault(); setOpen(false); }
  });
}

// ------------------------------------------------------------ horários

function currentPeriod() {
  const start = toIsoWithOffset(state.startDate, state.startTime);
  const end = toIsoWithOffset(state.endDate, state.endTime);
  return { start, end, warnings: periodWarnings(start, end, serverNow()) };
}

function renderPeriod() {
  const { start, end, warnings } = currentPeriod();
  const boxes = [];
  if (warnings.endBeforeStart) boxes.push(message("error", "O fim está antes do início. Confira as datas."));
  if (warnings.endInFuture) {
    boxes.push(message("error", "O fim está depois do horário atual. Registre só manutenções já encerradas."));
  }
  if (warnings.longDuration) boxes.push(message("warn", "A duração passa de 12 horas. Confira os horários."));
  show($("period-messages"), ...boxes);

  const invalid = warnings.endBeforeStart || warnings.endInFuture;
  for (const id of ["end-date", "end-time"]) {
    if (invalid) $(id).setAttribute("aria-invalid", "true");
    else if (!$("error-period").textContent) $(id).removeAttribute("aria-invalid");
  }
  $("elapsed").textContent = invalid ? "—" : formatDuration(durationMinutes(start, end));
  renderSummary();
}

function setupPeriod() {
  const fields = {
    "start-date": "startDate", "start-time": "startTime",
    "end-date": "endDate", "end-time": "endTime",
  };
  for (const [id, key] of Object.entries(fields)) {
    $(id).addEventListener("input", (event) => {
      state[key] = event.target.value;
      clearError("period");
      renderPeriod();
    });
  }
  $("end-now").addEventListener("click", () => {
    // Hora do servidor, para um relógio errado no aparelho não gravar horário errado.
    const now = localParts(serverNow());
    state.endDate = $("end-date").value = now.date;
    state.endTime = $("end-time").value = now.time;
    clearError("period");
    renderPeriod();
  });
}

// --------------------------------------------------------------- resumo

function renderSummary() {
  const subsets = [...state.subsetIds].map((id) => names.subsets.get(id)).filter(Boolean);
  const { start, end, warnings } = currentPeriod();
  const minutes = warnings.endBeforeStart ? null : durationMinutes(start, end);
  const rows = [
    ["Tipo", state.maintenanceType],
    ["Máquina", names.machines.get(state.machineId ?? "")],
    ["Subconjuntos", subsets.length ? subsets.join(", ") : "Nenhum"],
    ...(state.maintenanceType === "Corretiva" ? [["Problema", state.problem]] : []),
    ["Serviço", state.service],
    ["Técnico", names.technicians.get(state.technicianId)],
    ["Operador", state.operatorId ? names.operators.get(state.operatorId) : "Nenhum"],
    ["Início", formatLocalDateTime(state.startDate, state.startTime)],
    ["Fim", formatLocalDateTime(state.endDate, state.endTime)],
    ["Duração", formatDuration(minutes)],
  ];
  $("summary").replaceChildren(...rows.flatMap(([label, value]) => {
    const dt = document.createElement("dt");
    dt.textContent = label;
    const dd = document.createElement("dd");
    const empty = !value || value === "—";
    dd.textContent = empty ? "—" : value;
    if (empty) dd.classList.add("empty");
    return [dt, dd];
  }));

  const missing = missingFields(state);
  show($("missing"), ...(triedToSave && !saved && missing.length
    ? [message("error", `Falta preencher: ${missing.join(", ")}.`)]
    : []));
}

// ---------------------------------------------------------------- salvar

const MISSING_SECTION = {
  "tipo de manutenção": "maintenance_type", "máquina": "machine_id", "problema": "problem",
  "técnico": "technician_id", "início": "period", "fim": "period", "serviço realizado": "service",
};

function showApiError(error) {
  const placements = errorPlacements(error.code, error.message, error.details);
  const clockText = error.code === "invalid_maintenance_period" ? clockWarning(getClockOffset()) : null;
  for (const { section, message: text } of placements) {
    const full = clockText ? `${text} ${clockText}` : text;
    if (section) setError(section, full);
    else $("form-error").append(message("error", full));
  }
  // A lista na tela pode estar desatualizada (cadastro removido ou alterado).
  const resource = error.details.resource;
  if (error.code === "not_found" && resource === "machine") loadMachines();
  if (error.code === "not_found" && resource === "technician") loadTechnicians();
  if (error.code === "not_found" && resource === "operator") loadOperators();
  if ((error.code === "not_found" && resource === "subset") || error.code === "subset_machine_mismatch") {
    loadSubsets();
  }
  focusSection(placements[0].section);
}

function showSaveFailure(error) {
  if (error instanceof ApiError) {
    showApiError(error);
    return;
  }
  let text = describeError(error);
  if (error instanceof NetworkError && error.kind === "timeout") {
    text = "O servidor demorou demais para responder. A manutenção pode ter sido registrada: "
      + "confira antes de salvar de novo, para não duplicar o registro.";
  }
  $("form-error").append(message("error", text));
  focusSection(null);
}

function showSaved(maintenance) {
  saved = true;
  $("form").inert = true; // registro encerrado: nada mais a editar nele
  $("save").hidden = true;
  $("missing").replaceChildren();
  const minutes = isoDurationToMinutes(maintenance.elapsed_time);
  const box = message("ok", `Manutenção registrada (nº ${maintenance.id}, duração ${formatDuration(minutes)}).`, {
    label: "Registrar outra",
    onClick: resetForm,
  });
  box.classList.add("success");
  show($("save-result"), box);
  box.querySelector("button").focus();
}

/** Novo registro. Mantém só o técnico, que costuma registrar várias seguidas. */
function resetForm() {
  Object.assign(state, {
    maintenanceType: null, machineId: null, problem: null, operatorId: "",
    startDate: "", startTime: "", endDate: "", endTime: "", service: null, description: "",
  });
  state.subsetIds.clear();
  saved = false;
  triedToSave = false;
  for (const id of ["start-date", "start-time", "end-date", "end-time", "description"]) $(id).value = "";
  $("operator").value = "";
  $("description-area").hidden = true;
  $("description-open").hidden = false;
  $("description-open").setAttribute("aria-expanded", "false");
  $("section-problem").hidden = true;
  $("people-feedback").replaceChildren();
  $("save-result").replaceChildren();
  $("save").hidden = false;
  $("form").inert = false;
  clearAllErrors();
  renderTypes();
  renderProblems();
  renderServices();
  loadMachines();
  loadSubsets();
  renderPeriod();
  window.scrollTo({ top: 0, behavior: "smooth" });
  $("section-maintenance_type").focus({ preventScroll: true });
}

function setupSave() {
  const button = $("save");
  button.addEventListener("click", once(button, "Salvando…", async () => {
    if (saved) return;
    triedToSave = true;
    clearAllErrors();
    renderSummary();

    const missing = missingFields(state);
    if (missing.length) {
      focusSection(MISSING_SECTION[missing[0]]);
      return;
    }
    const { warnings } = currentPeriod();
    if (warnings.endBeforeStart || warnings.endInFuture) {
      focusSection("period");
      return;
    }
    try {
      showSaved(await api.createMaintenance(buildMaintenanceBody(state)));
    } catch (error) {
      showSaveFailure(error);
    }
  }));
}

// ---------------------------------------------------------------- início

function start() {
  setupTheme();
  setupLogo();
  setupClockChecks();
  renderTypes();
  renderProblems();
  renderServices();
  setupDescription();
  setupNewOperator();
  setupPeriod();
  setupSave();
  $("form").addEventListener("submit", (event) => event.preventDefault());
  $("technician").addEventListener("change", (event) => {
    state.technicianId = event.target.value;
    changed("technician_id");
  });
  $("operator").addEventListener("change", (event) => {
    state.operatorId = event.target.value;
    changed("operator_id");
  });
  loadSubsets();
  loadMachines();
  loadTechnicians();
  loadOperators();
  renderPeriod();
}

start();
