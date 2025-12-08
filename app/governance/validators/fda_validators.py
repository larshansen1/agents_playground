"""
FDA API Guidelines Ruleset Validators

Implements the validation logic for each check defined in fda_ruleset_v1.json.
These validators operate on parsed OpenAPI specs (as Python dicts).
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class CheckStatus(Enum):
    COMPLIANT = "COMPLIANT"
    VIOLATION = "VIOLATION"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNABLE_TO_DETERMINE = "UNABLE_TO_DETERMINE"


class Severity(Enum):
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    INFO = "INFO"


@dataclass
class CheckResult:
    """Result of a single check execution."""

    check_id: str
    status: CheckStatus
    severity: Severity
    evidence: str
    spec_paths_checked: list[str]
    details: dict[str, Any] | None = None


@dataclass
class ValidationContext:
    """Context passed to validators."""

    spec: dict[str, Any]
    check_config: dict[str, Any]


# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------


def get_nested(d: dict, path: str, default=None) -> Any:
    """Get nested dict value using dot notation. Handles [*] for arrays."""
    keys = path.replace("$.", "").split(".")
    current = d

    for key in keys:
        if current is None:
            return default
        if key == "[*]" or key.endswith("[*]"):
            # Array wildcard - return list of all values
            base_key = key.replace("[*]", "")
            if base_key and isinstance(current, dict):
                current = current.get(base_key, [])
            if isinstance(current, list):
                return current
            return default
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default

    return current


def get_all_operations(spec: dict) -> list[tuple[str, str, dict]]:
    """Extract all operations from spec as (path, method, operation_obj) tuples."""
    operations = []
    paths = spec.get("paths", {})
    http_methods = {"get", "post", "put", "patch", "delete", "head", "options"}

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method in http_methods:
            if method in path_item:
                operations.append((path, method, path_item[method]))

    return operations


# -----------------------------------------------------------------------------
# Validators
# -----------------------------------------------------------------------------


def validate_exists(ctx: ValidationContext) -> CheckResult:
    """Check that a path exists in the spec."""
    check = ctx.check_config
    path = check["spec_path"]
    value = get_nested(ctx.spec, path)

    exists = value is not None
    status = CheckStatus.COMPLIANT if exists else CheckStatus.VIOLATION
    evidence = check["evidence_template"].format(
        status="present" if exists else "missing", value=value
    )

    return CheckResult(
        check_id=check["check_id"],
        status=status,
        severity=Severity[check["severity"]],
        evidence=evidence,
        spec_paths_checked=[path],
    )


def validate_exists_and_non_empty(ctx: ValidationContext) -> CheckResult:
    """Check that a path exists and has non-empty value."""
    check = ctx.check_config
    path = check["spec_path"]
    value = get_nested(ctx.spec, path)

    exists_and_valid = value is not None and str(value).strip() != ""
    status = CheckStatus.COMPLIANT if exists_and_valid else CheckStatus.VIOLATION
    evidence = check["evidence_template"].format(
        status="present and non-empty" if exists_and_valid else "missing or empty", value=value
    )

    return CheckResult(
        check_id=check["check_id"],
        status=status,
        severity=Severity[check["severity"]],
        evidence=evidence,
        spec_paths_checked=[path],
    )


def validate_array_min_length(ctx: ValidationContext) -> CheckResult:
    """Check that an array has minimum number of elements."""
    check = ctx.check_config
    path = check["spec_path"]
    min_length = check["validation"]["min"]
    value = get_nested(ctx.spec, path)

    if isinstance(value, list):
        valid = len(value) >= min_length
        count = len(value)
    elif isinstance(value, dict):
        # Handle case where we're checking if object has entries
        valid = len(value) >= min_length
        count = len(value)
    else:
        valid = False
        count = 0

    status = CheckStatus.COMPLIANT if valid else CheckStatus.VIOLATION
    evidence = check["evidence_template"].format(
        status="found" if valid else "insufficient", count=count
    )

    return CheckResult(
        check_id=check["check_id"],
        status=status,
        severity=Severity[check["severity"]],
        evidence=evidence,
        spec_paths_checked=[path],
        details={"count": count, "required": min_length},
    )


def validate_regex(ctx: ValidationContext) -> CheckResult:
    """Check that a value matches a regex pattern."""
    check = ctx.check_config
    path = check["spec_path"]
    pattern = check["validation"]["pattern"]
    value = get_nested(ctx.spec, path)

    if value is None:
        status = CheckStatus.VIOLATION
        evidence = check["evidence_template"].format(status="missing", value="(not found)")
    else:
        matches = bool(re.match(pattern, str(value)))
        status = CheckStatus.COMPLIANT if matches else CheckStatus.VIOLATION
        evidence = check["evidence_template"].format(
            status="follows" if matches else "does not follow", value=value
        )

    return CheckResult(
        check_id=check["check_id"],
        status=status,
        severity=Severity[check["severity"]],
        evidence=evidence,
        spec_paths_checked=[path],
        details={"value": value, "pattern": pattern},
    )


def validate_object_min_keys(ctx: ValidationContext) -> CheckResult:
    """Check that an object has minimum number of keys."""
    check = ctx.check_config
    path = check["spec_path"]
    min_keys = check["validation"]["min"]
    value = get_nested(ctx.spec, path)

    if isinstance(value, dict):
        count = len(value)
        valid = count >= min_keys
    else:
        count = 0
        valid = False

    status = CheckStatus.COMPLIANT if valid else CheckStatus.VIOLATION
    evidence = check["evidence_template"].format(
        status="defined" if valid else "missing or empty", count=count
    )

    return CheckResult(
        check_id=check["check_id"],
        status=status,
        severity=Severity[check["severity"]],
        evidence=evidence,
        spec_paths_checked=[path],
        details={"count": count, "required": min_keys},
    )


# -----------------------------------------------------------------------------
# Custom validators
# -----------------------------------------------------------------------------


def validate_has_error_responses(ctx: ValidationContext) -> CheckResult:
    """Check that operations define error responses (4xx or 5xx)."""
    check = ctx.check_config
    operations = get_all_operations(ctx.spec)

    if not operations:
        return CheckResult(
            check_id=check["check_id"],
            status=CheckStatus.NOT_APPLICABLE,
            severity=Severity[check["severity"]],
            evidence="No operations defined",
            spec_paths_checked=["$.paths"],
        )

    missing_error_responses = []
    for path, method, op in operations:
        responses = op.get("responses", {})
        has_error = any(
            str(code).startswith("4") or str(code).startswith("5") for code in responses
        )
        if not has_error:
            missing_error_responses.append(f"{method.upper()} {path}")

    if missing_error_responses:
        status = CheckStatus.VIOLATION
        evidence = check["evidence_template"].format(
            status=f"missing for {len(missing_error_responses)} operation(s)"
        )
    else:
        status = CheckStatus.COMPLIANT
        evidence = check["evidence_template"].format(status="present")

    return CheckResult(
        check_id=check["check_id"],
        status=status,
        severity=Severity[check["severity"]],
        evidence=evidence,
        spec_paths_checked=["$.paths[*][*].responses"],
        details={"missing": missing_error_responses[:5]},  # Limit details
    )


def validate_has_health_endpoint(ctx: ValidationContext) -> CheckResult:
    """Check for presence of health/monitoring endpoint."""
    check = ctx.check_config
    patterns = check["validation"]["patterns"]
    paths = ctx.spec.get("paths", {})

    found_health = None
    for path in paths:
        path_lower = path.lower()
        for pattern in patterns:
            if pattern in path_lower:
                found_health = path
                break
        if found_health:
            break

    if found_health:
        status = CheckStatus.COMPLIANT
        evidence = check["evidence_template"].format(status=f"found at {found_health}")
    else:
        status = CheckStatus.VIOLATION
        evidence = check["evidence_template"].format(status="not found")

    return CheckResult(
        check_id=check["check_id"],
        status=status,
        severity=Severity[check["severity"]],
        evidence=evidence,
        spec_paths_checked=["$.paths"],
        details={"found_endpoint": found_health, "patterns_checked": patterns},
    )


def validate_has_token_auth(ctx: ValidationContext) -> CheckResult:
    """Check for token-based authentication scheme."""
    check = ctx.check_config
    check["validation"]["allowed_types"]
    schemes = ctx.spec.get("components", {}).get("securitySchemes", {})

    if not schemes:
        return CheckResult(
            check_id=check["check_id"],
            status=CheckStatus.VIOLATION,
            severity=Severity[check["severity"]],
            evidence=check["evidence_template"].format(status="not configured"),
            spec_paths_checked=["$.components.securitySchemes"],
        )

    found_token_auth = []
    for name, scheme in schemes.items():
        scheme_type = scheme.get("type", "")
        if scheme_type in ["oauth2", "openIdConnect"]:
            found_token_auth.append(f"{name} ({scheme_type})")
        elif scheme_type == "http" and scheme.get("scheme", "").lower() == "bearer":
            found_token_auth.append(f"{name} (bearer)")
        elif scheme_type == "apiKey":
            found_token_auth.append(f"{name} (apiKey)")

    if found_token_auth:
        status = CheckStatus.COMPLIANT
        evidence = check["evidence_template"].format(
            status=f"configured: {', '.join(found_token_auth)}"
        )
    else:
        status = CheckStatus.VIOLATION
        evidence = check["evidence_template"].format(status="not using token-based auth")

    return CheckResult(
        check_id=check["check_id"],
        status=status,
        severity=Severity[check["severity"]],
        evidence=evidence,
        spec_paths_checked=["$.components.securitySchemes"],
        details={"found_schemes": found_token_auth},
    )


def validate_no_verbs_in_paths(ctx: ValidationContext) -> CheckResult:
    """Check that path segments don't contain verbs."""
    check = ctx.check_config
    verb_patterns = check["validation"]["verb_patterns"]
    paths = ctx.spec.get("paths", {})

    violations = []
    for path in paths:
        segments = path.lower().split("/")
        for segment in segments:
            # Skip path parameters
            if segment.startswith("{"):
                continue
            for verb in verb_patterns:
                if verb in segment:
                    violations.append(f"{path} (contains '{verb}')")
                    break

    if violations:
        status = CheckStatus.VIOLATION
        details_str = f"Found verbs in: {', '.join(violations[:3])}"
        if len(violations) > 3:
            details_str += f" and {len(violations) - 3} more"
        evidence = check["evidence_template"].format(status="has issues", details=details_str)
    else:
        status = CheckStatus.COMPLIANT
        evidence = check["evidence_template"].format(status="follows REST conventions", details="")

    return CheckResult(
        check_id=check["check_id"],
        status=status,
        severity=Severity[check["severity"]],
        evidence=evidence,
        spec_paths_checked=["$.paths"],
        details={"violations": violations[:5]},
    )


