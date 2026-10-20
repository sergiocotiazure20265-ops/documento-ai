"""Relatorio da tentativa concluida: somente biblioteca padrao, Gmail com TLS."""

import json
import os
import smtplib
import ssl
import sys
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from urllib.request import Request, urlopen

MAILBOX = "sergio.coti@gmail.com"
RESULTS = {
    "success": "SUCESSO", "failure": "FALHA", "cancelled": "CANCELADO",
    "skipped": "NAO EXECUTADO", "timed_out": "TEMPO ESGOTADO",
    "neutral": "NEUTRO", "action_required": "ACAO NECESSARIA",
    "startup_failure": "FALHA NA INICIALIZACAO", "stale": "OBSOLETO",
}
COMMANDS = {
    "Restore": "dotnet restore DocumentoAI.sln",
    "Build": "dotnet build DocumentoAI.sln --configuration Release --no-restore",
    "Tests": 'dotnet test DocumentoAI.sln --configuration Release --no-restore --logger "console;verbosity=normal"',
    "Tests do relatorio de email": "python3 -m unittest discover -s .github/scripts/tests -v",
}


def result_label(value):
    return RESULTS.get(value, value or "SEM RESULTADO")


def duration(start, end):
    if not start or not end:
        return "nao disponivel"
    seconds = (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds()
    return f"{max(0, seconds):.0f}s"


def fetch_jobs(repository, run_id, attempt, token):
    """Pagina somente os jobs da tentativa que gerou o evento, inclusive reexecucoes."""
    jobs = []
    page = 1
    while True:
        url = (f"https://api.github.com/repos/{repository}/actions/runs/{run_id}"
               f"/attempts/{attempt}/jobs?per_page=100&page={page}")
        request = Request(url, headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        with urlopen(request, timeout=30) as response:
            batch = json.load(response)["jobs"]
        jobs.extend(batch)
        if len(batch) < 100:
            return jobs
        page += 1


def build_message(repository, run, jobs):
    result = result_label(run.get("conclusion"))
    message = EmailMessage()
    message["From"] = MAILBOX
    message["To"] = MAILBOX
    message["Subject"] = (f"[DocumentAI] {result} - pipeline #{run['run_number']}"
                          f" - tentativa {run['run_attempt']}")
    lines = [
        "RELATORIO DE EXECUCAO — DocumentAI", "",
        f"Resultado geral: {result}",
        f"Workflow: {run['name']}",
        f"Repositorio: {repository}",
        f"Execucao: #{run['run_number']} / tentativa {run['run_attempt']}",
        f"Evento: {run['event']}",
        f"Branch: {run.get('head_branch') or 'nao disponivel'}",
        f"Commit: {run['head_sha']}",
        f"Responsavel pelo acionamento: {run.get('triggering_actor', run.get('actor', {})).get('login', 'nao disponivel')}",
        f"Inicio (UTC): {run.get('run_started_at', 'nao disponivel')}",
        f"Atualizacao final (UTC): {run.get('updated_at', 'nao disponivel')}",
        f"Execucao e logs: {run['html_url']}", "",
        "JOBS E PASSOS EXECUTADOS",
    ]
    if not jobs:
        lines.append("GitHub nao disponibilizou jobs para esta tentativa.")
    for job in jobs:
        lines.extend([
            "", f"Job: {job['name']} — {result_label(job.get('conclusion'))}",
            f"Inicio (UTC): {job.get('started_at') or 'nao iniciado'}",
            f"Fim (UTC): {job.get('completed_at') or 'nao disponivel'}",
            f"Duracao: {duration(job.get('started_at'), job.get('completed_at'))}",
            f"Logs do job: {job.get('html_url', run['html_url'])}",
        ])
        for step in job.get("steps", []):
            lines.append(
                f"  {step['number']}. {step['name']}: {result_label(step.get('conclusion'))}"
                f" | duracao: {duration(step.get('started_at'), step.get('completed_at'))}")
            if step["name"] in COMMANDS:
                label = "Comando previsto (nao executado)" if step.get("conclusion") == "skipped" else "Comando"
                lines.append(f"     {label}: {COMMANDS[step['name']]}")
    lines.extend([
        "", "Deploy: nao configurado e nao executado.",
        "Este relatorio detalha os resultados dos passos informados pelo GitHub.",
        "Saidas dos comandos, falhas e resultados individuais dos testes estao nos links de logs.",
        "Logs brutos e credenciais nao sao incluidos no email.",
    ])
    message.set_content("\n".join(lines))
    return message


def send_message(message, password):
    if not password:
        raise ValueError("Cadastre a senha de app do Gmail em Actions Secret SMTP_PASSWORD.")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30,
                          context=ssl.create_default_context()) as client:
        client.login(MAILBOX, password)
        client.send_message(message)


def main():
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
    run = event["workflow_run"]
    repository = os.environ["GITHUB_REPOSITORY"]
    if run["repository"]["full_name"] != repository or run["name"] != "Build e Tests":
        raise ValueError("Evento fora da pipeline esperada.")
    jobs = fetch_jobs(repository, int(run["id"]), int(run["run_attempt"]), os.environ["GH_TOKEN"])
    message = build_message(repository, run, jobs)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        # Mantem uma copia legivel no resumo mesmo quando o SMTP nao estiver configurado.
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write("## Relatorio de email\n\n")
            summary.write("\n".join("    " + line for line in message.get_content().splitlines()))
            summary.write("\n")
    send_message(message, os.environ.get("SMTP_PASSWORD", ""))
    print("Relatorio aceito pelo SMTP do Gmail para envio a " + MAILBOX)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # Nao imprimir respostas externas que possam conter credenciais.
        print(f"Falha ao enviar relatorio ({type(error).__name__}). "
              "Confira o secret SMTP_PASSWORD, a senha de app do Gmail e a disponibilidade do servico.",
              file=sys.stderr)
        sys.exit(1)
