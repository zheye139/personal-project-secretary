import os
import subprocess
import sys
from pathlib import Path

import command_registry
import project_discovery


# ============================================================
# Windows / PowerShell 中文输出处理
# ============================================================

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


# ============================================================
# 基础配置
# ============================================================

BASE_DIR = Path(__file__).parent.resolve()


# ============================================================
# 避免访问本机服务时走系统代理
# ============================================================

for key in [
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
]:
    os.environ.pop(key, None)

os.environ["NO_PROXY"] = "localhost,127.0.0.1,::1"
os.environ["no_proxy"] = "localhost,127.0.0.1,::1"


def pause() -> None:
    """
    等待用户按回车。
    """
    input("\nPress Enter to continue...")


def clear_screen() -> None:
    """
    清屏。
    """
    os.system("cls" if os.name == "nt" else "clear")


def print_header(title: str = "Personal Project Secretary") -> None:
    """
    打印标题。
    """
    print("=" * 80)
    print(title)
    print("=" * 80)


def ask_text(prompt: str, default: str | None = None, required: bool = False) -> str:
    """
    输入字符串。
    """
    while True:
        if default is not None and default != "":
            raw = input(f"{prompt} [{default}]: ").strip()
            value = raw if raw else default
        else:
            value = input(f"{prompt}: ").strip()

        if required and not value:
            print("This field is required.")
            continue

        return value


def ask_multiline(prompt: str, required: bool = False) -> str:
    """
    输入多行文本。

    结束方式：
    输入一行 END 后回车。
    """
    print(prompt)
    print("Enter multiline text. Type END on a new line to finish.")
    print("")

    lines = []

    while True:
        line = input()

        if line.strip() == "END":
            break

        lines.append(line)

    text = "\n".join(lines).strip()

    if required and not text:
        print("Content is required.")
        return ask_multiline(prompt, required=required)

    return text


def ask_bool(prompt: str, default: bool = False) -> bool:
    """
    输入 yes/no。
    """
    default_text = "Y/n" if default else "y/N"

    while True:
        raw = input(f"{prompt} [{default_text}]: ").strip().lower()

        if not raw:
            return default

        if raw in ["y", "yes"]:
            return True

        if raw in ["n", "no"]:
            return False

        print("Please enter y or n.")


def choose_option(prompt: str, options: list[str], default: str | None = None) -> str:
    """
    从选项中选择。
    """
    if not options:
        return ""

    print(prompt)

    for index, option in enumerate(options, start=1):
        mark = ""
        if default is not None and option == default:
            mark = "  <default>"
        print(f"{index}. {option}{mark}")

    while True:
        raw = input("Select number or enter value directly: ").strip()

        if not raw and default is not None:
            return default

        if raw.isdigit():
            index = int(raw)

            if 1 <= index <= len(options):
                return options[index - 1]

        if raw:
            return raw

        print("Invalid selection.")


def confirm_action(message: str) -> bool:
    """
    二次确认。
    """
    print("")
    print("Confirmation required")
    print("-" * 80)
    print(message)
    print("-" * 80)

    raw = input("Type YES to continue: ").strip()

    return raw == "YES"


# ============================================================
# project_discovery.py 选择辅助
# ============================================================

def load_manifest_for_launcher() -> dict | None:
    """
    加载 index_manifest.json。

    如果 manifest 不存在或损坏，不中断 launcher，
    退回手动输入模式。
    """
    try:
        return project_discovery.load_manifest()
    except Exception as e:
        print("")
        print(f"[Warning] Failed to load index_manifest.json: {e}")
        print("Fallback to manual input.")
        return None


def get_project_options() -> list[str]:
    """
    获取项目列表。
    """
    manifest = load_manifest_for_launcher()

    if not manifest:
        return []

    projects = project_discovery.discover_projects(manifest)
    hidden_names = {"unknown", "qa_logs"}
    preferred_project = "Personal_Project_Assistant"

    options = []

    for item in projects:
        name = item.get("name", "").strip()

        if not name:
            continue

        if name.lower() in hidden_names:
            continue

        options.append(name)

    return sorted(
        options,
        key=lambda name: (
            name != preferred_project,
            name.lower(),
        ),
    )