def validate_no_sensitive_path_params(ctx: ValidationContext) -> CheckResult:
    """Check path parameters don't contain sensitive data identifiers."""
    check = ctx.check_config
    sensitive_patterns = check["validation"]["sensitive_patterns"]
    paths = ctx.spec.get("paths", {})

    violations = []
    for path in paths:
        path_lower = path.lower()
        for pattern in sensitive_patterns:
            if pattern in path_lower:
                violations.append(f"{path} (contains '{pattern}')")

    if violations:
        status = CheckStatus.VIOLATION
        details_str = f"Sensitive patterns in: {', '.join(violations[:3])}"
        evidence = check["evidence_template"].format(
            status="has security concerns", details=details_str
        )
    else:
        status = CheckStatus.COMPLIANT
        evidence = check["evidence_template"].format(
            status="passes", details="No sensitive patterns found"
        )

    return CheckResult(
        check_id=check["check_id"],
        status=status,
        severity=Severity[check["severity"]],
        evidence=evidence,
        spec_paths_checked=["$.paths"],
        details={"violations": violations},
    )


def validate_urls_use_https(ctx: ValidationContext) -> CheckResult:
    """Check server URLs use HTTPS scheme."""
    check = ctx.check_config
    servers = ctx.spec.get("servers", [])

    if not servers:
        return CheckResult(
            check_id=check["check_id"],
            status=CheckStatus.VIOLATION,
            severity=Severity[check["severity"]],
            evidence=check["evidence_template"].format(status="no servers defined", details=""),
            spec_paths_checked=["$.servers"],
        )

    insecure = []
    for server in servers:
        url = server.get("url", "")
        # Allow localhost for development
        if url.startswith("http://") and "localhost" not in url and "127.0.0.1" not in url:
            insecure.append(url)

    if insecure:
        status = CheckStatus.VIOLATION
        details_str = f"Insecure URLs: {', '.join(insecure)}"
        evidence = check["evidence_template"].format(
            status="has insecure URLs", details=details_str
        )
    else:
        status = CheckStatus.COMPLIANT
        evidence = check["evidence_template"].format(status="all URLs secure", details="")

    return CheckResult(
        check_id=check["check_id"],
        status=status,
        severity=Severity[check["severity"]],
        evidence=evidence,
        spec_paths_checked=["$.servers[*].url"],
        details={"insecure_urls": insecure},
    )


