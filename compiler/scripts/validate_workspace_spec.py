#!/usr/bin/env python3
"""Validate an n8n workspace bundle JSON file."""

from __future__ import annotations

import json
import re
import sys
from pathlib import PurePosixPath
from typing import Any


SPEC_VERSION = "1.0"
EXPECTED_TOP_LEVEL_KEYS = [
    "specVersion",
    "targetProfile",
    "workspace",
    "credentials",
    "files",
    "workflows",
    "importPlan",
    "assumptions",
]
BANNED_NODE_TYPES = {"n8n-nodes-base.executeCommand"}
ALLOWED_CONTENT_MODES = {"placeholder", "text", "json", "base64"}
ALLOWED_BIND_MODES = {"manual", "byName"}
NAME_PATTERN = re.compile(r"^[^\r\n\t]{1,128}$")


class ValidationError(Exception):
    """Raised when the workspace spec is invalid."""


def fail(message: str) -> None:
    raise ValidationError(message)


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def expect_keys(obj: dict[str, Any], required: list[str], label: str) -> None:
    missing = [key for key in required if key not in obj]
    if missing:
        fail(f"{label} is missing required keys: {', '.join(missing)}")


def expect_type(value: Any, expected_type: type | tuple[type, ...], label: str) -> None:
    if not isinstance(value, expected_type):
        if isinstance(expected_type, tuple):
            expected = ", ".join(t.__name__ for t in expected_type)
        else:
            expected = expected_type.__name__
        fail(f"{label} must be of type {expected}")


def expect_string(value: Any, label: str, *, non_empty: bool = True) -> str:
    expect_type(value, str, label)
    text = value.strip()
    if non_empty and not text:
        fail(f"{label} must be a non-empty string")
    return text


def expect_bool(value: Any, label: str) -> bool:
    expect_type(value, bool, label)
    return value


def expect_list(value: Any, label: str) -> list[Any]:
    expect_type(value, list, label)
    return value


def expect_dict(value: Any, label: str) -> dict[str, Any]:
    expect_type(value, dict, label)
    return value


def ensure_name(value: str, label: str) -> str:
    text = expect_string(value, label)
    if not NAME_PATTERN.match(text):
        fail(f"{label} must be 1-128 visible characters without tabs or newlines")
    return text


def ensure_string_list(values: Any, label: str) -> list[str]:
    items = expect_list(values, label)
    result: list[str] = []
    for index, item in enumerate(items):
        result.append(expect_string(item, f"{label}[{index}]"))
    return result


def ensure_unique(values: list[str], label: str) -> None:
    seen: set[str] = set()
    duplicates: list[str] = []
    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    if duplicates:
        fail(f"{label} contains duplicate values: {', '.join(duplicates)}")


def is_safe_files_path(path_text: str) -> bool:
    if not path_text.startswith("/files/"):
        return False
    if "\\" in path_text:
        return False
    pure = PurePosixPath(path_text)
    if any(part in {"..", "."} for part in pure.parts):
        return False
    return True


def is_trigger_type(node_type: str) -> bool:
    lower = node_type.lower()
    return (
        lower.endswith("trigger")
        or ".trigger" in lower
        or lower in {
            "n8n-nodes-base.manualtrigger",
            "n8n-nodes-base.webhook",
            "n8n-nodes-base.scheduletrigger",
            "n8n-nodes-base.errortrigger",
            "n8n-nodes-base.chattrigger",
            "n8n-nodes-base.formtrigger",
            "n8n-nodes-base.workflowtrigger",
            "n8n-nodes-base.localfiletrigger",
            "n8n-nodes-base.start",
        }
    )


