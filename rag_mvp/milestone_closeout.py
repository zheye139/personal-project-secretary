import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import config


# ============================================================
# base configuration
# ============================================================

KNOWLEDGE_ROOT = config.KNOWLEDGE_ROOT

MILESTONE_REPORT_DIR = getattr(
    config,
    "MILESTONE_REPORT_DIR",
    KNOWLEDGE_ROOT / "05_Summaries" / "milestone_reports",
)

BASE_DIR = Path(__file__).parent.resolve()


# ============================================================
# Windows / PowerShell English output 
# ============================================================

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

def run_command(title: str, command: list[str], timeout: int = 900) -> tuple[bool, str]:
    """
    execute a command, and :
    1. whetherOK
    2.  content

    purpose:
    - execute health_check_full.py
    - execute status.py
    - execute list_docs.py
    - execute search_docs.py
    """
    print("\n" + "=" * 80)
    print(f"start:{title}")
    print("=" * 80)
    print("command:", " ".join(command))
    print("")

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        result = subprocess.run(
            command,
            cwd=BASE_DIR,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout,
            env=env,
        )
    except Exception as e:
        output = f"[exception] {e}"
        print(output)
        return False, output

    output_parts = []

    if result.stdout:
        output_parts.append(result.stdout)

    if result.stderr:
        output_parts.append("[stderr]\n" + result.stderr)

    output = "\n".join(output_parts)

    if output:
        print(output)

    if result.returncode != 0:
        print(f"[failed] {title}, return code:{result.returncode}")
        return False, output

    print(f"[completed] {title}")
    return True, output

def get_milestone_config(milestone: str) -> dict:
    """
     milestonename configuration. 

     :
    - M1:Local RAG MVP Enhancement Stage
    - M2:Personal Secretary Capability Enhancement Stage

    later M3/M4 can inthisin . 
    """
    milestone_upper = milestone.upper()

    if milestone_upper == "M1":
        return {
            "title": "M1 milestone closeout report",
            "doc_type": "milestone_report",
            "tags": "[M1, milestone closeout, RAG, auto generated]",
            "focus": "Local RAG MVP Enhancement Stage",
            "summary_lines": build_m1_summary_lines(),
            "extra_checks": [
                (
                    "check M1  document",
                    [
                        sys.executable,
                        "search_docs.py",
                        "--tag",
                        "M1",
                        "M1 stagecompleted ？",
                    ],
                ),
            ],
        }

    if milestone_upper == "M2":
        return {
            "title": "M2 milestone closeout report",
            "doc_type": "milestone_report",
            "tags": "[M2, milestone closeout, personal secretary,  capability, auto generated]",
            "focus": "Personal Secretary Capability Enhancement Stage",
            "summary_lines": build_m2_summary_lines(),
            "extra_checks": [
                (
                    "check next_action_report",
                    [
                        sys.executable,
                        "search_docs.py",
                        "--doc-type",
                        "next_action_report",
                        "next action list",
                    ],
                ),
                (
                    "check project_brief",
                    [
                        sys.executable,
                        "search_docs.py",
                        "--doc-type",
                        "project_brief",
                        "project brief",
                    ],
                ),
                (
                    "check multi_project_status",
                    [
                        sys.executable,
                        "search_docs.py",
                        "--doc-type",
                        "multi_project_status",
                        "multi-project status summary",
                    ],
                ),
                (
                    "check priority_advice",
                    [
                        sys.executable,
                        "search_docs.py",
                        "--doc-type",
                        "priority_advice",
                        "priority advice",
                    ],
                ),
                (
                    "check review_report",
                    [
                        sys.executable,
                        "search_docs.py",
                        "--doc-type",
                        "review_report",
                        "project records ",
                    ],
                ),
                (
                    "check secretary_report",
                    [
                        sys.executable,
                        "search_docs.py",
                        "--doc-type",
                        "secretary_report",
                        "personal secretary report",
                    ],
                ),
            ],
        }

    return {
        "title": f"{milestone_upper} milestone closeout report",
        "doc_type": "milestone_report",
        "tags": f"[{milestone_upper}, milestone closeout, auto generated]",
        "focus": f"{milestone_upper} stage",
        "summary_lines": build_generic_summary_lines(milestone_upper),
        "extra_checks": [],
    }

