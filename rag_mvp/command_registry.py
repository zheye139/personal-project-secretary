import argparse
import json
import sys
from copy import deepcopy


# ============================================================
# Windows / PowerShell 中文输出处理
# ============================================================

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


# ============================================================
# 参数 schema 构建工具
# ============================================================

def arg_spec(
    name: str,
    flag: str | None = None,
    arg_type: str = "str",
    required: bool = False,
    default=None,
    choices: list[str] | None = None,
    description: str = "",
    positional: bool = False,
    multiple: bool = False,
    example: str = "",
    dangerous: bool = False,
    requires_confirmation: bool = False,
) -> dict:
    """
    构建一个命令参数说明。

    注意：
    这里不执行 argparse 解析，只描述参数。
    后续 launcher.py / Web UI 会读取这些字段生成输入项。
    """
    return {
        "name": name,
        "flag": flag,
        "type": arg_type,
        "required": required,
        "default": default,
        "choices": choices or [],
        "description": description,
        "positional": positional,
        "multiple": multiple,
        "example": example,
        "dangerous": dangerous,
        "requires_confirmation": requires_confirmation,
    }


def command_spec(
    command_id: str,
    title: str,
    description: str,
    category: str,
    script: str,
    arguments: list[dict] | None = None,
    dangerous: bool = False,
    requires_confirmation: bool = False,
    tags: list[str] | None = None,
) -> dict:
    """
    构建一个命令说明。

    command_registry.py 只做命令登记，不执行业务逻辑。
    """
    return {
        "id": command_id,
        "title": title,
        "description": description,
        "category": category,
        "script": script,
        "arguments": arguments or [],
        "dangerous": dangerous,
        "requires_confirmation": requires_confirmation,
        "tags": tags or [],
    }


# ============================================================
# 通用参数模板
# ============================================================

ARG_PROJECT = arg_spec(
    name="project",
    flag="--project",
    arg_type="str",
    required=False,
    description="限定项目名，例如 Demo_Project。",
    example="Demo_Project",
)

ARG_DOC_TYPE = arg_spec(
    name="doc_type",
    flag="--doc-type",
    arg_type="str",
    required=False,
    description="限定文档类型，例如 progress_log、milestone_report、qa_log。",
    example="progress_log",
)

ARG_CATEGORY = arg_spec(
    name="category",
    flag="--category",
    arg_type="str",
    required=False,
    description="限定资料大类，例如 project、knowledge、summary、problem。",
    example="project",
)

ARG_TAG = arg_spec(
    name="tag",
    flag="--tag",
    arg_type="str",
    required=False,
    description="限定标签。",
    example="RAG",
)

ARG_LIMIT = arg_spec(
    name="limit",
    flag="--limit",
    arg_type="int",
    required=False,
    default=5,
    description="返回结果数量。",
    example="5",
)

ARG_SEARCH_MODE = arg_spec(
    name="search_mode",
    flag="--search-mode",
    arg_type="choice",
    required=False,
    default="vector",
    choices=["vector", "keyword", "hybrid"],
    description="ask.py 使用的检索模式。",
    example="hybrid",
)

ARG_SEARCH_DOCS_MODE = arg_spec(
    name="mode",
    flag="--mode",
    arg_type="choice",
    required=False,
    default="vector",
    choices=["vector", "keyword", "hybrid"],
    description="search_docs.py 使用的检索模式。",
    example="hybrid",
)

ARG_MAX_SCAN_POINTS = arg_spec(
    name="max_scan_points",
    flag="--max-scan-points",
    arg_type="int",
    required=False,
    default=5000,
    description="keyword / hybrid 模式最多扫描多少个 Qdrant points。",
    example="5000",
)

ARG_VECTOR_WEIGHT = arg_spec(
    name="vector_weight",
    flag="--vector-weight",
    arg_type="float",
    required=False,
    default=0.6,
    description="hybrid 模式下向量检索权重。",
    example="0.6",
)

ARG_KEYWORD_WEIGHT = arg_spec(
    name="keyword_weight",
    flag="--keyword-weight",
    arg_type="float",
    required=False,
    default=0.4,
    description="hybrid 模式下关键词检索权重。",
    example="0.4",
)

ARG_DRY_RUN = arg_spec(
    name="dry_run",
    flag="--dry-run",
    arg_type="bool",
    required=False,
    default=False,
    description="只预览，不执行实际修改。",
)

ARG_SKIP_CHECK = arg_spec(
    name="skip_check",
    flag="--skip-check",
    arg_type="bool",
    required=False,
    default=False,
    description="跳过环境检查。",
)

