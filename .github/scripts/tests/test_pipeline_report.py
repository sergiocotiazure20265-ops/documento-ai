import importlib.util
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

SCRIPT = Path(__file__).resolve().parents[1] / "send_pipeline_report.py"
spec = importlib.util.spec_from_file_location("pipeline_report", SCRIPT)
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


class PipelineReportTests(unittest.TestCase):
    def run_data(self, conclusion="success"):
        return dict(name="Build e Tests", conclusion=conclusion, run_number=3,
                    run_attempt=2, event="push", head_branch="main", head_sha="abc123",
                    html_url="https://github.com/owner/repo/actions/runs/123")

    def test_reports_success_failure_cancelled_and_skipped_steps(self):
        for outcome, expected in [("success", "SUCESSO"), ("failure", "FALHA"),
                                  ("cancelled", "CANCELADO")]:
            with self.subTest(outcome=outcome):
                jobs = [dict(name="Build", conclusion=outcome, steps=[
                    dict(number=1, name="Restore", conclusion=outcome),
                    dict(number=2, name="Build", conclusion="skipped")])]
                message = report.build_message("owner/repo", self.run_data(outcome), jobs)
                self.assertIn(expected, message["Subject"])
                self.assertEqual("sergio.coti@gmail.com", message["To"])
                body = message.get_content()
                self.assertIn("tentativa 2", message["Subject"])
                self.assertIn("NAO EXECUTADO", body)
                self.assertIn("dotnet restore DocumentoAI.sln", body)
                self.assertIn("Comando previsto (nao executado)", body)
                self.assertIn("actions/runs/123", body)

    def test_missing_password_does_not_connect_to_smtp(self):
        with patch.object(report.smtplib, "SMTP") as smtp:
            with self.assertRaises(ValueError):
                report.send_message(report.build_message("owner/repo", self.run_data(), []), "")
            smtp.assert_not_called()

    def test_uses_gmail_tls_and_configured_recipient(self):
        message = report.build_message("owner/repo", self.run_data(), [])
        with patch.object(report.smtplib, "SMTP") as smtp:
            report.send_message(message, "fake-test-secret")
            self.assertEqual(("smtp.gmail.com", 587), smtp.call_args.args)
            client = smtp.return_value
            client.starttls.assert_called_once()
            client.login.assert_called_once_with(report.MAILBOX, "fake-test-secret")
            client.send_message.assert_called_once_with(message)

    def test_retries_connection_on_ssl_port_before_sending(self):
        message = report.build_message("owner/repo", self.run_data(), [])
        with patch.object(report.smtplib, "SMTP", side_effect=report.smtplib.SMTPServerDisconnected), \
             patch.object(report.smtplib, "SMTP_SSL") as smtp:
            report.send_message(message, "fake-test-secret")
            self.assertEqual(("smtp.gmail.com", 465), smtp.call_args.args)
            smtp.return_value.send_message.assert_called_once_with(message)

    def test_quit_disconnection_does_not_repeat_accepted_email(self):
        message = report.build_message("owner/repo", self.run_data(), [])
        with patch.object(report.smtplib, "SMTP") as smtp:
            smtp.return_value.quit.side_effect = report.smtplib.SMTPServerDisconnected
            report.send_message(message, "fake-test-secret")
            smtp.return_value.send_message.assert_called_once_with(message)

    def test_does_not_retry_ambiguous_send(self):
        message = report.build_message("owner/repo", self.run_data(), [])
        with patch.object(report.smtplib, "SMTP") as smtp, \
             patch.object(report.smtplib, "SMTP_SSL") as fallback:
            smtp.return_value.send_message.side_effect = report.smtplib.SMTPServerDisconnected
            with self.assertRaises(report.smtplib.SMTPServerDisconnected):
                report.send_message(message, "fake-test-secret")
            fallback.assert_not_called()

    def test_fetches_pages_for_exact_run_attempt(self):
        first = MagicMock()
        first.read.return_value = __import__("json").dumps({"jobs": [{}] * 100}).encode()
        second = MagicMock()
        second.read.return_value = b'{"jobs": [{"name": "last"}]}'
        with patch.object(report, "urlopen") as request:
            request.side_effect = [MagicMock(__enter__=lambda _: first),
                                   MagicMock(__enter__=lambda _: second)]
            jobs = report.fetch_jobs("owner/repo", 123, 2, "fake-token")
            self.assertEqual(101, len(jobs))
            self.assertIn("/attempts/2/jobs?per_page=100&page=2",
                          request.call_args.args[0].full_url)


if __name__ == "__main__":
    unittest.main()
