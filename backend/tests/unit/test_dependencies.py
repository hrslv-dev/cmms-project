"""Sessão por requisição: sempre fechada, com sucesso ou erro."""

import pytest

from app.api import dependencies


class FakeSession:
    closed = False

    def close(self):
        self.closed = True


@pytest.fixture
def fake(monkeypatch):
    session = FakeSession()
    monkeypatch.setattr(dependencies, "create_session", lambda: session)
    return session


def test_session_is_closed_after_success(fake):
    generator = dependencies.get_session()
    assert next(generator) is fake and not fake.closed
    with pytest.raises(StopIteration):
        next(generator)
    assert fake.closed


def test_session_is_closed_after_error(fake):
    generator = dependencies.get_session()
    next(generator)
    with pytest.raises(RuntimeError):
        generator.throw(RuntimeError())
    assert fake.closed