def ensure_ref_list(
    refs: Any,
    label: str,
    *,
    workflow_names: set[str],
    node_names_by_workflow: dict[str, set[str]],
) -> list[dict[str, str]]:
    items = expect_list(refs, label)
    result: list[dict[str, str]] = []
    for index, item in enumerate(items):
        ref = expect_dict(item, f"{label}[{index}]")
        expect_keys(ref, ["workflow", "node"], f"{label}[{index}]")
        workflow_name = ensure_name(ref["workflow"], f"{label}[{index}].workflow")
        node_name = ensure_name(ref["node"], f"{label}[{index}].node")
        if workflow_name not in workflow_names:
            fail(f"{label}[{index}] references unknown workflow '{workflow_name}'")
        if node_name not in node_names_by_workflow[workflow_name]:
            fail(
                f"{label}[{index}] references unknown node '{node_name}' "
                f"in workflow '{workflow_name}'"
            )
        result.append({"workflow": workflow_name, "node": node_name})
    return result


def validate_target_profile(target_profile: Any) -> dict[str, Any]:
    profile = expect_dict(target_profile, "targetProfile")
    expect_keys(
        profile,
        [
            "id",
            "n8nVersion",
            "timezone",
            "filesBasePath",
            "executionMode",
            "runners",
            "restrictions",
        ],
        "targetProfile",
    )

    if expect_string(profile["id"], "targetProfile.id") != "local-n8n-2.2.6":
        fail("targetProfile.id must be 'local-n8n-2.2.6'")
    if expect_string(profile["n8nVersion"], "targetProfile.n8nVersion") != "2.2.6":
        fail("targetProfile.n8nVersion must be '2.2.6'")
    if expect_string(profile["timezone"], "targetProfile.timezone") != "Europe/Istanbul":
        fail("targetProfile.timezone must be 'Europe/Istanbul'")
    if expect_string(profile["filesBasePath"], "targetProfile.filesBasePath") != "/files":
        fail("targetProfile.filesBasePath must be '/files'")
    if expect_string(profile["executionMode"], "targetProfile.executionMode") != "queue":
        fail("targetProfile.executionMode must be 'queue'")

    runners = expect_dict(profile["runners"], "targetProfile.runners")
    expect_keys(runners, ["enabled", "mode"], "targetProfile.runners")
    if not expect_bool(runners["enabled"], "targetProfile.runners.enabled"):
        fail("targetProfile.runners.enabled must be true")
    if expect_string(runners["mode"], "targetProfile.runners.mode") != "external":
        fail("targetProfile.runners.mode must be 'external'")

    restrictions = expect_dict(profile["restrictions"], "targetProfile.restrictions")
    expect_keys(
        restrictions,
        [
            "bannedNodeTypes",
            "codeNodeAllowedBuiltins",
            "codeNodeAllowedExternalPackages",
        ],
        "targetProfile.restrictions",
    )
    banned = ensure_string_list(
        restrictions["bannedNodeTypes"], "targetProfile.restrictions.bannedNodeTypes"
    )
    if "n8n-nodes-base.executeCommand" not in banned:
        fail("targetProfile.restrictions.bannedNodeTypes must include executeCommand")
    builtins = ensure_string_list(
        restrictions["codeNodeAllowedBuiltins"],
        "targetProfile.restrictions.codeNodeAllowedBuiltins",
    )
    if builtins != ["crypto", "path", "util"]:
        fail("targetProfile.restrictions.codeNodeAllowedBuiltins must be crypto,path,util")
    externals = ensure_string_list(
        restrictions["codeNodeAllowedExternalPackages"],
        "targetProfile.restrictions.codeNodeAllowedExternalPackages",
    )
    if externals:
        fail("targetProfile.restrictions.codeNodeAllowedExternalPackages must be empty")

    return profile


def validate_workspace(workspace: Any) -> dict[str, Any]:
    obj = expect_dict(workspace, "workspace")
    expect_keys(obj, ["name", "summary", "tags", "timezone", "project"], "workspace")
    ensure_name(obj["name"], "workspace.name")
    expect_string(obj["summary"], "workspace.summary")
    ensure_unique(ensure_string_list(obj["tags"], "workspace.tags"), "workspace.tags")
    if expect_string(obj["timezone"], "workspace.timezone") != "Europe/Istanbul":
        fail("workspace.timezone must be 'Europe/Istanbul' for this profile")
    if obj["project"] is not None:
        expect_string(obj["project"], "workspace.project")
    return obj