def validate_all_operations_have_operation_id(ctx: ValidationContext) -> CheckResult:
    """Check all operations define operationId."""
    check = ctx.check_config
    operations = get_all_operations(ctx.spec)

    if not operations:
        return CheckResult(
            check_id=check["check_id"],
            status=CheckStatus.NOT_APPLICABLE,
            severity=Severity[check["severity"]],
            evidence="No operations defined",
            spec_paths_checked=["$.paths"],
        )

    missing = []
    for path, method, op in operations:
        if not op.get("operationId"):
            missing.append(f"{method.upper()} {path}")

    if missing:
        status = CheckStatus.VIOLATION
        details_str = f"Missing for: {', '.join(missing[:3])}"
        if len(missing) > 3:
            details_str += f" and {len(missing) - 3} more"
        evidence = check["evidence_template"].format(status="missing", details=details_str)
    else:
        status = CheckStatus.COMPLIANT
        evidence = check["evidence_template"].format(
            status="present for all operations", details=""
        )

    return CheckResult(
        check_id=check["check_id"],
        status=status,
        severity=Severity[check["severity"]],
        evidence=evidence,
        spec_paths_checked=["$.paths[*][*].operationId"],
        details={"missing": missing[:5], "total_operations": len(operations)},
    )


def validate_all_operations_have_descriptions(ctx: ValidationContext) -> CheckResult:
    """Check all operations have descriptions."""
    check = ctx.check_config
    operations = get_all_operations(ctx.spec)

    if not operations:
        return CheckResult(
            check_id=check["check_id"],
            status=CheckStatus.NOT_APPLICABLE,
            severity=Severity[check["severity"]],
            evidence="No operations defined",
            spec_paths_checked=["$.paths"],
        )

    missing = []
    for path, method, op in operations:
        if not op.get("description") and not op.get("summary"):
            missing.append(f"{method.upper()} {path}")

    if missing:
        status = CheckStatus.VIOLATION
        details_str = f"Missing for: {', '.join(missing[:3])}"
        if len(missing) > 3:
            details_str += f" and {len(missing) - 3} more"
        evidence = check["evidence_template"].format(status="missing", details=details_str)
    else:
        status = CheckStatus.COMPLIANT
        evidence = check["evidence_template"].format(
            status="present for all operations", details=""
        )

    return CheckResult(
        check_id=check["check_id"],
        status=status,
        severity=Severity[check["severity"]],
        evidence=evidence,
        spec_paths_checked=["$.paths[*][*].description"],
        details={"missing": missing[:5], "total_operations": len(operations)},
    )