ARG_SHOW_TEXT = arg_spec(
    name="show_text",
    flag="--show-text",
    arg_type="bool",
    required=False,
    default=False,
    description="显示检索正文预览。",
)


# ============================================================
# 命令注册表
# ============================================================

def build_command_registry() -> dict[str, dict]:
    """
    构建命令注册表。

    注意：
    1. 这里只登记命令，不执行命令。
    2. script 使用相对脚本名，不包含本机绝对路径。
    3. dangerous / requires_confirmation 给 launcher.py 和 Web UI 使用。
    """
    commands = [
        # ----------------------------------------------------
        # system
        # ----------------------------------------------------
        command_spec(
            command_id="check_env",
            title="Check environment",
            description="检查本地 Python、Ollama、Qdrant、embedding model 和 collection 状态。",
            category="system",
            script="check_env.py",
            tags=["system", "environment", "health"],
        ),
        command_spec(
            command_id="health_check",
            title="Run full health check",
            description="执行完整健康检查，验证核心脚本和 RAG 问答链路。",
            category="system",
            script="health_check_full.py",
            tags=["system", "health"],
        ),
        command_spec(
            command_id="status",
            title="Show knowledge base status",
            description="查看当前知识库和项目状态摘要。",
            category="system",
            script="status.py",
            tags=["system", "status"],
        ),
        command_spec(
            command_id="list_docs",
            title="List indexed documents",
            description="列出当前 Qdrant collection 中已入库的文档信息。",
            category="system",
            script="list_docs.py",
            tags=["system", "qdrant", "documents"],
        ),

        # ----------------------------------------------------
        # search / ask
        # ----------------------------------------------------
        command_spec(
            command_id="search",
            title="Search documents",
            description="搜索知识库片段，支持 vector / keyword / hybrid 三种模式。",
            category="search",
            script="search_docs.py",
            arguments=[
                arg_spec(
                    name="query",
                    positional=True,
                    multiple=True,
                    required=True,
                    description="搜索内容。",
                    example="M3 阶段增量索引做了什么？",
                ),
                deepcopy(ARG_SEARCH_DOCS_MODE),
                deepcopy(ARG_PROJECT),
                deepcopy(ARG_DOC_TYPE),
                deepcopy(ARG_CATEGORY),
                deepcopy(ARG_TAG),
                deepcopy(ARG_LIMIT),
                deepcopy(ARG_MAX_SCAN_POINTS),
                deepcopy(ARG_VECTOR_WEIGHT),
                deepcopy(ARG_KEYWORD_WEIGHT),
                deepcopy(ARG_SHOW_TEXT),
            ],
            tags=["search", "vector", "keyword", "hybrid"],
        ),
        command_spec(
            command_id="ask",
            title="Ask a question",
            description="基于知识库进行 RAG 问答，支持 vector / keyword / hybrid 检索模式。",
            category="ask",
            script="ask.py",
            arguments=[
                arg_spec(
                    name="question",
                    positional=True,
                    multiple=True,
                    required=True,
                    description="要提问的问题。",
                    example="当前项目下一步应该做什么？",
                ),
                deepcopy(ARG_SEARCH_MODE),
                deepcopy(ARG_PROJECT),
                deepcopy(ARG_DOC_TYPE),
                deepcopy(ARG_CATEGORY),
                deepcopy(ARG_TAG),
                deepcopy(ARG_LIMIT),
                deepcopy(ARG_MAX_SCAN_POINTS),
                deepcopy(ARG_VECTOR_WEIGHT),
                deepcopy(ARG_KEYWORD_WEIGHT),
            ],
            tags=["ask", "rag", "qwen3", "hybrid"],
        ),

        # ----------------------------------------------------
        # note
        # ----------------------------------------------------
        command_spec(
            command_id="add_note",
            title="Add note",
            description="新增一条 Markdown 知识库记录。",
            category="note",
            script="add_note.py",
            arguments=[
                arg_spec(
                    name="category",
                    flag="--category",
                    arg_type="str",
                    required=True,
                    description="资料大类，例如 project、knowledge、problem、summary。",
                    example="project",
                ),
                arg_spec(
                    name="project",
                    flag="--project",
                    arg_type="str",
                    required=False,
                    description="项目名。",
                    example="Demo_Project",
                ),
                arg_spec(
                    name="doc_type",
                    flag="--doc-type",
                    arg_type="str",
                    required=True,
                    description="文档类型，例如 progress_log、decision、issue。",
                    example="progress_log",
                ),
                arg_spec(
                    name="title",
                    flag="--title",
                    arg_type="str",
                    required=True,
                    description="记录标题。",
                    example="M4.1 command registry completed",
                ),
                arg_spec(
                    name="tags",
                    flag="--tags",
                    arg_type="str",
                    required=False,
                    description="逗号分隔标签。",
                    example="RAG,M4.1,launcher",
                ),
                arg_spec(
                    name="content",
                    flag="--content",
                    arg_type="text",
                    required=True,
                    description="正文内容。",
                    example="记录本次项目进展。",
                ),
            ],
            tags=["note", "markdown", "frontmatter"],
        ),

        # ----------------------------------------------------
        # index
        # ----------------------------------------------------
        command_spec(
            command_id="update_index",
            title="Update index",
            description="增量更新知识库索引。默认处理新增、修改、删除和未变化文件。",
            category="index",
            script="update_index.py",
            arguments=[
                deepcopy(ARG_DRY_RUN),
                deepcopy(ARG_PROJECT),
                arg_spec(
                    name="force_project",
                    flag="--force-project",
                    arg_type="bool",
                    required=False,
                    default=False,
                    description="强制重建指定项目内全部现存 Markdown 文件。",
                    requires_confirmation=True,
                ),
                arg_spec(
                    name="file",
                    flag="--file",
                    arg_type="str",
                    required=False,
                    description="只更新指定 Markdown 文件。",
                    example="01_Projects/Demo_Project/progress_log.md",
                ),
                arg_spec(
                    name="force_file",
                    flag="--force-file",
                    arg_type="bool",
                    required=False,
                    default=False,
                    description="强制重建指定 Markdown 文件。",
                    requires_confirmation=True,
                ),
                arg_spec(
                    name="force_all",
                    flag="--force-all",
                    arg_type="bool",
                    required=False,
                    default=False,
                    description="强制重建全部 Markdown 文件。",
                    dangerous=True,
                    requires_confirmation=True,
                ),
                deepcopy(ARG_SKIP_CHECK),
                arg_spec(
                    name="skip_list_docs",
                    flag="--skip-list-docs",
                    arg_type="bool",
                    required=False,
                    default=False,
                    description="跳过 list_docs 验证。",
                ),
            ],
            tags=["index", "incremental", "manifest"],
        ),
        command_spec(
            command_id="rebuild_index",
            title="Rebuild index",
            description="全量重建 Qdrant collection 和 index_manifest.json。默认预览，--execute 才会执行。",
            category="index",
            script="rebuild_index.py",
            arguments=[
                arg_spec(
                    name="execute",
                    flag="--execute",
                    arg_type="bool",
                    required=False,
                    default=False,
                    description="真正执行全量重建。",
                    dangerous=True,
                    requires_confirmation=True,
                ),
                arg_spec(
                    name="skip_snapshot",
                    flag="--skip-snapshot",
                    arg_type="bool",
                    required=False,
                    default=False,
                    description="跳过重建前快照。",
                ),
                deepcopy(ARG_SKIP_CHECK),
            ],
            dangerous=True,
            requires_confirmation=True,
            tags=["index", "rebuild", "qdrant", "manifest"],
        ),

        # ----------------------------------------------------
        # backup
        # ----------------------------------------------------
        command_spec(
            command_id="backup",
            title="Backup knowledge base",
            description="备份知识库目录和关键系统文件。",
            category="backup",
            script="backup_kb.py",
            dangerous=False,
            requires_confirmation=True,
            tags=["backup", "maintenance"],
        ),

        # ----------------------------------------------------
        # report
        # ----------------------------------------------------
        command_spec(
            command_id="project_report",
            title="Generate project report",
            description="生成指定项目的项目报告。",
            category="report",
            script="project_report.py",
            arguments=[
                deepcopy(ARG_PROJECT),
            ],
            tags=["report", "project"],
        ),
        command_spec(
            command_id="time_report",
            title="Generate time report",
            description="按时间维度生成知识库进展报告。",
            category="report",
            script="time_report.py",
            tags=["report", "time"],
        ),

        # ----------------------------------------------------
        # secretary
        # ----------------------------------------------------
        command_spec(
            command_id="next_action",
            title="Generate next actions",
            description="根据项目资料生成下一步行动项。",
            category="secretary",
            script="next_action.py",
            arguments=[
                deepcopy(ARG_PROJECT),
            ],
            tags=["secretary", "action"],
        ),
        command_spec(
            command_id="project_brief",
            title="Generate project brief",
            description="生成项目简报。",
            category="secretary",
            script="project_brief.py",
            arguments=[
                deepcopy(ARG_PROJECT),
            ],
            tags=["secretary", "brief"],
        ),
        command_spec(
            command_id="multi_project_status",
            title="Generate multi-project status",
            description="生成多个项目的状态汇总。",
            category="secretary",
            script="multi_project_status.py",
            arguments=[
                deepcopy(ARG_PROJECT),
                arg_spec(
                    name="exclude_project",
                    flag="--exclude-project",
                    arg_type="str",
                    required=False,
                    description="排除指定项目。",
                    example="Archived_Project",
                ),
            ],
            tags=["secretary", "multi-project"],
        ),
        command_spec(
            command_id="priority_advisor",
            title="Generate priority advice",
            description="根据项目资料生成优先级建议。",
            category="secretary",
            script="priority_advisor.py",
            arguments=[
                deepcopy(ARG_PROJECT),
            ],
            tags=["secretary", "priority"],
        ),
        command_spec(
            command_id="review_assistant",
            title="Generate review report",
            description="生成项目复盘和问题检查报告。",
            category="secretary",
            script="review_assistant.py",
            arguments=[
                deepcopy(ARG_PROJECT),
            ],
            tags=["secretary", "review"],
        ),
        command_spec(
            command_id="secretary_report",
            title="Generate secretary report",
            description="生成个人项目秘书综合汇报。",
            category="secretary",
            script="secretary_report.py",
            arguments=[
                deepcopy(ARG_PROJECT),
            ],
            tags=["secretary", "report"],
        ),

        # ----------------------------------------------------
        # eval
        # ----------------------------------------------------
        command_spec(
            command_id="retrieval_eval",
            title="Run retrieval evaluation",
            description="基于 retrieval_eval.json 评估 vector / keyword / hybrid 检索质量。",
            category="eval",
            script="retrieval_eval.py",
            arguments=[
                arg_spec(
                    name="mode",
                    flag="--mode",
                    arg_type="choice",
                    required=False,
                    default="all",
                    choices=["vector", "keyword", "hybrid", "all"],
                    description="评估模式。",
                    example="all",
                ),
                arg_spec(
                    name="top_k",
                    flag="--top-k",
                    arg_type="str",
                    required=False,
                    description="TopK 列表，例如 1,3,5,10。",
                    example="1,3,5",
                ),
                deepcopy(ARG_LIMIT),
                deepcopy(ARG_MAX_SCAN_POINTS),
                deepcopy(ARG_VECTOR_WEIGHT),
                deepcopy(ARG_KEYWORD_WEIGHT),
                arg_spec(
                    name="no_save",
                    flag="--no-save",
                    arg_type="bool",
                    required=False,
                    default=False,
                    description="只在终端输出，不保存 Markdown 报告。",
                ),
            ],
            tags=["eval", "retrieval", "topk"],
        ),

        # ----------------------------------------------------
        # milestone
        # ----------------------------------------------------
        command_spec(
            command_id="milestone_closeout",
            title="Generate milestone closeout",
            description="生成里程碑封版报告，例如 M1 / M2 / M3 / M4。",
            category="milestone",
            script="milestone_closeout.py",
            arguments=[
                arg_spec(
                    name="milestone",
                    flag="--milestone",
                    arg_type="str",
                    required=True,
                    description="里程碑编号，例如 M3。",
                    example="M3",
                ),
                arg_spec(
                    name="skip_health",
                    flag="--skip-health",
                    arg_type="bool",
                    required=False,
                    default=False,
                    description="跳过健康检查。",
                ),
            ],
            tags=["milestone", "closeout"],
        ),
    ]

    registry = {}

    for item in commands:
        command_id = item["id"]

        if command_id in registry:
            raise ValueError(f"重复的 command id：{command_id}")

        registry[command_id] = item

    return registry