def validate_credentials(credentials: Any) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    items = expect_list(credentials, "credentials")
    result: list[dict[str, Any]] = []
    by_name: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(items):
        credential = expect_dict(item, f"credentials[{index}]")
        expect_keys(
            credential,
            ["name", "type", "requiredFields", "placeholders", "bindMode", "usedBy", "notes"],
            f"credentials[{index}]",
        )
        name = ensure_name(credential["name"], f"credentials[{index}].name")
        if name in by_name:
            fail(f"credentials contains duplicate name '{name}'")
        expect_string(credential["type"], f"credentials[{index}].type")
        required_fields = ensure_string_list(
            credential["requiredFields"], f"credentials[{index}].requiredFields"
        )
        if not required_fields:
            fail(f"credentials[{index}].requiredFields must not be empty")
        placeholders = expect_dict(credential["placeholders"], f"credentials[{index}].placeholders")
        for field_name in required_fields:
            if field_name not in placeholders:
                fail(
                    f"credentials[{index}].placeholders must include required field '{field_name}'"
                )
            expect_string(
                placeholders[field_name],
                f"credentials[{index}].placeholders.{field_name}",
            )
        bind_mode = expect_string(credential["bindMode"], f"credentials[{index}].bindMode")
        if bind_mode not in ALLOWED_BIND_MODES:
            fail(
                f"credentials[{index}].bindMode must be one of: "
                f"{', '.join(sorted(ALLOWED_BIND_MODES))}"
            )
        expect_list(credential["usedBy"], f"credentials[{index}].usedBy")
        expect_string(credential["notes"], f"credentials[{index}].notes")
        result.append(credential)
        by_name[name] = credential
    return result, by_name


