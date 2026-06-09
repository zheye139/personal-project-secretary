import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import config
import search_docs


# ============================================================
# 基础配置
# ============================================================

KNOWLEDGE_ROOT = config.KNOWLEDGE_ROOT

EVAL_DIR = getattr(
    config,
    "EVAL_DIR",
    KNOWLEDGE_ROOT / "99_System" / "eval",
)

RETRIEVAL_EVAL_PATH = getattr(
    config,
    "RETRIEVAL_EVAL_PATH",
    EVAL_DIR / "retrieval_eval.json",
)

RETRIEVAL_EVAL_REPORT_DIR = getattr(
    config,
    "RETRIEVAL_EVAL_REPORT_DIR",
    KNOWLEDGE_ROOT / "05_Summaries" / "retrieval_eval_reports",
)


# ============================================================
# Windows / PowerShell 中文输出处理
# ============================================================

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


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


def now_iso() -> str:
    """
    返回当前 ISO 时间字符串。
    """
    return datetime.now().isoformat(timespec="seconds")


def now_timestamp() -> str:
    """
    返回适合文件名使用的时间戳。
    """
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def load_eval_set(path: Path) -> dict:
    """
    读取 retrieval_eval.json。
    """
    if not path.exists():
        raise FileNotFoundError(f"评估测试集不存在：{path}")

    data = json.loads(path.read_text(encoding="utf-8"))

    if "cases" not in data or not isinstance(data["cases"], list):
        raise ValueError("retrieval_eval.json 格式错误：缺少 cases 列表。")

    return data


def parse_top_k(raw_top_k: str | None, default_top_k: list[int]) -> list[int]:
    """
    解析 --top-k 参数。

    示例：
    --top-k 1,3,5
    """
    if not raw_top_k:
        return default_top_k

    result = []

    for item in raw_top_k.split(","):
        item = item.strip()

        if not item:
            continue

        result.append(int(item))

    return sorted(set(result))


def normalize_text(value) -> str:
    """
    转成小写文本，用于关键词命中判断。
    """
    if value is None:
        return ""

    if isinstance(value, list):
        value = " ".join(str(item) for item in value)

    return str(value).lower()


def payload_combined_text(payload: dict) -> str:
    """
    合并 payload 中用于判断关键词命中的字段。
    """
    fields = [
        payload.get("title", ""),
        payload.get("file_name", ""),
        payload.get("source", ""),
        payload.get("doc_type", ""),
        payload.get("category", ""),
        payload.get("project", ""),
        payload.get("tags", []),
        payload.get("text", ""),
    ]

    return normalize_text(" ".join(normalize_text(field) for field in fields))


def expected_keyword_hits(case: dict, payload: dict) -> list[str]:
    """
    返回当前 payload 命中的 expected_keywords。
    """
    expected_keywords = case.get("expected_keywords", []) or []
    combined = payload_combined_text(payload)

    hits = []

    for keyword in expected_keywords:
        keyword_norm = normalize_text(keyword)

        if keyword_norm and keyword_norm in combined:
            hits.append(str(keyword))

    return hits