# ============================================================
# 查询与显示函数
# ============================================================

def get_command_registry() -> dict[str, dict]:
    """
    获取命令注册表。

    后续 launcher.py 和 Web UI 可以直接 import 这个函数。
    """
    return build_command_registry()


def get_command(command_id: str) -> dict | None:
    """
    根据 id 获取命令。
    """
    registry = get_command_registry()
    return registry.get(command_id)


def list_categories() -> list[str]:
    """
    返回所有命令分类。
    """
    registry = get_command_registry()
    return sorted({item["category"] for item in registry.values()})


def list_commands(category: str | None = None) -> list[dict]:
    """
    返回命令列表，可按 category 过滤。
    """
    registry = get_command_registry()
    commands = list(registry.values())

    if category:
        commands = [
            item
            for item in commands
            if item.get("category") == category
        ]

    return sorted(commands, key=lambda item: (item["category"], item["id"]))


def bool_text(value: bool) -> str:
    """
    布尔值显示。
    """
    return "yes" if value else "no"


def print_categories() -> None:
    """
    打印分类列表。
    """
    print("Command categories:")
    print("")

    for category in list_categories():
        print(f"- {category}")


def print_command_list(category: str | None = None) -> None:
    """
    打印命令列表。
    """
    commands = list_commands(category=category)

    if category:
        print(f"Command list, category={category}")
    else:
        print("Command list")

    print("")

    if not commands:
        print("No commands found.")
        return

    print(f"{'ID':<24} {'Category':<12} {'Script':<28} {'Danger':<8} Title")
    print("-" * 96)

    for item in commands:
        print(
            f"{item['id']:<24} "
            f"{item['category']:<12} "
            f"{item['script']:<28} "
            f"{bool_text(item.get('dangerous', False)):<8} "
            f"{item['title']}"
        )