def validate_workflows(
    workflows: Any,
    credential_names: set[str],
) -> tuple[list[dict[str, Any]], dict[str, set[str]]]:
    items = expect_list(workflows, "workflows")
    result: list[dict[str, Any]] = []
    node_names_by_workflow: dict[str, set[str]] = {}
    workflow_names: list[str] = []

    for index, item in enumerate(items):
        workflow = expect_dict(item, f"workflows[{index}]")
        expect_keys(
            workflow,
            [
                "name",
                "purpose",
                "active",
                "settings",
                "manualSteps",
                "validationNotes",
                "nodes",
                "connections",
            ],
            f"workflows[{index}]",
        )
        workflow_name = ensure_name(workflow["name"], f"workflows[{index}].name")
        workflow_names.append(workflow_name)
        expect_string(workflow["purpose"], f"workflows[{index}].purpose")
        expect_bool(workflow["active"], f"workflows[{index}].active")
        expect_dict(workflow["settings"], f"workflows[{index}].settings")
        ensure_string_list(workflow["manualSteps"], f"workflows[{index}].manualSteps")
        ensure_string_list(workflow["validationNotes"], f"workflows[{index}].validationNotes")

        nodes = expect_list(workflow["nodes"], f"workflows[{index}].nodes")
        if not nodes:
            fail(f"workflows[{index}].nodes must not be empty")

        node_names: list[str] = []
        has_trigger = False
        for node_index, node_value in enumerate(nodes):
            node = expect_dict(node_value, f"workflows[{index}].nodes[{node_index}]")
            expect_keys(
                node,
                ["name", "type", "typeVersion", "position", "parameters"],
                f"workflows[{index}].nodes[{node_index}]",
            )
            node_name = ensure_name(node["name"], f"workflows[{index}].nodes[{node_index}].name")
            node_type = expect_string(node["type"], f"workflows[{index}].nodes[{node_index}].type")
            if node_type in BANNED_NODE_TYPES:
                fail(f"workflows[{index}] uses banned node type '{node_type}'")
            node_names.append(node_name)
            expect_type(
                node["typeVersion"],
                (int, float),
                f"workflows[{index}].nodes[{node_index}].typeVersion",
            )
            position = expect_list(node["position"], f"workflows[{index}].nodes[{node_index}].position")
            if len(position) != 2 or not all(isinstance(value, (int, float)) for value in position):
                fail(
                    f"workflows[{index}].nodes[{node_index}].position must be a two-item number array"
                )
            expect_dict(node["parameters"], f"workflows[{index}].nodes[{node_index}].parameters")
            if "disabled" in node:
                expect_bool(node["disabled"], f"workflows[{index}].nodes[{node_index}].disabled")
            if "notes" in node:
                expect_string(node["notes"], f"workflows[{index}].nodes[{node_index}].notes")
            refs = ensure_string_list(
                node.get("credentialRefs", []),
                f"workflows[{index}].nodes[{node_index}].credentialRefs",
            )
            for ref in refs:
                if ref not in credential_names:
                    fail(
                        f"workflows[{index}].nodes[{node_index}] references unknown credential '{ref}'"
                    )
            if is_trigger_type(node_type):
                has_trigger = True

        ensure_unique(node_names, f"workflows[{index}].nodes.name")
        if not has_trigger:
            fail(f"workflows[{index}] must include at least one trigger node")
        node_names_by_workflow[workflow_name] = set(node_names)

        connections = expect_list(workflow["connections"], f"workflows[{index}].connections")
        for edge_index, edge_value in enumerate(connections):
            edge = expect_dict(edge_value, f"workflows[{index}].connections[{edge_index}]")
            expect_keys(edge, ["from", "to"], f"workflows[{index}].connections[{edge_index}]")
            for side in ("from", "to"):
                side_value = expect_dict(
                    edge[side], f"workflows[{index}].connections[{edge_index}].{side}"
                )
                required = ["node", "index", "output" if side == "from" else "input"]
                expect_keys(
                    side_value,
                    required,
                    f"workflows[{index}].connections[{edge_index}].{side}",
                )
                side_node = ensure_name(
                    side_value["node"],
                    f"workflows[{index}].connections[{edge_index}].{side}.node",
                )
                if side_node not in node_names_by_workflow[workflow_name]:
                    fail(
                        f"workflows[{index}].connections[{edge_index}] references unknown node "
                        f"'{side_node}'"
                    )
                if side == "from":
                    expect_string(
                        side_value["output"],
                        f"workflows[{index}].connections[{edge_index}].from.output",
                    )
                else:
                    expect_string(
                        side_value["input"],
                        f"workflows[{index}].connections[{edge_index}].to.input",
                    )
                if not isinstance(side_value["index"], int) or side_value["index"] < 0:
                    fail(
                        f"workflows[{index}].connections[{edge_index}].{side}.index "
                        "must be a non-negative integer"
                    )

        result.append(workflow)

    ensure_unique(workflow_names, "workflows.name")
    return result, node_names_by_workflow


def validate_files(
    files: Any,
    *,
    workflow_names: set[str],
    node_names_by_workflow: dict[str, set[str]],
) -> list[dict[str, Any]]:
    items = expect_list(files, "files")
    result: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for index, item in enumerate(items):
        file_entry = expect_dict(item, f"files[{index}]")
        expect_keys(
            file_entry,
            ["path", "format", "content", "producedBy", "consumedBy", "notes"],
            f"files[{index}]",
        )
        path_text = expect_string(file_entry["path"], f"files[{index}].path")
        if path_text in seen_paths:
            fail(f"files contains duplicate path '{path_text}'")
        if not is_safe_files_path(path_text):
            fail(f"files[{index}].path must stay under /files and avoid path traversal")
        seen_paths.add(path_text)
        expect_string(file_entry["format"], f"files[{index}].format")
        content = expect_dict(file_entry["content"], f"files[{index}].content")
        expect_keys(content, ["mode"], f"files[{index}].content")
        mode = expect_string(content["mode"], f"files[{index}].content.mode")
        if mode not in ALLOWED_CONTENT_MODES:
            fail(
                f"files[{index}].content.mode must be one of: "
                f"{', '.join(sorted(ALLOWED_CONTENT_MODES))}"
            )
        if mode == "placeholder":
            expect_string(content.get("description"), f"files[{index}].content.description")
        elif "value" not in content:
            fail(f"files[{index}].content.value is required for mode '{mode}'")
        ensure_ref_list(
            file_entry["producedBy"],
            f"files[{index}].producedBy",
            workflow_names=workflow_names,
            node_names_by_workflow=node_names_by_workflow,
        )
        ensure_ref_list(
            file_entry["consumedBy"],
            f"files[{index}].consumedBy",
            workflow_names=workflow_names,
            node_names_by_workflow=node_names_by_workflow,
        )
        expect_string(file_entry["notes"], f"files[{index}].notes")
        result.append(file_entry)
    return result