def result_matches_case(case: dict, item: dict) -> tuple[bool, dict]:
    """
    判断单条检索结果是否命中当前 case。

    命中逻辑：
    1. expected_project 如果存在，必须匹配 payload.project。
    2. expected_doc_type 如果存在，必须匹配 payload.doc_type。
    3. expected_file_contains 如果存在，必须出现在 source 或 file_name 中。
    4. expected_keywords 至少命中 min_keyword_hits 个，默认 1 个。
    """
    payload = item.get("payload", {}) or {}

    expected_project = str(case.get("expected_project", "") or "").strip()
    expected_doc_type = str(case.get("expected_doc_type", "") or "").strip()
    expected_file_contains = str(case.get("expected_file_contains", "") or "").strip()

    payload_project = str(payload.get("project", "") or "").strip()
    payload_doc_type = str(payload.get("doc_type", "") or "").strip()
    payload_source = str(payload.get("source", "") or "")
    payload_file_name = str(payload.get("file_name", "") or "")

    checks = {}

    if expected_project:
        checks["project"] = payload_project == expected_project
    else:
        checks["project"] = True

    if expected_doc_type:
        checks["doc_type"] = payload_doc_type == expected_doc_type
    else:
        checks["doc_type"] = True

    if expected_file_contains:
        checks["file"] = (
            expected_file_contains.lower() in payload_source.lower()
            or expected_file_contains.lower() in payload_file_name.lower()
        )
    else:
        checks["file"] = True

    keyword_hits = expected_keyword_hits(case, payload)
    expected_keywords = case.get("expected_keywords", []) or []
    min_keyword_hits = int(case.get("min_keyword_hits", 1))

    if expected_keywords:
        checks["keywords"] = len(keyword_hits) >= min_keyword_hits
    else:
        checks["keywords"] = True

    matched = all(checks.values())

    detail = {
        "checks": checks,
        "keyword_hits": keyword_hits,
        "payload_project": payload_project,
        "payload_doc_type": payload_doc_type,
        "payload_source": payload_source,
        "payload_file_name": payload_file_name,
    }

    return matched, detail


def find_first_hit_rank(case: dict, results: list[dict]) -> tuple[int | None, dict | None]:
    """
    返回首次命中的排名，从 1 开始。
    如果没有命中，返回 None。
    """
    for index, item in enumerate(results, start=1):
        matched, detail = result_matches_case(case, item)

        if matched:
            return index, detail

    return None, None


def top_k_hit(first_hit_rank: int | None, k: int) -> bool:
    """
    判断是否 TopK 命中。
    """
    if first_hit_rank is None:
        return False

    return first_hit_rank <= k


def run_search_for_case(
    client,
    case: dict,
    mode: str,
    limit: int,
    max_scan_points: int,
    vector_weight: float,
    keyword_weight: float,
) -> list[dict]:
    """
    对单条 case 执行指定模式检索。

    这里复用 search_docs.py 中已经实现的 vector / keyword / hybrid 检索函数。
    """
    question = case["question"]

    query_filter = search_docs.build_filter(
        project=case.get("filter_project"),
        doc_type=case.get("filter_doc_type"),
        category=case.get("filter_category"),
        tag=case.get("filter_tag"),
    )

    if mode == "vector":
        return search_docs.vector_search(
            client=client,
            query=question,
            query_filter=query_filter,
            limit=limit,
        )

    if mode == "keyword":
        return search_docs.keyword_search(
            client=client,
            query=question,
            query_filter=query_filter,
            limit=limit,
            max_scan_points=max_scan_points,
        )

    if mode == "hybrid":
        return search_docs.hybrid_search(
            client=client,
            query=question,
            query_filter=query_filter,
            limit=limit,
            max_scan_points=max_scan_points,
            vector_weight=vector_weight,
            keyword_weight=keyword_weight,
        )

    raise ValueError(f"不支持的评估模式：{mode}")


