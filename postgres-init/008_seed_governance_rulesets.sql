-- Seed governance rulesets (generic migration, framework-agnostic)
-- Initial data: FDA ruleset v1.0

-- Note: In production, this JSONB would be loaded from backlog/API_TOOL/fda_ruleset_v1.json
-- For this migration, we create a simplified version with MVP rules only

INSERT INTO governance_rulesets (
    ruleset_id,
    framework,
    version,
    effective_date,
    rules,
    checksum,
    metadata
)
VALUES (
    'FDA-DK-2024-1.0',
    'FDA',
    '1.0.0',
    '2024-01-01',
    '{
        "ruleset_name": "Danish FDA API Guidelines (Retningslinjer for webservices)",
        "source_url": "https://arkitektur.digst.dk/metoder/begrebs-og-datametoder/retningslinjer-webservices",
        "description": "Fællesoffentlige retningslinjer for REST webservices i den offentlige sektor",
        "categories": [
            {"id": "documentation", "name_en": "Service Documentation", "name_da": "Servicedokumentation"},
            {"id": "versioning", "name_en": "Service Versioning", "name_da": "Serviceversionering"},
            {"id": "resource_modeling", "name_en": "REST Resource Modeling", "name_da": "Modellering af REST webservices"},
            {"id": "security", "name_en": "Security Requirements", "name_da": "Sikkerhedskrav"},
            {"id": "data_representation", "name_en": "Data Representation", "name_da": "Datarepræsentation"}
        ],
        "rules": [
            {
                "id": "R06",
                "name_en": "Document according to framework",
                "name_da": "Dokumentér udstillede webservices i overensstemmelse med den fællesoffentlige dokumentationsramme",
                "category": "documentation",
                "priority": "MUST",
                "severity_default": "CRITICAL",
                "description": "REST webservices shall use OpenAPI specification with required metadata elements per Bilag 1",
                "check_type": "structural",
                "automatable": true
            },
            {
                "id": "R11",
                "name_en": "Use semantic versioning",
                "name_da": "Anvend semantisk versionering af webservices",
                "category": "versioning",
                "priority": "MUST",
                "severity_default": "MAJOR",
                "description": "Use semantic versioning (Major.Minor.Patch). Major = breaking change, Minor = backward compatible additions",
                "check_type": "structural",
                "automatable": true
            },
            {
                "id": "R23",
                "name_en": "Token-based security",
                "name_da": "Webservices skal have tokenbaseret sikkerhed",
                "category": "security",
                "priority": "MUST",
                "severity_default": "CRITICAL",
                "description": "Use federated token-based authentication. No point-to-point certificate auth (except TLS).",
                "check_type": "structural",
                "automatable": true
            },
            {
                "id": "R24",
                "name_en": "Expose as REST resources",
                "name_da": "Udstil webservices som REST ressourcer",
                "category": "resource_modeling",
                "priority": "MUST",
                "severity_default": "MAJOR",
                "description": "Follow REST architectural style for CRUD operations on resources",
                "check_type": "structural",
                "automatable": true
            },
            {
                "id": "R37",
                "name_en": "Use HTTP",
                "name_da": "Anvend HTTP som fællesoffentlig REST kommunikationsprotokol",
                "category": "data_representation",
                "priority": "MUST",
                "severity_default": "MAJOR",
                "description": "HTTP is the standard protocol. Use proper HTTP methods and status codes.",
                "check_type": "structural",
                "automatable": true
            },
            {
                "id": "R39",
                "name_en": "Secure HTTP",
                "name_da": "Anvend HTTP sikkert til REST ressourcer",
                "category": "security",
                "priority": "MUST",
                "severity_default": "CRITICAL",
                "description": "Require HTTPS (TLS 1.1+). Reject unsecure HTTP with error (no redirect).",
                "check_type": "structural",
                "automatable": true
            },
            {
                "id": "BILAG1-OPS",
                "name_en": "Operation documentation",
                "name_da": "Operationsdokumentation",
                "category": "documentation",
                "priority": "MUST",
                "severity_default": "MAJOR",
                "description": "Each operation must have operationId and description per Bilag 1",
                "check_type": "structural",
                "automatable": true
            }
        ],
        "severity_definitions": {
            "CRITICAL": {"description": "Must be fixed before production deployment. Blocks compliance.", "weight": 4},
            "MAJOR": {"description": "Should be fixed. Significant deviation from guidelines.", "weight": 3},
            "MINOR": {"description": "Recommended improvement. Does not block deployment.", "weight": 2},
            "INFO": {"description": "Informational finding. Best practice suggestion.", "weight": 1}
        }
    }'::jsonb,
    'placeholder_checksum_replace_with_sha256',
    '{
        "created_by": "FDA API Governance Review System",
        "source_documents": [
            "Retningslinjer for webservices (hovedddokument)",
            "Bilag 1 - Dokumentation for REST webservices"
        ],
        "total_rules": 7,
        "notes": "MVP ruleset with 7 structural rules. Full ruleset with 32 checks available in backlog/API_TOOL/fda_ruleset_v1.json"
    }'::jsonb
)
ON CONFLICT (ruleset_id) DO NOTHING;

-- Verify
SELECT ruleset_id, framework, version, jsonb_array_length(rules->'rules') as rule_count
FROM governance_rulesets
WHERE ruleset_id = 'FDA-DK-2024-1.0';
