"""Cronômetro de manutenção baseado em token assinado.

Fluxo no front end: "Iniciar manutenção" → "Encerrar manutenção" → cadastro.
Nada é gravado no banco antes do cadastro; os horários vêm do RELÓGIO DO
SERVIDOR e viajam até o cadastro dentro de um token que o front end guarda.

Formato do token::

    base64url(JSON) "." base64url(HMAC-SHA256(chave, base64url(JSON)))

- O JSON NÃO é criptografado: o front end pode decodificá-lo para exibir o
  cronômetro.
- O HMAC é uma "assinatura" com chave secreta que só o servidor conhece.
  Qualquer alteração no JSON (por exemplo, adiantar a hora de início) gera
  uma assinatura diferente, e o token é recusado. Sem a chave, não é possível
  produzir uma assinatura válida.

Limitações (decorrentes de não gravar nada antes do cadastro):

1. Manutenções em andamento não existem no banco: ninguém além do dispositivo
   que iniciou sabe que estão acontecendo.
2. O token vive no front end. Na memória da página, fechar a aba o perde; no
   ``localStorage``, sobrevive, mas só naquele navegador e dispositivo.
3. O servidor não guarda estado: o mesmo token encerrado pode ser enviado
   duas vezes e gerar duas manutenções. O front end deve descartá-lo após o
   cadastro.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.services.exceptions import InvalidTimerTokenError, TimerStateError

TOKEN_VERSION = 1


class TimerConfigurationError(RuntimeError):
    """Configuração ausente ou inválida (erro de implantação, não de domínio)."""


@dataclass(frozen=True)
class TimerData:
    """Conteúdo verificado de um token: horários com fuso do servidor."""

    start: datetime
    end: datetime | None


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64decode(text: str) -> bytes:
    """Decodifica base64url aceitando SOMENTE a forma que ``_b64encode`` produz.

    O decodificador do Python é tolerante: descarta caracteres fora do
    alfabeto (``"abc!!"`` vira ``"abc"``) e aceita mais de uma grafia para os
    mesmos bytes, porque o último caractere carrega bits de sobra. Com isso,
    várias strings diferentes seriam aceitas como o mesmo token. Reencodificar
    o resultado e comparar com o texto recebido garante uma única forma válida.
    """
    # O "=" de preenchimento é removido no token; aqui ele é recolocado.
    raw = base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))
    if _b64encode(raw) != text:
        raise ValueError("base64url fora da forma canônica.")
    return raw


class MaintenanceTimer:
    """Emite e verifica tokens de início/fim com o relógio do servidor."""

    def __init__(
        self,
        secret: str | bytes,
        tz: ZoneInfo,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not secret:
            raise TimerConfigurationError("A chave do cronômetro não pode ser vazia.")
        self._secret = secret.encode() if isinstance(secret, str) else secret
        self.tz = tz
        # Relógio injetável: os testes passam um relógio falso; em produção é
        # a hora atual do servidor, já no fuso configurado.
        self._clock = clock or (lambda: datetime.now(tz))

    @classmethod
    def from_env(cls) -> MaintenanceTimer:
        """Cria o cronômetro a partir do `.env` (via ``Config``)."""
        from app.infrastructure.conf.config import Config

        settings = Config.load_timer_settings()
        secret = settings["MAINTENANCE_TIMER_SECRET"]
        if not secret:
            raise TimerConfigurationError(
                "MAINTENANCE_TIMER_SECRET não está definido no .env."
            )
        tz_name = settings["MAINTENANCE_TIMEZONE"]
        try:
            tz = ZoneInfo(tz_name)
        # ZoneInfoNotFoundError: nome bem formado, mas inexistente ("Fuso/X").
        # ValueError: nome malformado ("" ou "../algo").
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise TimerConfigurationError(
                f"MAINTENANCE_TIMEZONE inválido: {tz_name!r}. "
                "Use um nome da base IANA, como 'America/Sao_Paulo'."
            ) from exc
        return cls(secret, tz)

    # ----------------------------------------------------------------- público

    def start(self) -> str:
        """Botão "Iniciar": token com a hora de início."""
        return self._sign({"v": TOKEN_VERSION, "start": self._now().isoformat()})

    def finish(self, token: str) -> str:
        """Botão "Encerrar": novo token com início e fim."""
        data = self.read(token)
        if data.end is not None:
            raise TimerStateError("Esta manutenção já foi encerrada.")
        return self._sign(
            {
                "v": TOKEN_VERSION,
                "start": data.start.isoformat(),
                "end": self._now().isoformat(),
            }
        )

    def read(self, token: str) -> TimerData:
        """Verifica a assinatura e devolve os horários; recusa tokens inválidos."""
        try:
            payload_part, signature_part = token.split(".")
            expected = self._signature(payload_part)
            # compare_digest leva o mesmo tempo independentemente de onde as
            # assinaturas diferem, o que impede descobrir a assinatura correta
            # medindo o tempo de resposta.
            if not hmac.compare_digest(_b64decode(signature_part), expected):
                raise InvalidTimerTokenError("Assinatura do token inválida.")
            payload = json.loads(_b64decode(payload_part))
            if payload.get("v") != TOKEN_VERSION:
                raise InvalidTimerTokenError("Versão de token não suportada.")
            start = datetime.fromisoformat(payload["start"])
            end = datetime.fromisoformat(payload["end"]) if "end" in payload else None
        except InvalidTimerTokenError:
            raise
        except (ValueError, KeyError, TypeError, AttributeError, binascii.Error) as exc:
            raise InvalidTimerTokenError("Token do cronômetro malformado.") from exc
        return TimerData(start=start.astimezone(self.tz),
                         end=end.astimezone(self.tz) if end else None)

    # ----------------------------------------------------------------- interno

    def _now(self) -> datetime:
        now = self._clock()
        if now.tzinfo is None:
            raise TimerConfigurationError("O relógio deve devolver datetime com fuso.")
        # Sem microssegundos: a coluna TIME do banco não precisa dessa precisão.
        return now.astimezone(self.tz).replace(microsecond=0)

    def _signature(self, payload_part: str) -> bytes:
        return hmac.new(self._secret, payload_part.encode("ascii"), hashlib.sha256).digest()

    def _sign(self, payload: dict) -> str:
        payload_part = _b64encode(
            json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
        )
        return f"{payload_part}.{_b64encode(self._signature(payload_part))}"
