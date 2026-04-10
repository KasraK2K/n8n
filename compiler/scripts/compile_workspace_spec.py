#!/usr/bin/env python3
"""Compile an n8n workspace bundle into import-ready workflow files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_workspace_spec import ValidationError, validate_spec_file


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "workflow"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def gather_usage(spec: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    usage: dict[str, list[dict[str, str]]] = {
        credential["name"]: [] for credential in spec["credentials"]
    }
    for workflow in spec["workflows"]:
        for node in workflow["nodes"]:
            for ref in node.get("credentialRefs", []):
                usage.setdefault(ref, []).append(
                    {"workflow": workflow["name"], "node": node["name"]}
                )
    return usage


def compile_node(node: dict[str, Any], credentials_by_name: dict[str, dict[str, Any]]) -> dict[str, Any]:
    compiled = {
        "parameters": node["parameters"],
        "name": node["name"],
        "type": node["type"],
        "typeVersion": node["typeVersion"],
        "position": node["position"],
    }
    if node.get("disabled"):
        compiled["disabled"] = True
    if node.get("notes"):
        compiled["notes"] = node["notes"]
        compiled["notesInFlow"] = True

    credential_bindings: dict[str, dict[str, str]] = {}
    for ref in node.get("credentialRefs", []):
        credential = credentials_by_name[ref]
        if credential.get("bindMode", "manual") != "byName":
            continue
        credential_type = credential["type"]
        if credential_type in credential_bindings:
            raise ValidationError(
                f"Node '{node['name']}' cannot bind more than one credential of type "
                f"'{credential_type}' by name"
            )
        credential_bindings[credential_type] = {"name": credential["name"]}

    if credential_bindings:
        compiled["credentials"] = credential_bindings
    return compiled


def compile_connections(connections: list[dict[str, Any]]) -> dict[str, Any]:
    compiled: dict[str, Any] = {}
    for edge in connections:
        source = edge["from"]
        target = edge["to"]
        source_bucket = compiled.setdefault(source["node"], {})
        output_bucket = source_bucket.setdefault(source["output"], [])
        while len(output_bucket) <= source["index"]:
            output_bucket.append([])
        output_bucket[source["index"]].append(
            {
                "node": target["node"],
                "type": target["input"],
                "index": target["index"],
            }
        )
    return compiled


def compile_workflow(
    workflow: dict[str, Any],
    credentials_by_name: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    return {
        "name": workflow["name"],
        "nodes": [compile_node(node, credentials_by_name) for node in workflow["nodes"]],
        "connections": compile_connections(workflow["connections"]),
        "settings": workflow["settings"],
        "staticData": None,
        "tags": [],
        "active": workflow["active"],
    }


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def build_import_plan(spec: dict[str, Any], workflow_files: dict[str, str]) -> dict[str, Any]:
    return {
        "specVersion": spec["specVersion"],
        "targetProfile": spec["targetProfile"]["id"],
        "workspace": spec["workspace"]["name"],
        "credentialCreationOrder": spec["importPlan"]["credentialCreationOrder"],
        "workflowImportOrder": [
            {"name": name, "file": workflow_files[name]}
            for name in spec["importPlan"]["workflowImportOrder"]
        ],
        "publishSteps": spec["importPlan"]["publishSteps"],
        "postImportChecks": spec["importPlan"]["postImportChecks"],
        "assumptions": spec["assumptions"],
    }


def compile_spec(spec: dict[str, Any], out_dir: Path) -> dict[str, str]:
    ensure_dir(out_dir)
    workflows_dir = out_dir / "workflows"
    ensure_dir(workflows_dir)

    credentials_by_name = {credential["name"]: credential for credential in spec["credentials"]}
    usage = gather_usage(spec)
    ordered_workflows = {
        workflow["name"]: workflow for workflow in spec["workflows"]
    }
    workflow_files: dict[str, str] = {}

    for index, workflow_name in enumerate(spec["importPlan"]["workflowImportOrder"], start=1):
        workflow = ordered_workflows[workflow_name]
        payload = compile_workflow(workflow, credentials_by_name)
        filename = f"{index:02d}-{slugify(workflow_name)}.workflow.json"
        path = workflows_dir / filename
        write_json(path, payload)
        workflow_files[workflow_name] = str(path)

    credential_manifest = []
    for credential_name in spec["importPlan"]["credentialCreationOrder"]:
        credential = credentials_by_name[credential_name]
        credential_manifest.append(
            {
                "name": credential["name"],
                "type": credential["type"],
                "bindMode": credential["bindMode"],
                "requiredFields": credential["requiredFields"],
                "placeholders": credential["placeholders"],
                "usedBy": usage.get(credential_name, []) or credential["usedBy"],
                "notes": credential["notes"],
            }
        )

    credentials_path = out_dir / "credentials.placeholders.json"
    write_json(credentials_path, credential_manifest)

    import_plan = build_import_plan(spec, workflow_files)
    import_plan_path = out_dir / "import-plan.json"
    write_json(import_plan_path, import_plan)

    return {
        "workflows_dir": str(workflows_dir),
        "credentials_manifest": str(credentials_path),
        "import_plan": str(import_plan_path),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compile an n8n workspace bundle JSON file into workflow exports."
    )
    parser.add_argument("spec", help="Path to the workspace bundle JSON file")
    parser.add_argument("--out", required=True, help="Directory where compiled files will be written")
    return parser.parse_args(argv[1:])


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        spec = validate_spec_file(args.spec)
        outputs = compile_spec(spec, Path(args.out).resolve())
    except ValidationError as exc:
        print(f"[ERROR] {exc}")
        return 1
    except OSError as exc:
        print(f"[ERROR] Failed to write compiled output: {exc}")
        return 1

    print("[OK] Compiled workspace bundle")
    print(f"  Workflows: {outputs['workflows_dir']}")
    print(f"  Credentials: {outputs['credentials_manifest']}")
    print(f"  Import plan: {outputs['import_plan']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