def get_doc_type_options(project: str | None = None) -> list[str]:
    """
    获取 doc_type 列表。
    """
    manifest = load_manifest_for_launcher()

    if not manifest:
        return []

    doc_types = project_discovery.discover_doc_types(
        manifest=manifest,
        project=project or None,
    )

    return [
        item.get("name", "")
        for item in doc_types
        if item.get("name", "")
    ]


def get_category_options() -> list[str]:
    """
    获取 category 列表。
    """
    manifest = load_manifest_for_launcher()

    if not manifest:
        return []

    categories = project_discovery.discover_categories(manifest)

    return [
        item.get("name", "")
        for item in categories
        if item.get("name", "")
    ]


def get_tag_options(project: str | None = None) -> list[str]:
    """
    获取 tag 列表。
    """
    manifest = load_manifest_for_launcher()

    if not manifest:
        return []

    tags = project_discovery.discover_tags(
        manifest=manifest,
        project=project or None,
    )

    return [
        item.get("name", "")
        for item in tags
        if item.get("name", "")
    ]


def choose_from_list_or_manual(
    prompt: str,
    options: list[str],
    required: bool = False,
    allow_manual: bool = True,
    allow_empty: bool = True,
    default: str = "",
) -> str:
    """
    从列表选择，或手动输入。

    输入规则：
    - 0：跳过 / 不填写
    - 数字：选择列表项
    - m：手动输入
    - 直接输入完整值：作为手动值
    """
    options = [item for item in options if item]

    if not options:
        return ask_text(
            prompt,
            default=default,
            required=required,
        )

    print("")
    print(prompt)

    if allow_empty:
        print("0. None / skip")

    for index, option in enumerate(options, start=1):
        mark = ""
        if default and option == default:
            mark = "  <default>"
        print(f"{index}. {option}{mark}")

    if allow_manual:
        print("m. Manual input")

    while True:
        raw = input("Select: ").strip()

        if not raw and default:
            return default

        if raw == "0" and allow_empty:
            return ""

        if raw.isdigit():
            index = int(raw)

            if 1 <= index <= len(options):
                return options[index - 1]

        if raw.lower() == "m" and allow_manual:
            return ask_text(
                f"{prompt} manual value",
                required=required,
            )

        if raw and allow_manual:
            return raw

        if required:
            print("This field is required.")
            continue

        print("Invalid selection.")


def choose_project(
    required: bool = False,
    allow_empty: bool = True,
    allow_manual: bool = True,
    prompt: str = "Project",
) -> str:
    """
    选择项目。
    """
    options = get_project_options()
    preferred_project = "Personal_Project_Assistant"
    default = preferred_project if preferred_project in options else ""

    return choose_from_list_or_manual(
        prompt=prompt,
        options=options,
        required=required,
        allow_manual=allow_manual,
        allow_empty=allow_empty,
        default=default,
    )


def choose_doc_type(
    project: str | None = None,
    required: bool = False,
    allow_empty: bool = True,
    allow_manual: bool = True,
    prompt: str = "Doc type",
) -> str:
    """
    选择 doc_type。
    """
    return choose_from_list_or_manual(
        prompt=prompt,
        options=get_doc_type_options(project=project),
        required=required,
        allow_manual=allow_manual,
        allow_empty=allow_empty,
    )


def choose_category(
    required: bool = False,
    allow_empty: bool = True,
    allow_manual: bool = True,
    prompt: str = "Category",
) -> str:
    """
    选择 category。
    """
    return choose_from_list_or_manual(
        prompt=prompt,
        options=get_category_options(),
        required=required,
        allow_manual=allow_manual,
        allow_empty=allow_empty,
    )


