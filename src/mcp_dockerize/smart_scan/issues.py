"""Issue types, severities, and result containers for Smart-Scan analysis."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class IssueType(Enum):
    missing_package_lock = "missing_package_lock"
    runtime_version_mismatch = "runtime_version_mismatch"
    path_has_spaces = "path_has_spaces"
    missing_env_var = "missing_env_var"
    missing_entry_point = "missing_entry_point"
    invalid_json_manifest = "invalid_json_manifest"
    volume_path_not_found = "volume_path_not_found"
    unknown_runtime = "unknown_runtime"


class Severity(Enum):
    blocking = "blocking"
    warning = "warning"
    info = "info"


@dataclass
class Issue:
    issue_type: IssueType
    severity: Severity
    description: str
    auto_fixable: bool
    fix_instruction: str
    affected_path: str = ""


@dataclass
class Fix:
    issue_type: IssueType
    description: str
    files_modified: List[str] = field(default_factory=list)
    success: bool = True
    error: str = ""


@dataclass
class SmartScanResult:
    server_path: str
    runtime: str
    runtime_version: str
    entry_point: str
    package_manager: str
    env_vars: List[str]
    data_volumes: List[str]
    issues: List[Issue]
    deployment_pattern: str = "volume_mounted"