def evaluate_mode(
    eval_set: dict,
    mode: str,
    top_k_values: list[int],
    limit: int,
    max_scan_points: int,
    vector_weight: float,
    keyword_weight: float,
) -> dict:
    """
    执行某一种检索模式的评估。
    """
    cases = eval_set.get("cases", [])

    mode_result = {
        "mode": mode,
        "total_cases": len(cases),
        "top_k_values": top_k_values,
        "top_k_hits": {str(k): 0 for k in top_k_values},
        "cases": [],
    }

    client = search_docs.get_qdrant_client()

    try:
        for case in cases:
            case_id = case.get("id", "")
            question = case.get("question", "")

            print("")
            print(f"[{mode}] 评估：{case_id}")
            print(f"问题：{question}")

            results = run_search_for_case(
                client=client,
                case=case,
                mode=mode,
                limit=limit,
                max_scan_points=max_scan_points,
                vector_weight=vector_weight,
                keyword_weight=keyword_weight,
            )

            first_hit_rank, hit_detail = find_first_hit_rank(case, results)

            case_result = {
                "id": case_id,
                "question": question,
                "first_hit_rank": first_hit_rank,
                "top_k": {},
                "expected_project": case.get("expected_project", ""),
                "expected_doc_type": case.get("expected_doc_type", ""),
                "expected_file_contains": case.get("expected_file_contains", ""),
                "expected_keywords": case.get("expected_keywords", []),
                "hit_detail": hit_detail,
                "top_results": [],
            }

            for k in top_k_values:
                hit = top_k_hit(first_hit_rank, k)
                case_result["top_k"][str(k)] = hit

                if hit:
                    mode_result["top_k_hits"][str(k)] += 1

            for rank, item in enumerate(results, start=1):
                payload = item.get("payload", {}) or {}

                case_result["top_results"].append(
                    {
                        "rank": rank,
                        "score": float(item.get("score", 0.0)),
                        "mode": item.get("mode", mode),
                        "source": payload.get("source", ""),
                        "doc_type": payload.get("doc_type", ""),
                        "project": payload.get("project", ""),
                        "title": payload.get("title", ""),
                        "file_name": payload.get("file_name", ""),
                    }
                )

            if first_hit_rank is None:
                print("命中结果：未命中")
            else:
                print(f"命中结果：Top{first_hit_rank}")

            mode_result["cases"].append(case_result)

    finally:
        try:
            client.close()
        except Exception:
            pass

    mode_result["top_k_rates"] = {}

    for k in top_k_values:
        hit_count = mode_result["top_k_hits"][str(k)]
        total = mode_result["total_cases"]

        if total == 0:
            rate = 0.0
        else:
            rate = hit_count / total

        mode_result["top_k_rates"][str(k)] = rate

    return mode_result


def evaluate_all_modes(
    eval_set: dict,
    modes: list[str],
    top_k_values: list[int],
    limit: int,
    max_scan_points: int,
    vector_weight: float,
    keyword_weight: float,
) -> dict:
    """
    执行多个模式评估。
    """
    results = {
        "created_at": now_iso(),
        "eval_name": eval_set.get("name", ""),
        "eval_version": eval_set.get("version", ""),
        "modes": {},
    }

    for mode in modes:
        print("")
        print("=" * 80)
        print(f"开始评估模式：{mode}")
        print("=" * 80)

        results["modes"][mode] = evaluate_mode(
            eval_set=eval_set,
            mode=mode,
            top_k_values=top_k_values,
            limit=limit,
            max_scan_points=max_scan_points,
            vector_weight=vector_weight,
            keyword_weight=keyword_weight,
        )

    return results


def format_percent(value: float) -> str:
    """
    格式化百分比。
    """
    return f"{value * 100:.1f}%"