def choose_tag(
    project: str | None = None,
    required: bool = False,
    allow_empty: bool = True,
    allow_manual: bool = True,
    prompt: str = "Tag",
) -> str:
    """
    选择 tag。
    """
    return choose_from_list_or_manual(
        prompt=prompt,
        options=get_tag_options(project=project),
        required=required,
        allow_manual=allow_manual,
        allow_empty=allow_empty,
    )


def build_command(command_id: str, extra_args: list[str] | None = None) -> list[str]:
    """
    根据 command_registry 中的 script 构建命令。

    注意：
    这里使用 sys.executable，保证使用当前 Python 环境。
    """
    registry = command_registry.get_command_registry()
    command = registry.get(command_id)

    if not command:
        raise ValueError(f"Command not found in registry: {command_id}")

    script = command["script"]
    argv = [sys.executable, script]

    if extra_args:
        argv.extend(extra_args)

    return argv


def run_registered_command(
    command_id: str,
    extra_args: list[str] | None = None,
    confirm_message: str | None = None,
) -> int:
    """
    执行 command_registry 中登记的命令。
    """
    registry = command_registry.get_command_registry()
    command = registry.get(command_id)

    if not command:
        print(f"Command not found: {command_id}")
        return 1

    dangerous = bool(command.get("dangerous", False))
    requires_confirmation = bool(command.get("requires_confirmation", False))

    if confirm_message:
        requires_confirmation = True

    if dangerous or requires_confirmation:
        message = confirm_message or (
            f"You are going to run command: {command_id}\n"
            f"Script: {command.get('script')}\n"
            "This operation requires confirmation."
        )

        if not confirm_action(message):
            print("Cancelled.")
            return 0

    argv = build_command(command_id, extra_args=extra_args)

    print("")
    print("=" * 80)
    print(f"Running: {command.get('title', command_id)}")
    print("=" * 80)
    print("Command:")
    print(" ".join(argv))
    print("")

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        result = subprocess.run(
            argv,
            cwd=BASE_DIR,
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        return 130
    except Exception as e:
        print(f"Failed to run command: {e}")
        return 1

    print("")
    print("=" * 80)
    print(f"Exit code: {result.returncode}")
    print("=" * 80)

    return result.returncode


def append_optional_arg(args: list[str], flag: str, value: str | None) -> None:
    """
    value 非空时追加参数。
    """
    if value:
        args.extend([flag, value])


def append_bool_arg(args: list[str], flag: str, enabled: bool) -> None:
    """
    bool 为 True 时追加 flag。
    """
    if enabled:
        args.append(flag)


def action_system_status() -> None:
    """
    系统状态菜单。
    """
    print_header("System status")

    options = [
        "status",
        "check_env",
        "health_check",
        "list_docs",
    ]

    choice = choose_option(
        "Select system command:",
        options=options,
        default="status",
    )

    run_registered_command(choice)
    pause()


def action_ask_question() -> None:
    """
    RAG 问答。
    """
    print_header("Ask a question")

    question = ask_text("Question", required=True)

    search_mode = choose_option(
        "Search mode:",
        options=["vector", "keyword", "hybrid"],
        default="hybrid",
    )

    project = choose_project(
        required=False,
        allow_empty=True,
        prompt="Project filter, optional",
    )

    doc_type = choose_doc_type(
        project=project,
        required=False,
        allow_empty=True,
        prompt="Doc type filter, optional",
    )

    category = choose_category(
        required=False,
        allow_empty=True,
        prompt="Category filter, optional",
    )

    tag = choose_tag(
        project=project,
        required=False,
        allow_empty=True,
        prompt="Tag filter, optional",
    )

    limit = ask_text("Limit", default="5")

    args = [question]
    args.extend(["--search-mode", search_mode])
    args.extend(["--limit", limit])

    append_optional_arg(args, "--project", project)
    append_optional_arg(args, "--doc-type", doc_type)
    append_optional_arg(args, "--category", category)
    append_optional_arg(args, "--tag", tag)

    if search_mode == "hybrid":
        vector_weight = ask_text("Vector weight", default="0.6")
        keyword_weight = ask_text("Keyword weight", default="0.4")
        args.extend(["--vector-weight", vector_weight])
        args.extend(["--keyword-weight", keyword_weight])

    run_registered_command("ask", extra_args=args)
    pause()


def action_search_documents() -> None:
    """
    搜索文档。
    """
    print_header("Search documents")

    query = ask_text("Search query", required=True)

    mode = choose_option(
        "Search mode:",
        options=["vector", "keyword", "hybrid"],
        default="hybrid",
    )

    project = choose_project(
        required=False,
        allow_empty=True,
        prompt="Project filter, optional",
    )

    doc_type = choose_doc_type(
        project=project,
        required=False,
        allow_empty=True,
        prompt="Doc type filter, optional",
    )

    category = choose_category(
        required=False,
        allow_empty=True,
        prompt="Category filter, optional",
    )

    tag = choose_tag(
        project=project,
        required=False,
        allow_empty=True,
        prompt="Tag filter, optional",
    )
    
    limit = ask_text("Limit", default="5")
    show_text = ask_bool("Show text preview?", default=True)

    args = [query]
    args.extend(["--mode", mode])
    args.extend(["--limit", limit])

    append_optional_arg(args, "--project", project)
    append_optional_arg(args, "--doc-type", doc_type)
    append_optional_arg(args, "--category", category)
    append_optional_arg(args, "--tag", tag)
    append_bool_arg(args, "--show-text", show_text)

    if mode == "hybrid":
        vector_weight = ask_text("Vector weight", default="0.6")
        keyword_weight = ask_text("Keyword weight", default="0.4")
        args.extend(["--vector-weight", vector_weight])
        args.extend(["--keyword-weight", keyword_weight])

    run_registered_command("search", extra_args=args)
    pause()


def action_add_note() -> None:
    """
    添加 Markdown 记录。
    """
    print_header("Add note")

    category = choose_category(
        required=True,
        allow_empty=False,
        allow_manual=True,
        prompt="Category",
    )

    if not category:
        category = "project"

    project = choose_project(
        required=False,
        allow_empty=True,
        allow_manual=True,
        prompt="Project, optional",
    )

    doc_type = choose_doc_type(
        project=project,
        required=True,
        allow_empty=False,
        allow_manual=True,
        prompt="Doc type",
    )

    if not doc_type:
        doc_type = "progress_log"

    title = ask_text("Title", required=True)
    tags = ask_text("Tags, comma separated", default="")
    content = ask_multiline("Content", required=True)

    args = [
        "--category",
        category,
        "--doc-type",
        doc_type,
        "--title",
        title,
        "--content",
        content,
    ]

    append_optional_arg(args, "--project", project)
    append_optional_arg(args, "--tags", tags)

    run_registered_command("add_note", extra_args=args)

    if ask_bool("Update index for this project now?", default=True):
        index_args = []

        if project:
            index_args.extend(["--project", project])

        run_registered_command("update_index", extra_args=index_args)

    pause()


def action_update_index() -> None:
    """
    更新索引。
    """
    print_header("Update index")

    options = [
        "dry-run all",
        "incremental all",
        "project dry-run",
        "project update",
        "project force update",
        "single file update",
        "force all",
    ]

    choice = choose_option(
        "Select update mode:",
        options=options,
        default="incremental all",
    )

    args = []

    if choice == "dry-run all":
        args.append("--dry-run")

    elif choice == "incremental all":
        pass

    elif choice == "project dry-run":
        project = choose_project(
            required=True,
            allow_empty=False,
            prompt="Project",
        )
        args.extend(["--project", project, "--dry-run"])

    elif choice == "project update":
        project = choose_project(
            required=True,
            allow_empty=False,
            prompt="Project",
        )
        args.extend(["--project", project])

    elif choice == "project force update":
        project = choose_project(
            required=True,
            allow_empty=False,
            prompt="Project",
        )
        args.extend(["--project", project, "--force-project"])

        msg = (
            "This will force rebuild all indexed Markdown files in the selected project.\n"
            f"Project: {project}"
        )
        run_registered_command(
            "update_index",
            extra_args=args,
            confirm_message=msg,
        )
        pause()
        return

    elif choice == "single file update":
        file_path = ask_text(
            "Markdown file path, relative or absolute",
            required=True,
        )
        force_file = ask_bool("Force rebuild this file?", default=False)

        args.extend(["--file", file_path])
        append_bool_arg(args, "--force-file", force_file)

    elif choice == "force all":
        args.append("--force-all")

        msg = (
            "This will force rebuild all Markdown files in the knowledge base.\n"
            "It may take time and will rewrite Qdrant points."
        )
        run_registered_command(
            "update_index",
            extra_args=args,
            confirm_message=msg,
        )
        pause()
        return

    run_registered_command("update_index", extra_args=args)
    pause()


def action_project_report() -> None:
    """
    项目报告。
    """
    print_header("Generate project report")

    project = choose_project(
        required=True,
        allow_empty=False,
        prompt="Project",
    )
    args = ["--project", project]

    run_registered_command("project_report", extra_args=args)

    if ask_bool("Update index for this project now?", default=True):
        run_registered_command(
            "update_index",
            extra_args=["--project", project],
        )

    pause()


def action_next_actions() -> None:
    """
    下一步行动项。
    """
    print_header("Generate next actions")

    project = choose_project(
        required=True,
        allow_empty=False,
        prompt="Project",
    )
    args = ["--project", project]

    run_registered_command("next_action", extra_args=args)

    if ask_bool("Update index for this project now?", default=True):
        run_registered_command(
            "update_index",
            extra_args=["--project", project],
        )

    pause()


def action_secretary_report() -> None:
    """
    个人秘书综合汇报。
    """
    print_header("Generate secretary report")

    project = choose_project(
        required=False,
        allow_empty=True,
        prompt="Project, optional",
    )

    args = []
    append_optional_arg(args, "--project", project)

    run_registered_command("secretary_report", extra_args=args)

    if ask_bool("Update index now?", default=True):
        index_args = []
        append_optional_arg(index_args, "--project", project)
        run_registered_command("update_index", extra_args=index_args)

    pause()


def action_retrieval_eval() -> None:
    """
    检索评估。
    """
    print_header("Run retrieval evaluation")

    mode = choose_option(
        "Evaluation mode:",
        options=["all", "vector", "keyword", "hybrid"],
        default="all",
    )

    top_k = ask_text("TopK, optional", default="1,3,5")
    limit = ask_text("Limit", default="5")
    no_save = ask_bool("No save report?", default=False)

    args = [
        "--mode",
        mode,
        "--top-k",
        top_k,
        "--limit",
        limit,
    ]

    append_bool_arg(args, "--no-save", no_save)

    run_registered_command("retrieval_eval", extra_args=args)

    if not no_save and ask_bool("Update index for eval report now?", default=True):
        run_registered_command(
            "update_index",
            extra_args=["--project", "Personal_Project_Assistant"],
        )

    pause()


def action_backup() -> None:
    """
    备份知识库。
    """
    print_header("Backup knowledge base")

    msg = (
        "This will create a local backup of the knowledge base files.\n"
        "It does not upload data to the internet."
    )

    run_registered_command(
        "backup",
        confirm_message=msg,
    )

    pause()


def action_rebuild_index() -> None:
    """
    全量重建索引。
    """
    print_header("Rebuild index")

    preview_only = ask_bool(
        "Preview only? If yes, do not execute rebuild.",
        default=True,
    )

    args = []

    if not preview_only:
        args.append("--execute")

        skip_check = ask_bool("Skip check?", default=False)
        skip_snapshot = ask_bool("Skip snapshot?", default=False)

        append_bool_arg(args, "--skip-check", skip_check)
        append_bool_arg(args, "--skip-snapshot", skip_snapshot)

        msg = (
            "This will rebuild the Qdrant collection and reset index_manifest.json.\n"
            "Please make sure Markdown files are the source of truth."
        )

        run_registered_command(
            "rebuild_index",
            extra_args=args,
            confirm_message=msg,
        )
    else:
        run_registered_command("rebuild_index", extra_args=args)

    pause()


def action_milestone_closeout() -> None:
    """
    里程碑封版。
    """
    print_header("Milestone closeout")

    milestone = choose_option(
        "Milestone:",
        options=["M1", "M2", "M3", "M4"],
        default="M3",
    )

    skip_health = ask_bool("Skip health check?", default=False)

    args = ["--milestone", milestone]
    append_bool_arg(args, "--skip-health", skip_health)

    run_registered_command("milestone_closeout", extra_args=args)

    if ask_bool("Update index for closeout report now?", default=True):
        run_registered_command(
            "update_index",
            extra_args=["--project", "Personal_Project_Assistant"],
        )

    pause()


def run_project_discovery_menu() -> None:
    """
    项目与元数据发现菜单。
    """
    while True:
        clear_screen()
        print_header("Project discovery")

        print("1. Summary")
        print("2. Projects")
        print("3. Doc types")
        print("4. Categories")
        print("5. Tags")
        print("6. Files")
        print("0. Back")
        print("")

        choice = input("Select: ").strip()

        if choice == "1":
            run_python_script("project_discovery.py", ["--summary"])
            pause()

        elif choice == "2":
            run_python_script("project_discovery.py", ["--projects"])
            pause()

        elif choice == "3":
            project = choose_project(
                required=False,
                allow_empty=True,
                prompt="Project filter, optional",
            )
            args = ["--doc-types"]
            append_optional_arg(args, "--project", project)
            run_python_script("project_discovery.py", args)
            pause()

        elif choice == "4":
            run_python_script("project_discovery.py", ["--categories"])
            pause()

        elif choice == "5":
            project = choose_project(
                required=False,
                allow_empty=True,
                prompt="Project filter, optional",
            )
            args = ["--tags"]
            append_optional_arg(args, "--project", project)
            run_python_script("project_discovery.py", args)
            pause()

        elif choice == "6":
            project = choose_project(
                required=False,
                allow_empty=True,
                prompt="Project filter, optional",
            )
            args = ["--files", "--limit", "30"]
            append_optional_arg(args, "--project", project)
            run_python_script("project_discovery.py", args)
            pause()

        elif choice == "0":
            return

        else:
            print("Invalid option.")
            pause()


def run_python_script(script: str, args: list[str] | None = None) -> int:
    """
    直接运行一个 Python 脚本。

    用于没有纳入 command_registry 的辅助工具，
    例如 project_discovery.py。
    """
    argv = [sys.executable, script]

    if args:
        argv.extend(args)

    print("")
    print("=" * 80)
    print("Running:")
    print(" ".join(argv))
    print("=" * 80)
    print("")

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    result = subprocess.run(
        argv,
        cwd=BASE_DIR,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    print("")
    print("=" * 80)
    print(f"Exit code: {result.returncode}")
    print("=" * 80)

    return result.returncode


def action_start_local_api() -> None:
    """
    Start the local read-only FastAPI server in the foreground.
    """
    print_header("Start local API server")

    script_path = BASE_DIR / "run_api.ps1"

    if not script_path.exists():
        print(f"Startup script not found: {script_path.name}")
        return

    print("API server: http://127.0.0.1:8000")
    print("Docs:       http://127.0.0.1:8000/docs")
    print("The server runs in the foreground. Press Ctrl+C to stop it.")
    print("")

    argv = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script_path),
    ]

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        result = subprocess.run(
            argv,
            cwd=BASE_DIR,
            env=env,
        )
    except KeyboardInterrupt:
        print("\nLocal API server stopped.")
        return
    except Exception as e:
        print(f"Failed to start local API server: {e}")
        return

    print("")
    print(f"Local API server exited with code: {result.returncode}")