def print_argument_detail(argument: dict, index: int) -> None:
    """
    打印单个参数详情。
    """
    print(f"  {index}. {argument.get('name', '')}")

    if argument.get("flag"):
        print(f"     flag: {argument.get('flag')}")

    if argument.get("positional"):
        print("     positional: yes")

    print(f"     type: {argument.get('type', '')}")
    print(f"     required: {bool_text(argument.get('required', False))}")

    if argument.get("default") is not None:
        print(f"     default: {argument.get('default')}")

    if argument.get("choices"):
        print(f"     choices: {', '.join(argument.get('choices', []))}")

    if argument.get("multiple"):
        print("     multiple: yes")

    if argument.get("dangerous"):
        print("     dangerous: yes")

    if argument.get("requires_confirmation"):
        print("     requires_confirmation: yes")

    if argument.get("example"):
        print(f"     example: {argument.get('example')}")

    if argument.get("description"):
        print(f"     description: {argument.get('description')}")


def print_command_detail(command_id: str) -> None:
    """
    打印单个命令详情。
    """
    command = get_command(command_id)

    if not command:
        print(f"Command not found: {command_id}")
        print("")
        print("Use this command to list available commands:")
        print("python command_registry.py --list")
        raise SystemExit(1)

    print(f"ID: {command['id']}")
    print(f"Title: {command['title']}")
    print(f"Category: {command['category']}")
    print(f"Script: {command['script']}")
    print(f"Dangerous: {bool_text(command.get('dangerous', False))}")
    print(
        "Requires confirmation: "
        f"{bool_text(command.get('requires_confirmation', False))}"
    )
    print(f"Description: {command['description']}")

    if command.get("tags"):
        print(f"Tags: {', '.join(command.get('tags', []))}")

    print("")
    print("Arguments:")

    arguments = command.get("arguments", [])

    if not arguments:
        print("  No arguments.")
        return

    for index, argument in enumerate(arguments, start=1):
        print_argument_detail(argument, index)