def build_markdown_report(
    eval_set: dict,
    eval_results: dict,
    top_k_values: list[int],
    limit: int,
    max_scan_points: int,
    vector_weight: float,
    keyword_weight: float,
) -> str:
    """
    生成 Markdown 评估报告。
    """
    now = now_iso()

    lines = []

    lines.append("---")
    lines.append(f"title: 检索评估报告 {now_timestamp()}")
    lines.append(f"created: {now}")
    lines.append("category: summary")
    lines.append("project: Personal_Project_Assistant")
    lines.append("doc_type: retrieval_eval_report")
    lines.append("tags: [检索评估, M3.9, retrieval_eval, 自动生成]")
    lines.append("---")
    lines.append("")

    lines.append("# 检索评估报告")
    lines.append("")
    lines.append(f"生成时间：{now}")
    lines.append(f"测试集：{eval_set.get('name', '')}")
    lines.append(f"测试集版本：{eval_set.get('version', '')}")
    lines.append(f"测试用例数量：{len(eval_set.get('cases', []))}")
    lines.append(f"评估 TopK：{top_k_values}")
    lines.append(f"检索 limit：{limit}")
    lines.append(f"max_scan_points：{max_scan_points}")
    lines.append(f"hybrid vector_weight：{vector_weight}")
    lines.append(f"hybrid keyword_weight：{keyword_weight}")
    lines.append("")

    lines.append("## 1. 总体结果")
    lines.append("")

    header = ["模式"] + [f"Top{k}" for k in top_k_values]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(["---"] * len(header)) + " |")

    for mode, mode_result in eval_results.get("modes", {}).items():
        row = [mode]

        for k in top_k_values:
            rate = mode_result["top_k_rates"].get(str(k), 0.0)
            hit_count = mode_result["top_k_hits"].get(str(k), 0)
            total = mode_result.get("total_cases", 0)
            row.append(f"{format_percent(rate)} ({hit_count}/{total})")

        lines.append("| " + " | ".join(row) + " |")

    lines.append("")
    lines.append("## 2. 分模式明细")
    lines.append("")

    for mode, mode_result in eval_results.get("modes", {}).items():
        lines.append(f"### 2.{list(eval_results['modes'].keys()).index(mode) + 1} 模式：{mode}")
        lines.append("")

        lines.append("| Case | 问题 | 首次命中 | Top1 | Top3 | Top5 |")
        lines.append("| --- | --- | --- | --- | --- | --- |")

        for case_result in mode_result.get("cases", []):
            first_hit = case_result.get("first_hit_rank")
            first_hit_text = f"Top{first_hit}" if first_hit is not None else "未命中"

            top1 = "是" if case_result.get("top_k", {}).get("1", False) else "否"
            top3 = "是" if case_result.get("top_k", {}).get("3", False) else "否"
            top5 = "是" if case_result.get("top_k", {}).get("5", False) else "否"

            question = case_result.get("question", "").replace("|", "/")

            lines.append(
                "| "
                + " | ".join(
                    [
                        case_result.get("id", ""),
                        question,
                        first_hit_text,
                        top1,
                        top3,
                        top5,
                    ]
                )
                + " |"
            )

        lines.append("")

    lines.append("## 3. 未命中 Case 详情")
    lines.append("")

    any_miss = False

    for mode, mode_result in eval_results.get("modes", {}).items():
        missed_cases = [
            item
            for item in mode_result.get("cases", [])
            if item.get("first_hit_rank") is None
        ]

        if not missed_cases:
            continue

        any_miss = True
        lines.append(f"### 模式：{mode}")
        lines.append("")

        for case_result in missed_cases:
            lines.append(f"#### {case_result.get('id', '')}")
            lines.append("")
            lines.append(f"- 问题：{case_result.get('question', '')}")
            lines.append(f"- 期望项目：{case_result.get('expected_project', '')}")
            lines.append(f"- 期望文档类型：{case_result.get('expected_doc_type', '')}")
            lines.append(f"- 期望文件包含：{case_result.get('expected_file_contains', '')}")
            lines.append(f"- 期望关键词：{case_result.get('expected_keywords', [])}")
            lines.append("")
            lines.append("Top 结果：")
            lines.append("")

            for result in case_result.get("top_results", [])[:5]:
                lines.append(
                    f"- Top{result.get('rank')}: "
                    f"{result.get('doc_type', '')} | "
                    f"{result.get('source', '')} | "
                    f"score={result.get('score', 0):.4f}"
                )

            lines.append("")

    if not any_miss:
        lines.append("没有未命中的 case。")
        lines.append("")

    lines.append("## 4. 后续建议")
    lines.append("")
    lines.append("1. 如果 keyword 命中率明显高于 vector，说明测试集偏脚本名、错误码和精确术语。")
    lines.append("2. 如果 vector 命中率较低，可以考虑优化 chunk 切分、增加标题和摘要信息。")
    lines.append("3. 如果 hybrid 命中率没有提升，需要调整 vector_weight 和 keyword_weight。")
    lines.append("4. 后续可以增加更多真实问答用例，形成长期检索回归测试。")
    lines.append("")

    return "\n".join(lines)


def save_report(markdown_report: str) -> Path:
    """
    保存 Markdown 评估报告。
    """
    RETRIEVAL_EVAL_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    report_path = (
        RETRIEVAL_EVAL_REPORT_DIR
        / f"{now_timestamp()}_retrieval_eval_report.md"
    )

    report_path.write_text(markdown_report, encoding="utf-8")
    return report_path