def action_advanced_maintenance() -> None:
    """
    高级维护菜单。
    """
    while True:
        clear_screen()
        print_header("Advanced maintenance")

        print("1. Check environment")
        print("2. Full health check")
        print("3. List indexed documents")
        print("4. Rebuild index")
        print("5. Milestone closeout")
        print("6. Project discovery summary")
        print("7. Command registry list")
        print("8. Start local API server")
        print("0. Back")
        print("")

        choice = input("Select: ").strip()

        if choice == "1":
            run_registered_command("check_env")
            pause()

        elif choice == "2":
            run_registered_command("health_check")
            pause()

        elif choice == "3":
            run_registered_command("list_docs")
            pause()

        elif choice == "4":
            action_rebuild_index()

        elif choice == "5":
            action_milestone_closeout()

        elif choice == "6":
            run_project_discovery_menu()

        elif choice == "7":
            print("")
            print("Registered commands:")
            print("")
            command_registry.print_command_list()
            pause()

        elif choice == "8":
            action_start_local_api()

        elif choice == "0":
            return

        else:
            print("Invalid option.")
            pause()


def normalize_menu_input(value: str) -> str:
    """
    规范化菜单输入。

    M4.2 修正：
    只做大小写和空格兼容，不做缩写识别。
    """
    return " ".join(value.strip().lower().split())