def build_m1_summary_lines() -> list[str]:
    """
    M1 stagesummarycontent. 
    """
    return [
        "## 1. M1 stage ",
        "",
        "M1 stage goal iscompleted'Personal Project Secretary + Knowledge Base'local RAG MVP, ",
        "and ascanlong-termmaintenance knowledge basetool. ",
        "",
        "M1 stagecore :",
        "",
        "1. Markdown is . ",
        "2. Qdrant isrebuildable . ",
        "3. Ollama is model . ",
        "4. Python scriptisautomatic tool . ",
        "5. config.py is configurationin . ",
        "",
        "## 2. M1 completed capabilities",
        "",
        "1. Ollama  model . ",
        "2. qwen3:8b chat model . ",
        "3. bge-m3 embedding model . ",
        "4. Docker Qdrant vector database . ",
        "5. Markdown document . ",
        "6. Frontmatter metadata parsing. ",
        "7. project / doc_type / category / tag filtered retrieval. ",
        "8. ask.py RAG question answering. ",
        "9. search_docs.py chunk search. ",
        "10. add_note.py quicklyaddrecord. ",
        "11. project_report.py project report. ",
        "12. time_report.py daily report / weekly report. ",
        "13. status.py system status overview. ",
        "14. backup_kb.py knowledge basebackup. ",
        "15. validate_kb.py and repair_frontmatter.py validation check andrepair. ",
        "16. rebuild_index.py safe rebuild . ",
        "17. health_check_full.py full-chain health check. ",
        "",
        "## 3. M1 closeout decision",
        "",
        "if health_check_full.py, status.py, list_docs.py  passed, and documentcanretrieval, ",
        "  M1 canas  RAG knowledge base MVP  . ",
        "",
    ]

def build_m2_summary_lines() -> list[str]:
    """
    M2 stagesummarycontent. 

    M2  notisservice-oriented API layer, instead'personal secretary capabilities '. 
    """
    return [
        "## 1. M2 stage ",
        "",
        "M2 stage goal is M1 'can , can , canquestion answering'knowledge basebasiccapability, ",
        " as'can , can , can , can recommendations'personal secretary capability. ",
        "",
        "M2 stagenotprioritize  FastAPI service-oriented API layer,  notprioritize  Web UI, ",
        "insteadprioritize script capability. ",
        "",
        "## 2. M2 completed capabilities",
        "",
        "### M2.1 next_action.py",
        "",
        "from progress_log, next_steps, project_report, weekly_report in next action items, ",
        "  next_action_report, and save to 05_Summaries/next_actions. ",
        "",
        "### M2.2 project_brief.py",
        "",
        " project brief,  current status, recent , current issues, next actions, risk remindersandrecommended records to add, ",
        "and save to 05_Summaries/project_briefs. ",
        "",
        "### M2.3 multi_project_status.py",
        "",
        " project status,  default all ,   --project specified , --exclude-project  , ",
        "and save to 05_Summaries/multi_project_status. ",
        "",
        "### M2.4 priority_advisor.py",
        "",
        " project status, issue, plan,  andmulti-project recordsprovidepriority advice, ",
        "and save to 05_Summaries/priority_advice. ",
        "",
        "### M2.5 review_assistant.py",
        "",
        "forproject records , check project recordswhether complete, identifymissing information, risks and hidden issues, ",
        "recommended records to add and immediate issue, and save to 05_Summaries/review_reports. ",
        "",
        "### M2.6 secretary_report.py",
        "",
        "  multi_project_status, priority_advice, review_report, project_brief, next_action_report, ",
        "weekly_report, daily_report, project_report, progress_log, next_steps, issues etc.records, ",
        " personal secretary report, and save to 05_Summaries/secretary_reports. ",
        "",
        "## 3. M2  ",
        "",
        "```powershell",
        "python next_action.py --project Personal_Project_Assistant",
        "python project_brief.py --project Personal_Project_Assistant",
        "python multi_project_status.py",
        "python priority_advisor.py",
        "python review_assistant.py --project Personal_Project_Assistant",
        "python secretary_report.py",
        "python update_index.py",
        "```",
        "",
        "## 4. M2 closeout decision",
        "",
        "M2 can conditions:",
        "",
        "1. next_action_report can and . ",
        "2. project_brief can and . ",
        "3. multi_project_status can and . ",
        "4. priority_advice can and . ",
        "5. review_report can and . ",
        "6. secretary_report can and . ",
        "7. health_check_full.py  checkpassed. ",
        "8. status.py can displaysystem status. ",
        "9. list_docs.py can listdocument. ",
        "",
        "if conditions ,   M2 canas'Personal Secretary Capability Enhancement Stage' . ",
        "",
        "## 5. M2 maintenance recommendations",
        "",
        "1. each timeadd project records execute `python update_index.py`. ",
        "2. each stageend execute `python project_brief.py --project  `. ",
        "3. weeklyexecute `python multi_project_status.py` and `python priority_advisor.py`. ",
        "4. weeklyexecute  `python secretary_report.py`  personal secretary report. ",
        "5. regularly execute `python review_assistant.py --project  ` check project recordsquality. ",
        "6.  corescript execute `python backup_kb.py`. ",
        "",
        "## 6. M3  ",
        "",
        "M2 completed , next stagecan has :",
        "",
        "1.  capability, for exampleautomaticplan, tasks ,  items . ",
        "2. startservice-oriented API layer, for example FastAPI,   Web UI,  andautomatic execute . ",
        "",
        " , recommendations M3 prioritize as:",
        "",
        "```text",
        "M3:tasks andautomatic capability",
        "```",
        "",
        " notis entercomplex Web UI. ",
        "",
    ]