def validate_operation_ids_unique(ctx: ValidationContext) -> CheckResult:
    """Check operationIds are unique across spec."""
    check = ctx.check_config
    operations = get_all_operations(ctx.spec)
    operation_ids: dict[str, str] = {}  # operation_id -> "METHOD /path"
    duplicates = []

    for path, method, op in operations:
        op_id = op.get("operationId")
        if op_id:
            if op_id in operation_ids:
                duplicates.append(
                    f"{op_id} (used by {operation_ids[op_id]} and {method.upper()} {path})"
                )
            else:
                operation_ids[op_id] = f"{method.upper()} {path}"

    if duplicates:
        status = CheckStatus.VIOLATION
        details_str = f"Duplicates: {', '.join(duplicates[:3])}"
        evidence = check["evidence_template"].format(status="has duplicates", details=details_str)
    else:
        status = CheckStatus.COMPLIANT
        evidence = check["evidence_template"].format(status="all unique", details="")

    return CheckResult(
        check_id=check["check_id"],
        status=status,
        severity=Severity[check["severity"]],
        evidence=evidence,
        spec_paths_checked=["$.paths[*][*].operationId"],
        details={"duplicates": duplicates},
    )


def validate_supports_json_content_type(ctx: ValidationContext) -> CheckResult:
    """Check responses support application/json."""
    check = ctx.check_config
    operations = get_all_operations(ctx.spec)

    if not operations:
        return CheckResult(
            check_id=check["check_id"],
            status=CheckStatus.NOT_APPLICABLE,
            severity=Severity[check["severity"]],
            evidence="No operations defined",
            spec_paths_checked=["$.paths"],
        )

    missing_json = []
    for path, method, op in operations:
        responses = op.get("responses", {})
        has_json = False
        for _code, response in responses.items():
            content = response.get("content", {})
            if "application/json" in content:
                has_json = True
                break
        if not has_json and responses:
            missing_json.append(f"{method.upper()} {path}")

    # Only flag if more than half of operations lack JSON
    if len(missing_json) > len(operations) / 2:
        status = CheckStatus.VIOLATION
        evidence = check["evidence_template"].format(
            status=f"missing for {len(missing_json)} operations"
        )
    else:
        status = CheckStatus.COMPLIANT
        evidence = check["evidence_template"].format(status="supported")

    return CheckResult(
        check_id=check["check_id"],
        status=status,
        severity=Severity[check["severity"]],
        evidence=evidence,
        spec_paths_checked=["$.paths[*][*].responses[*].content"],
        details={"missing_json": missing_json[:5]},
    )