def print_json_output(command_id: str | None = None, category: str | None = None) -> None:
    """
    输出 JSON。
    """
    if command_id:
        data = get_command(command_id)

        if not data:
            raise SystemExit(f"Command not found: {command_id}")

    else:
        commands = list_commands(category=category)
        data = {
            "version": 1,
            "commands": commands,
            "categories": list_categories(),
        }

    print(json.dumps(data, ensure_ascii=False, indent=2))


# ============================================================
# 命令行入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Personal Project Secretary command registry"
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="列出已注册命令。",
    )

    parser.add_argument(
        "--show",
        default=None,
        help="显示指定命令详情，例如 ask。",
    )

    parser.add_argument(
        "--category",
        default=None,
        help="按分类过滤命令，例如 report、secretary、index。",
    )

    parser.add_argument(
        "--categories",
        action="store_true",
        help="列出所有命令分类。",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出。",
    )

    args = parser.parse_args()

    if args.json:
        print_json_output(
            command_id=args.show,
            category=args.category,
        )
        return

    if args.categories:
        print_categories()
        return

    if args.show:
        print_command_detail(args.show)
        return

    # 默认行为：列出命令。
    if args.list or not any(
        [
            args.list,
            args.show,
            args.category,
            args.categories,
            args.json,
        ]
    ):
        print_command_list(category=args.category)
        return

    if args.category:
        print_command_list(category=args.category)
        return


if __name__ == "__main__":
    main()