def validate_import_plan(
    import_plan: Any,
    *,
    credential_names: set[str],
    workflow_names: set[str],
) -> dict[str, Any]:
    plan = expect_dict(import_plan, "importPlan")
    expect_keys(
        plan,
        ["credentialCreationOrder", "workflowImportOrder", "publishSteps", "postImportChecks"],
        "importPlan",
    )
    credential_order = ensure_string_list(
        plan["credentialCreationOrder"], "importPlan.credentialCreationOrder"
    )
    workflow_order = ensure_string_list(
        plan["workflowImportOrder"], "importPlan.workflowImportOrder"
    )
    if set(credential_order) != credential_names:
        fail("importPlan.credentialCreationOrder must include every credential exactly once")
    if len(credential_order) != len(credential_names):
        fail("importPlan.credentialCreationOrder contains duplicates")
    if set(workflow_order) != workflow_names:
        fail("importPlan.workflowImportOrder must include every workflow exactly once")
    if len(workflow_order) != len(workflow_names):
        fail("importPlan.workflowImportOrder contains duplicates")
    ensure_string_list(plan["publishSteps"], "importPlan.publishSteps")
    ensure_string_list(plan["postImportChecks"], "importPlan.postImportChecks")
    return plan


def validate_usage_references(
    credentials: list[dict[str, Any]],
    *,
    workflow_names: set[str],
    node_names_by_workflow: dict[str, set[str]],
) -> None:
    for index, credential in enumerate(credentials):
        ensure_ref_list(
            credential["usedBy"],
            f"credentials[{index}].usedBy",
            workflow_names=workflow_names,
            node_names_by_workflow=node_names_by_workflow,
        )


def validate_spec_data(spec: Any) -> dict[str, Any]:
    obj = expect_dict(spec, "root")
    expect_keys(obj, EXPECTED_TOP_LEVEL_KEYS, "root")
    if list(obj.keys()) != EXPECTED_TOP_LEVEL_KEYS:
        fail("top-level keys must appear in this order: " + ", ".join(EXPECTED_TOP_LEVEL_KEYS))
    if expect_string(obj["specVersion"], "specVersion") != SPEC_VERSION:
        fail(f"specVersion must be '{SPEC_VERSION}'")

    validate_target_profile(obj["targetProfile"])
    validate_workspace(obj["workspace"])
    credentials, credentials_by_name = validate_credentials(obj["credentials"])
    workflows, node_names_by_workflow = validate_workflows(
        obj["workflows"], set(credentials_by_name.keys())
    )
    workflow_names = {workflow["name"] for workflow in workflows}
    validate_usage_references(
        credentials,
        workflow_names=workflow_names,
        node_names_by_workflow=node_names_by_workflow,
    )
    validate_files(
        obj["files"],
        workflow_names=workflow_names,
        node_names_by_workflow=node_names_by_workflow,
    )
    validate_import_plan(
        obj["importPlan"],
        credential_names=set(credentials_by_name.keys()),
        workflow_names=workflow_names,
    )
    ensure_string_list(obj["assumptions"], "assumptions")
    return obj


def validate_spec_file(path: str) -> dict[str, Any]:
    try:
        data = load_json(path)
    except FileNotFoundError:
        fail(f"Spec file not found: {path}")
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON: {exc}")
    return validate_spec_data(data)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: validate_workspace_spec.py <spec.json>")
        return 1

    try:
        spec = validate_spec_file(argv[1])
    except ValidationError as exc:
        print(f"[ERROR] {exc}")
        return 1

    print(
        f"[OK] Valid workspace spec: {spec['workspace']['name']} "
        f"({len(spec['workflows'])} workflow(s), {len(spec['credentials'])} credential(s))"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