def validate_success_responses_have_schemas(ctx: ValidationContext) -> CheckResult:
    """Check 2xx responses define schemas."""
    check = ctx.check_config
    operations = get_all_operations(ctx.spec)

    if not operations:
        return CheckResult(
            check_id=check["check_id"],
            status=CheckStatus.NOT_APPLICABLE,
            severity=Severity[check["severity"]],
            evidence="No operations defined",
            spec_paths_checked=["$.paths"],
        )

    missing_schema = []
    for path, method, op in operations:
        responses = op.get("responses", {})
        for code, response in responses.items():
            if str(code).startswith("2") and code != "204":  # 204 No Content doesn't need schema
                content = response.get("content", {})
                has_schema = any("schema" in media_type for media_type in content.values())
                if content and not has_schema:
                    missing_schema.append(f"{method.upper()} {path} ({code})")

    if missing_schema:
        status = CheckStatus.VIOLATION
        details_str = f"Missing for: {', '.join(missing_schema[:3])}"
        evidence = check["evidence_template"].format(status="incomplete", details=details_str)
    else:
        status = CheckStatus.COMPLIANT
        evidence = check["evidence_template"].format(status="complete", details="")

    return CheckResult(
        check_id=check["check_id"],
        status=status,
        severity=Severity[check["severity"]],
        evidence=evidence,
        spec_paths_checked=["$.paths[*][*].responses.2*.content[*].schema"],
        details={"missing_schema": missing_schema[:5]},
    )


def validate_parameters_have_descriptions(ctx: ValidationContext) -> CheckResult:
    """Check parameters have descriptions."""
    check = ctx.check_config
    operations = get_all_operations(ctx.spec)

    missing_desc = []
    total_params = 0

    for path, method, op in operations:
        params = op.get("parameters", [])
        for param in params:
            total_params += 1
            if not param.get("description"):
                param_name = param.get("name", "unknown")
                missing_desc.append(f"{param_name} in {method.upper()} {path}")

    if not total_params:
        return CheckResult(
            check_id=check["check_id"],
            status=CheckStatus.NOT_APPLICABLE,
            severity=Severity[check["severity"]],
            evidence="No parameters defined",
            spec_paths_checked=["$.paths[*][*].parameters"],
        )

    # Minor issue if some are missing, not a hard failure
    if missing_desc:
        status = CheckStatus.VIOLATION
        details_str = f"{len(missing_desc)} of {total_params} parameters lack descriptions"
        evidence = check["evidence_template"].format(status="incomplete", details=details_str)
    else:
        status = CheckStatus.COMPLIANT
        evidence = check["evidence_template"].format(status="complete", details="")

    return CheckResult(
        check_id=check["check_id"],
        status=status,
        severity=Severity[check["severity"]],
        evidence=evidence,
        spec_paths_checked=["$.paths[*][*].parameters[*].description"],
        details={"missing": missing_desc[:5], "total": total_params},
    )