def print_terminal_summary(eval_results: dict, top_k_values: list[int]) -> None:
    """
    在终端打印整体评估摘要。
    """
    print("")
    print("=" * 80)
    print("检索评估摘要")
    print("=" * 80)

    for mode, mode_result in eval_results.get("modes", {}).items():
        print("")
        print(f"模式：{mode}")

        for k in top_k_values:
            key = str(k)
            hit_count = mode_result["top_k_hits"].get(key, 0)
            total = mode_result.get("total_cases", 0)
            rate = mode_result["top_k_rates"].get(key, 0.0)

            print(f"Top{k}: {format_percent(rate)} ({hit_count}/{total})")


def main():
    parser = argparse.ArgumentParser(
        description="个人项目秘书 + 数据知识库：检索质量评估工具"
    )

    parser.add_argument(
        "--mode",
        choices=["vector", "keyword", "hybrid", "all"],
        default="all",
        help="评估模式。默认 all。",
    )

    parser.add_argument(
        "--eval-path",
        default=str(RETRIEVAL_EVAL_PATH),
        help="retrieval_eval.json 路径。",
    )

    parser.add_argument(
        "--top-k",
        default=None,
        help="TopK 评估列表，例如 1,3,5。默认读取测试集 default_top_k。",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="每条 case 返回多少条检索结果。",
    )

    parser.add_argument(
        "--max-scan-points",
        type=int,
        default=5000,
        help="keyword / hybrid 模式最多扫描多少个 Qdrant points。",
    )

    parser.add_argument(
        "--vector-weight",
        type=float,
        default=0.6,
        help="hybrid 模式下向量检索权重。",
    )

    parser.add_argument(
        "--keyword-weight",
        type=float,
        default=0.4,
        help="hybrid 模式下关键词检索权重。",
    )

    parser.add_argument(
        "--no-save",
        action="store_true",
        help="只在终端输出，不保存 Markdown 报告。",
    )

    args = parser.parse_args()

    eval_path = Path(args.eval_path)

    eval_set = load_eval_set(eval_path)

    default_top_k = eval_set.get("default_top_k", [1, 3, 5])
    top_k_values = parse_top_k(args.top_k, default_top_k)

    if args.mode == "all":
        modes = ["vector", "keyword", "hybrid"]
    else:
        modes = [args.mode]

    print("个人项目秘书 + 数据知识库：检索质量评估")
    print(f"测试集：{eval_path}")
    print(f"评估模式：{modes}")
    print(f"TopK：{top_k_values}")
    print(f"limit：{args.limit}")
    print(f"max_scan_points：{args.max_scan_points}")
    print(f"vector_weight：{args.vector_weight}")
    print(f"keyword_weight：{args.keyword_weight}")

    eval_results = evaluate_all_modes(
        eval_set=eval_set,
        modes=modes,
        top_k_values=top_k_values,
        limit=args.limit,
        max_scan_points=args.max_scan_points,
        vector_weight=args.vector_weight,
        keyword_weight=args.keyword_weight,
    )

    print_terminal_summary(
        eval_results=eval_results,
        top_k_values=top_k_values,
    )

    markdown_report = build_markdown_report(
        eval_set=eval_set,
        eval_results=eval_results,
        top_k_values=top_k_values,
        limit=args.limit,
        max_scan_points=args.max_scan_points,
        vector_weight=args.vector_weight,
        keyword_weight=args.keyword_weight,
    )

    if args.no_save:
        print("")
        print("已选择 --no-save，未保存 Markdown 报告。")
        return

    report_path = save_report(markdown_report)

    print("")
    print("检索评估报告已保存：")
    print(report_path)
    print("")
    print("建议下一步执行：")
    print("python update_index.py --project Personal_Project_Assistant")
    print(
        'python ask.py --doc-type retrieval_eval_report '
        '"检索评估结果如何？"'
    )


if __name__ == "__main__":
    main()