def build_generic_summary_lines(milestone: str) -> list[str]:
    """
     specificconfigurationmilestone this general . 
    """
    return [
        f"## 1. {milestone} stage ",
        "",
        f"{milestone} stage configurationspecificsummary . ",
        "",
        f"## 2. {milestone} stagecheckdescription",
        "",
        " report executegeneralcheck:",
        "",
        "1. health_check_full.py",
        "2. status.py",
        "3. list_docs.py",
        "",
        "if complete content, pleasein get_milestone_config() in specificconfiguration. ",
        "",
    ]

def save_closeout_report(
    milestone: str,
    milestone_config: dict,
    outputs: dict[str, str],
    results: dict[str, bool],
) -> Path:
    """
    savemilestone closeout report. 
    """
    MILESTONE_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    milestone_upper = milestone.upper()

    report_path = MILESTONE_REPORT_DIR / f"{timestamp}_{milestone_upper}_closeout_report.md"

    lines = []

    lines.append("---")
    lines.append(f"title: {milestone_config['title']} {timestamp}")
    lines.append(f"created: {now.isoformat(timespec='seconds')}")
    lines.append("category: summary")
    lines.append("project: Personal_Project_Assistant")
    lines.append(f"doc_type: {milestone_config['doc_type']}")
    lines.append(f"tags: {milestone_config['tags']}")
    lines.append(f"milestone: {milestone_upper}")
    lines.append("---")
    lines.append("")

    lines.append(f"# {milestone_config['title']}")
    lines.append("")
    lines.append(f"generated at:{now.isoformat(timespec='seconds')}")
    lines.append(f"knowledge base root:{KNOWLEDGE_ROOT}")
    lines.append(f"stage :{milestone_config['focus']}")
    lines.append("")

    lines.extend(milestone_config["summary_lines"])
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## automaticcheck results ")
    lines.append("")

    for name, ok in results.items():
        status = "passed" if ok else "failed"
        lines.append(f"- {name}:{status}")

    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## automaticcheck ")
    lines.append("")

    for name, output in outputs.items():
        lines.append(f"### {name}")
        lines.append("")
        lines.append("```text")
        lines.append(output)
        lines.append("```")
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path

def main():
    parser = argparse.ArgumentParser(
        description="Personal Project Secretary + Knowledge Base:generalmilestone closeoutcheck"
    )

    parser.add_argument(
        "--milestone",
        required=True,
        help="stagename, for example M1, M2, M3. ",
    )

    parser.add_argument(
        "--skip-health",
        action="store_true",
        help="skip health_check_full.py,  quickly closeout report. ",
    )

    parser.add_argument(
        "--skip-extra-checks",
        action="store_true",
        help="skipthismilestone retrievalcheck. ",
    )

    args = parser.parse_args()

    milestone = args.milestone.upper()
    milestone_config = get_milestone_config(milestone)

    print("Personal Project Secretary + Knowledge Base:generalmilestone closeoutcheck")
    print(f"stage:{milestone}")
    print(f"stage :{milestone_config['focus']}")
    print(f"working directory:{BASE_DIR}")
    print(f"Python:{sys.executable}")

    checks = []

    if not args.skip_health:
        checks.append(
            ("health_check_full.py", [sys.executable, "health_check_full.py"])
        )

    checks.extend(
        [
            ("status.py", [sys.executable, "status.py"]),
            ("list_docs.py", [sys.executable, "list_docs.py"]),
        ]
    )

    if not args.skip_extra_checks:
        checks.extend(milestone_config.get("extra_checks", []))

    outputs = {}
    results = {}

    for name, command in checks:
        ok, output = run_command(name, command)
        outputs[name] = output
        results[name] = ok

    report_path = save_closeout_report(
        milestone=milestone,
        milestone_config=milestone_config,
        outputs=outputs,
        results=results,
    )

    print("\n" + "=" * 80)
    print("milestone closeoutcheckcompleted")
    print("=" * 80)
    print("")
    print("closeout reportalready :")
    print(report_path)
    print("")

    if all(results.values()):
        print(f" :{milestone} stagecan . ")
    else:
        print(f" :{milestone} stage hascheck failed, please firstrepair. ")

    print("")
    print("recommended next command:")
    print("python update_index.py")
    print(
        f'python ask.py --doc-type milestone_report "{milestone} stagecompleted ？"'
    )


if __name__ == "__main__":
    main()

