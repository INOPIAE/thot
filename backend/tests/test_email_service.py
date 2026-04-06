import pytest
from app.utils.email_service import EmailService

@pytest.fixture
def email_service():
    return EmailService()

def test_send_email_reset_confirmation(email_service, monkeypatch):
    monkeypatch.setattr(email_service, "send_email", lambda *a, **kw: True)
    assert email_service.send_email_reset_confirmation("to@example.com", "token", "user", "en")

def test_send_email_reset_info(email_service, monkeypatch):
    monkeypatch.setattr(email_service, "send_email", lambda *a, **kw: True)
    assert email_service.send_email_reset_info("to@example.com", "user", "de")

def test_send_registration_confirmation_email(email_service, monkeypatch):
    monkeypatch.setattr(email_service, "send_email", lambda *a, **kw: True)
    assert email_service.send_registration_confirmation_email("to@example.com", "user", "link", 12, "en")

def test_send_password_reset_email(email_service, monkeypatch):
    monkeypatch.setattr(email_service, "send_email", lambda *a, **kw: True)
    assert email_service.send_password_reset_email("to@example.com", "user", "link", 1, "de", True)

def test_send_otp_reset_email(email_service, monkeypatch):
    monkeypatch.setattr(email_service, "send_email", lambda *a, **kw: True)
    assert email_service.send_otp_reset_email("to@example.com", "user", "link", 2, "en", False)

def test_send_email_change_confirmation(email_service, monkeypatch):
    monkeypatch.setattr(email_service, "send_email", lambda *a, **kw: True)
    assert email_service.send_email_change_confirmation("to@example.com", "user", "link", "code", 3)

def test_send_email_failure(email_service, monkeypatch):
    monkeypatch.setattr(email_service, "_create_smtp_connection", lambda *a, **kw: (_ for _ in ()).throw(Exception("fail")))
    result = email_service.send_email("to@example.com", "subj", "html", "plain")
    assert result is False

def test_send_email_success(email_service, monkeypatch):
    class DummySMTP:
        def sendmail(self, *a, **kw): return True
        def quit(self): return True
    monkeypatch.setattr(email_service, "_create_smtp_connection", lambda *a, **kw: DummySMTP())
    assert email_service.send_email("to@example.com", "subj", "<html></html>", "plain")
