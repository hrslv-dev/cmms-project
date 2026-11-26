"""Garante que a suíte não alcança o banco real."""

from app.infrastructure.conf.config import Config


def test_real_credentials_are_blocked():
    assert Config.load_envar()["DB_NAME"] == "blocked_by_tests"


def test_session_uses_disposable_database(session):
    url = session.get_bind().engine.url
    assert (url.host, url.database, url.username) == ("127.0.0.1", "cmms_test", "tester")
