from __future__ import annotations

import argparse
import ast
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path


EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ipynb_checkpoints",
    "node_modules",
}

LOCAL_EXTENSIONS = {".py", ".js", ".html", ".css", ".md", ".txt", ".json"}


@dataclass
class Edge:
    source: str
    target: str
    kind: str
    detail: str = ""


@dataclass
class FileNode:
    path: str
    kind: str
    tags: list[str] = field(default_factory=list)


def should_skip(path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in path.parts)


def iter_project_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_file() and not should_skip(path):
            files.append(path)
    return sorted(files)


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def classify_file(path: Path) -> FileNode:
    relative = path.as_posix()
    tags: list[str] = []

    if relative == "backend/app/main.py":
        tags.extend(["entrypoint", "fastapi", "serves_frontend"])
    elif relative.endswith("/simulation.py"):
        tags.extend(["api_route"])
    elif "/domain/" in relative:
        tags.extend(["domain_logic"])
    elif "/services/" in relative:
        tags.extend(["service"])
    elif "/schemas/" in relative:
        tags.extend(["schema"])
    elif relative.startswith("frontend/"):
        tags.extend(["frontend"])
    elif relative.startswith("backend/legacy/"):
        tags.extend(["legacy"])
    elif relative.startswith("backend/references/"):
        tags.extend(["reference"])
    elif path.name == "AGENTS.md":
        tags.extend(["agent_context"])

    return FileNode(path=relative, kind=path.suffix.lstrip(".") or "file", tags=tags)


def python_module_name(path: Path, root: Path) -> str | None:
    relative = path.relative_to(root)
    if relative.suffix != ".py":
        return None
    module = ".".join(relative.with_suffix("").parts)
    return module


def build_python_module_index(files: list[Path], root: Path) -> dict[str, Path]:
    index: dict[str, Path] = {}
    for path in files:
        module_name = python_module_name(path, root)
        if module_name:
            index[module_name] = path
    return index


def resolve_python_import(
    module_index: dict[str, Path],
    current_module: str,
    imported_module: str | None,
    level: int = 0,
) -> Path | None:
    if level == 0:
        if not imported_module:
            return None
        return module_index.get(imported_module)

    current_parts = current_module.split(".")
    base_parts = current_parts[:-level]
    if imported_module:
        base_parts += imported_module.split(".")
    candidate = ".".join(base_parts)
    return module_index.get(candidate)


def parse_python_edges(path: Path, root: Path, module_index: dict[str, Path]) -> list[Edge]:
    edges: list[Edge] = []
    source = rel(path, root)
    current_module = python_module_name(path, root)
    if not current_module:
        return edges

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return edges

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                target_path = resolve_python_import(module_index, current_module, alias.name, level=0)
                if target_path:
                    edges.append(
                        Edge(
                            source=source,
                            target=rel(target_path, root),
                            kind="python_import",
                            detail=alias.name,
                        )
                    )
        elif isinstance(node, ast.ImportFrom):
            target_path = resolve_python_import(
                module_index,
                current_module,
                node.module,
                level=node.level,
            )
            if target_path:
                edges.append(
                    Edge(
                        source=source,
                        target=rel(target_path, root),
                        kind="python_import",
                        detail=f"from {'.' * node.level}{node.module or ''}",
                    )
                )
        elif isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr

            if func_name == "StaticFiles":
                for keyword in node.keywords:
                    if keyword.arg == "directory":
                        value = ast.unparse(keyword.value)
                        edges.append(
                            Edge(
                                source=source,
                                target="frontend/",
                                kind="serves_directory",
                                detail=value,
                            )
                        )
            elif func_name in {"read_text", "read_bytes", "open"}:
                detail = ast.unparse(node)
                edges.append(
                    Edge(
                        source=source,
                        target="(dynamic file access)",
                        kind="file_io_hint",
                        detail=detail[:140],
                    )
                )

    return edges


def parse_html_edges(path: Path, root: Path) -> list[Edge]:
    content = path.read_text(encoding="utf-8")
    source = rel(path, root)
    edges: list[Edge] = []

    for match in re.finditer(r"""(?:src|href)=["']([^"']+)["']""", content):
        asset = match.group(1)
        if asset.startswith("/app/"):
            target = asset.removeprefix("/app/")
            edges.append(Edge(source=source, target=f"frontend/{target}", kind="asset_ref", detail=asset))
        elif asset.startswith("./") or asset.startswith("../"):
            edges.append(Edge(source=source, target=asset, kind="asset_ref", detail=asset))

    return edges


def parse_js_edges(path: Path, root: Path) -> list[Edge]:
    content = path.read_text(encoding="utf-8")
    source = rel(path, root)
    edges: list[Edge] = []

    for match in re.finditer(r"""fetch\(\s*["']([^"']+)["']""", content):
        endpoint = match.group(1)
        edges.append(Edge(source=source, target=endpoint, kind="api_call", detail="fetch"))

    for match in re.finditer(r"""["'](/app/[^"']+)["']""", content):
        asset = match.group(1)
        target = asset.removeprefix("/app/")
        edges.append(Edge(source=source, target=f"frontend/{target}", kind="asset_ref", detail=asset))

    return edges


def parse_requirements(path: Path, root: Path) -> list[Edge]:
    edges: list[Edge] = []
    source = rel(path, root)
    for line in path.read_text(encoding="utf-8").splitlines():
        dependency = line.strip()
        if not dependency or dependency.startswith("#"):
            continue
        edges.append(Edge(source=source, target=dependency, kind="dependency", detail="requirements"))
    return edges