def resolve_main_menu_choice(raw_choice: str) -> str:
    """
    将用户输入转换为主菜单编号。

    只支持：
    1. 数字输入，例如 1
    2. 完整菜单名称，例如 System status

    不支持缩写：
    - status
    - ask
    - search
    - q
    """
    if raw_choice.strip() == "Exit":
        return "0"

    value = normalize_menu_input(raw_choice)

    aliases = {
        "1": "1",
        "system status": "1",

        "2": "2",
        "ask a question": "2",

        "3": "3",
        "search documents": "3",

        "4": "4",
        "add note": "4",

        "5": "5",
        "update index": "5",

        "6": "6",
        "generate project report": "6",

        "7": "7",
        "generate next actions": "7",

        "8": "8",
        "generate secretary report": "8",

        "9": "9",
        "run retrieval evaluation": "9",

        "10": "10",
        "backup knowledge base": "10",

        "11": "11",
        "advanced maintenance": "11",

        "0": "0",
    }

    return aliases.get(value, "")


def print_main_menu() -> None:
    """
    打印主菜单。
    """
    print_header("Personal Project Secretary")

    print("1. System status")
    print("2. Ask a question")
    print("3. Search documents")
    print("4. Add note")
    print("5. Update index")
    print("6. Generate project report")
    print("7. Generate next actions")
    print("8. Generate secretary report")
    print("9. Run retrieval evaluation")
    print("10. Backup knowledge base")
    print("11. Advanced maintenance")
    print("0. Exit")
    print("")


def main() -> None:
    """
    launcher.py 主入口。
    """
    # 启动时确认 command_registry 可用。
    registry = command_registry.get_command_registry()

    if not registry:
        print("No commands registered.")
        return

    while True:
        clear_screen()
        print_main_menu()

        raw_choice = input("Select: ").strip()
        choice = resolve_main_menu_choice(raw_choice)

        if choice == "1":
            action_system_status()

        elif choice == "2":
            action_ask_question()

        elif choice == "3":
            action_search_documents()

        elif choice == "4":
            action_add_note()

        elif choice == "5":
            action_update_index()

        elif choice == "6":
            action_project_report()

        elif choice == "7":
            action_next_actions()

        elif choice == "8":
            action_secretary_report()

        elif choice == "9":
            action_retrieval_eval()

        elif choice == "10":
            action_backup()

        elif choice == "11":
            action_advanced_maintenance()

        elif choice == "0":
            print("Bye.")
            return

        else:
            print(f"Invalid option: {raw_choice}")
            print("")
            print("Please enter a menu number, for example:")
            print("1")
            print("")
            print("Or enter the full menu title, for example:")
            print("System status")
            print("Ask a question")
            print("Search documents")
            pause()


if __name__ == "__main__":
    main()