# -----------------------------------------------------------------------------
# Validator registry
# -----------------------------------------------------------------------------

VALIDATORS = {
    "exists": validate_exists,
    "exists_and_non_empty": validate_exists_and_non_empty,
    "array_min_length": validate_array_min_length,
    "regex": validate_regex,
    "object_min_keys": validate_object_min_keys,
    # Custom validators
    "has_error_responses": validate_has_error_responses,
    "error_responses_have_descriptions": validate_has_error_responses,  # Same logic
    "has_health_endpoint": validate_has_health_endpoint,
    "has_token_auth": validate_has_token_auth,
    "no_verbs_in_paths": validate_no_verbs_in_paths,
    "no_sensitive_path_params": validate_no_sensitive_path_params,
    "uses_standard_search_params": lambda ctx: CheckResult(  # Placeholder
        check_id=ctx.check_config["check_id"],
        status=CheckStatus.NOT_APPLICABLE,
        severity=Severity.INFO,
        evidence="Search parameter check not yet implemented",
        spec_paths_checked=[],
    ),
    "collection_endpoints_have_pagination": lambda ctx: CheckResult(  # Placeholder
        check_id=ctx.check_config["check_id"],
        status=CheckStatus.NOT_APPLICABLE,
        severity=Severity.INFO,
        evidence="Pagination check not yet implemented",
        spec_paths_checked=[],
    ),
    "supports_json_content_type": validate_supports_json_content_type,
    "success_responses_have_schemas": validate_success_responses_have_schemas,
    "request_bodies_have_schemas": lambda ctx: CheckResult(  # Placeholder
        check_id=ctx.check_config["check_id"],
        status=CheckStatus.NOT_APPLICABLE,
        severity=Severity.INFO,
        evidence="Request body schema check not yet implemented",
        spec_paths_checked=[],
    ),
    "uses_standard_http_methods": lambda ctx: CheckResult(  # Always passes if parsed
        check_id=ctx.check_config["check_id"],
        status=CheckStatus.COMPLIANT,
        severity=Severity[ctx.check_config["severity"]],
        evidence="HTTP method usage is valid (spec parsed successfully)",
        spec_paths_checked=["$.paths"],
    ),
    "get_has_no_request_body": lambda ctx: CheckResult(  # Placeholder
        check_id=ctx.check_config["check_id"],
        status=CheckStatus.NOT_APPLICABLE,
        severity=Severity.INFO,
        evidence="GET request body check not yet implemented",
        spec_paths_checked=[],
    ),
    "urls_use_https": validate_urls_use_https,
    "all_operations_have_operation_id": validate_all_operations_have_operation_id,
    "all_operations_have_descriptions": validate_all_operations_have_descriptions,
    "operation_ids_unique": validate_operation_ids_unique,
    "parameters_have_descriptions": validate_parameters_have_descriptions,
}


def run_check(spec: dict, check_config: dict) -> CheckResult:
    """Run a single check against a spec."""
    validation = check_config.get("validation", {})
    validator_type = validation.get("type", "exists")

    # For custom validators, use the validator name
    if validator_type == "custom":
        validator_type = validation.get("validator", "exists")

    validator = VALIDATORS.get(validator_type)
    if not validator:
        return CheckResult(
            check_id=check_config["check_id"],
            status=CheckStatus.UNABLE_TO_DETERMINE,
            severity=Severity[check_config.get("severity", "INFO")],
            evidence=f"Unknown validator type: {validator_type}",
            spec_paths_checked=[],
        )

    ctx = ValidationContext(spec=spec, check_config=check_config)
    return validator(ctx)