def build_tree_lines(root: Path) -> list[str]:
    lines: list[str] = []

    def walk(directory: Path, prefix: str = "") -> None:
        entries = [
            path
            for path in sorted(directory.iterdir(), key=lambda item: (item.is_file(), item.name.lower()))
            if not should_skip(path)
        ]
        for index, entry in enumerate(entries):
            connector = "└── " if index == len(entries) - 1 else "├── "
            lines.append(f"{prefix}{connector}{entry.name}")
            if entry.is_dir():
                extension = "    " if index == len(entries) - 1 else "│   "
                walk(entry, prefix + extension)

    lines.append(root.name)
    walk(root)
    return lines


def build_report(root: Path) -> dict[str, object]:
    files = iter_project_files(root)
    file_nodes = [classify_file(Path(rel(path, root))) for path in files if path.suffix in LOCAL_EXTENSIONS]
    module_index = build_python_module_index(files, root)
    edges: list[Edge] = []

    for path in files:
        if path.suffix == ".py":
            edges.extend(parse_python_edges(path, root, module_index))
        elif path.suffix == ".html":
            edges.extend(parse_html_edges(path, root))
        elif path.suffix == ".js":
            edges.extend(parse_js_edges(path, root))
        elif path.name == "requirements.txt":
            edges.extend(parse_requirements(path, root))

    entrypoints = [
        "backend/app/main.py",
        "frontend/index.html",
        "frontend/app.js",
    ]

    return {
        "root": root.name,
        "entrypoints": entrypoints,
        "files": [asdict(node) for node in file_nodes],
        "edges": [asdict(edge) for edge in edges],
        "tree": build_tree_lines(root),
    }


def group_files_by_layer(files: list[dict[str, object]]) -> dict[str, list[str]]:
    layers = {
        "frontend": [],
        "api": [],
        "services": [],
        "domain": [],
        "schemas": [],
        "references": [],
        "legacy": [],
        "tooling_docs": [],
        "other": [],
    }

    for file_node in files:
        path = file_node["path"]
        tags = set(file_node["tags"])
        if path.startswith("frontend/"):
            layers["frontend"].append(path)
        elif path.startswith("backend/app/api/"):
            layers["api"].append(path)
        elif path.startswith("backend/app/services/"):
            layers["services"].append(path)
        elif path.startswith("backend/app/domain/"):
            layers["domain"].append(path)
        elif path.startswith("backend/app/schemas/"):
            layers["schemas"].append(path)
        elif path.startswith("backend/references/"):
            layers["references"].append(path)
        elif path.startswith("backend/legacy/"):
            layers["legacy"].append(path)
        elif path in {"README.md", "AGENTS.md", "backend/README.md", "frontend/README.md"} or "agent_context" in tags:
            layers["tooling_docs"].append(path)
        else:
            layers["other"].append(path)

    return {name: values for name, values in layers.items() if values}


def mermaid_id(path: str) -> str:
    sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", path)
    if sanitized and sanitized[0].isdigit():
        sanitized = f"n_{sanitized}"
    return sanitized


def build_mermaid(report: dict[str, object]) -> list[str]:
    files = report["files"]
    edges = report["edges"]
    allowed_prefixes = ("frontend/", "backend/app/", "backend/references/", "backend/legacy/")
    selected_files = [node for node in files if node["path"].startswith(allowed_prefixes)]
    selected_paths = {node["path"] for node in selected_files}

    lines = ["flowchart LR"]
    grouped = group_files_by_layer(selected_files)

    for layer_name, paths in grouped.items():
        lines.append(f"  subgraph {layer_name}[{layer_name}]")
        for path in paths:
            lines.append(f'    {mermaid_id(path)}["{path}"]')
        lines.append("  end")

    for edge in edges:
        source = edge["source"]
        target = edge["target"]
        if source in selected_paths and target in selected_paths:
            lines.append(f"  {mermaid_id(source)} -->|{edge['kind']}| {mermaid_id(target)}")
        elif source in selected_paths and str(target).startswith("/simulation"):
            endpoint_id = mermaid_id(f"endpoint_{target}")
            lines.append(f'  {endpoint_id}["{target}"]')
            lines.append(f"  {mermaid_id(source)} -->|api_call| {endpoint_id}")

    return lines


def render_markdown(report: dict[str, object]) -> str:
    lines: list[str] = []
    lines.append(f"# Project Map: {report['root']}")
    lines.append("")
    lines.append("## Entrypoints")
    for item in report["entrypoints"]:
        lines.append(f"- `{item}`")
    lines.append("")
    lines.append("## Tree")
    lines.append("```text")
    lines.extend(report["tree"])
    lines.append("```")
    lines.append("")
    lines.append("## Layers")
    for layer_name, paths in group_files_by_layer(report["files"]).items():
        lines.append(f"### {layer_name}")
        for path in paths:
            lines.append(f"- `{path}`")
        lines.append("")
    lines.append("## Mermaid")
    lines.append("```mermaid")
    lines.extend(build_mermaid(report))
    lines.append("```")
    lines.append("")
    lines.append("## Files")
    for file_node in report["files"]:
        tags = ", ".join(file_node["tags"]) if file_node["tags"] else "-"
        lines.append(f"- `{file_node['path']}` [{file_node['kind']}] tags: {tags}")
    lines.append("")
    lines.append("## Relationships")
    for edge in report["edges"]:
        detail = f" ({edge['detail']})" if edge["detail"] else ""
        lines.append(f"- `{edge['source']}` -> `{edge['target']}` [{edge['kind']}] {detail}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a static map of the project structure.")
    parser.add_argument("--root", default=".", help="Project root to inspect.")
    parser.add_argument("--format", choices=["md", "json"], default="md", help="Output format.")
    parser.add_argument("--output", help="Optional output file.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report = build_report(root)
    output = render_markdown(report) if args.format == "md" else json.dumps(report, indent=2)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
