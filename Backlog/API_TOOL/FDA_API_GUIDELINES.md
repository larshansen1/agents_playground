# Danish FDA API Guidelines (Retningslinjer for webservices)

Source: https://arkitektur.digst.dk/metoder/begrebs-og-datametoder/retningslinjer-webservices

## Overview

These guidelines are published by Digitaliseringsstyrelsen as part of the Fællesoffentlig Digital Arkitektur (FDA).
They implement Principle 7 ("IT-løsninger samarbejder effektivt") and Architecture Rule 7.1 regarding common integration patterns and technical standards.

---

## General Guidelines (R01-R23)

### Focus on Service Consumers

| ID | Name (EN) | Name (DA) | Description |
|----|-----------|-----------|-------------|
| R01 | Minimal functionality per service | Udstil minimal funktionalitet og data i den enkelte webservice | One webservice should only expose sufficient data/functionality for a specific use case. Reduces coupling and change impact. |
| R02 | Decouple from implementation | Separér webservices fra konkret implementering | Use facades to shield consumers from internal implementation details. |
| R03 | Decouple from external dependencies | Separér webservices fra eksterne afhængigheder | Services should expose own datasets, not external domain objects directly. |

### Responsibility Transfer in Service Calls

| ID | Name (EN) | Name (DA) | Description |
|----|-----------|-----------|-------------|
| R04 | Support retry attempts | Understøt gentagne forsøg på kald fra serviceanvenderen | Services must handle repeated calls idempotently. Consumer is responsible for retrying until response received. |
| R05 | Require transfer information | Kræv specifikke informationer ved ansvarsoverdragelse | For authority handover, require: identifying organization, receiving organization, unique transfer ID, reference to legal basis. Return explicit receipt. |

### Service Documentation

| ID | Name (EN) | Name (DA) | Description |
|----|-----------|-----------|-------------|
| R06 | Document according to framework | Dokumentér udstillede webservices i overensstemmelse med den fællesoffentlige dokumentationsramme | Follow FDA documentation framework (Bilag 1). For REST: use OpenAPI with SmartAPI extensions. |
| R07 | Tag with classification | Opmærk webservices i henhold til fællesoffentlige emnesystematikker | Tag services with KLE or FORM classification codes. |
| R08 | Mark data sensitivity | Opmærk webservices med følsomhed eller fortrolighed af data | Document sensitivity/confidentiality level of data transferred. |
| R09 | Document error codes | Dokumentér servicespecifikke fejlkoder for webservices | All service-specific errors must be documented with codes, descriptions, causes. |
| R10 | Document version lifecycle | Dokumentér drift af forskellige versioner af webservices | Document: versioning strategy, concurrent version support, advance notice period, identification mechanism. |

### Service Versioning

| ID | Name (EN) | Name (DA) | Description |
|----|-----------|-----------|-------------|
| R11 | Use semantic versioning | Anvend semantisk versionering af webservices | Major.Minor.Patch versioning. Major = breaking change. Minor = backward compatible additions. |
| R12 | Maintain old versions | Viderefør gamle versioner, når en webservice ændres | Maintain previous versions during transition period for breaking changes. |

### Service Logging

| ID | Name (EN) | Name (DA) | Description |
|----|-----------|-----------|-------------|
| R13 | Log all calls | Log alle kald til webservices | Log all significant calls, especially those with sensitive/confidential data. |
| R14 | Use transaction identifiers | Anvend transaktionsidentifikatorer ved kald og svar | Require globally unique transaction ID (UUID RFC 4122). Pass through to downstream services. |
| R15 | Use request IDs | Anvend requestID ved kald og svar | Log unique requestID per call. Use same ID for retransmitted responses. |

### Service Availability

| ID | Name (EN) | Name (DA) | Description |
|----|-----------|-----------|-------------|
| R16 | Support monitoring | Understøt monitorering af udstillede webservices | Expose availability/health endpoint. No authentication required. Must not modify data. |

### Service Error Messages

| ID | Name (EN) | Name (DA) | Description |
|----|-----------|-----------|-------------|
| R17 | Standardized error format | Returnér servicespecifikke fejl som standardiserede fejlmeddelelser | Use FDA error structure (Bilag 2). Include error code, name, location, no security-sensitive info. |

### Temporal Resources (Bitemporality)

| ID | Name (EN) | Name (DA) | Description |
|----|-----------|-----------|-------------|
| R18 | Enforce temporal integrity | Forretningsregler vedrørende temporaler indkapsles og håndhæves på serviceniveau | Service must validate temporal integrity for all dimensions. |
| R19 | Default to snapshot | Webservices med temporale ressourcer returnerer som et øjebliksbillede | Default return current valid snapshot (registration time = call time, validity = call time). |
| R20 | Standard temporal parameters | Webservices med temporale ressourcer anvender anerkendte nøgleord | Use "GyldigTidspunkt" for validity timestamp. Registration time is always call receipt time. |
| R21 | Separate history endpoints | Webservices med temporale ressourcer skal udstille ensartet funktionalitet til revision og Linje | Use separate read-only endpoints for history/slices. Parameters: GyldigFra, GyldigTil, RegistreringFra, RegistreringTil. |
| R22 | Consistent temporal handling | Webservices med temporale ressourcer skal anvende ens håndtering af tidspunkter | Fra timestamps are inclusive, Til timestamps are exclusive. |

### Security Requirements

| ID | Name (EN) | Name (DA) | Description |
|----|-----------|-----------|-------------|
| R23 | Token-based security | Webservices skal have tokenbaseret sikkerhed | Use federated token-based authentication. No point-to-point certificate auth (except TLS). |

---

## REST-Specific Guidelines (R24-R40)

### REST Resource Modeling

| ID | Name (EN) | Name (DA) | Description |
|----|-----------|-----------|-------------|
| R24 | Expose as REST resources | Udstil webservices som REST ressourcer | Follow REST architectural style for CRUD operations on resources. |
| R25 | Expose data as resources | Udstil data som REST ressourcer | Even for process triggers, model as resource creation (e.g., "create shipment"). |
| R26 | Model from business domain | Modellér REST ressourcer med udgangspunkt i forretningsmodellering | Base on business modeling per FDA rules for concept/data modeling. |
| R27 | Name from business terms | Navngiv REST ressourcer ud fra forretningsmodellens begreber | Use domain vocabulary: "sager", "journalnotater", "parter". |
| R28 | Name as nouns per REST style | Navngiv REST ressourcer ud fra REST arkitekturstilen | Resources as nouns, no operations in URI. Example: /lokaler/123. |
| R29 | Unique stable identifiers | Udstillede REST ressourcer har unikke, sikre identifikatorer | URIs must be unique, stable over resource lifetime, contain no sensitive data. |
| R30 | Expose related entities | Udstil REST ressourcers relaterede entiteter | Related entities should be separate resources with relationships. |
| R31 | Return hypermedia links | Returnér REST ressourcer med hypertext links | Include links to related resources (HATEOAS). |

### REST Search Operations

| ID | Name (EN) | Name (DA) | Description |
|----|-----------|-----------|-------------|
| R32 | Standardized search parameters | Anvend standardiserede REST fremsøgningsparametre | Use: q (query), sort, fields (projection), embed (related objects). |
| R33 | Support pagination | Understøt søgning med delresultater | Support pagination for large result sets. Use X-Total-Count header and Link header. |

### REST Data Representation

| ID | Name (EN) | Name (DA) | Description |
|----|-----------|-----------|-------------|
| R34 | Standardized data format | Repræsentér REST ressourcer i et standardiseret dataformat | Use JSON or XML. Return format requested by consumer via Accept header. |
| R35 | Declare representations | Deklarér REST ressourcer datarepræsentationer | Document supported formats in OpenAPI. |
| R36 | Internationalized text | Overfør tekst i en internationaliseret repræsentation | Use UTF-8 encoding. Support Accept-Language header. Default to Danish. |

### REST Communication Protocol

| ID | Name (EN) | Name (DA) | Description |
|----|-----------|-----------|-------------|
| R37 | Use HTTP | Anvend HTTP som fællesoffentlig REST kommunikationsprotokol | HTTP is the standard protocol for REST. Use proper HTTP methods and status codes. |
| R38 | Use HTTP mechanisms | Anvend HTTPs mekanismer til effektiv kommunikation | Use HTTP caching, compression, conditional requests. |
| R39 | Secure HTTP | Anvend HTTP sikkert til REST ressourcer | Require HTTPS (TLS 1.1+). Reject unsecure HTTP with error (no redirect). |

### REST Security

| ID | Name (EN) | Name (DA) | Description |
|----|-----------|-----------|-------------|
| R40 | Use OIO IDWS REST | REST webservices skal anvende OIO IDWS REST profile V1.0 | Apply Danish public sector identity and web service security profile. |

---

## Documentation Requirements (Bilag 1)

### Required OpenAPI Metadata Elements

**Basic Service Information (SKAL = mandatory):**
- openapi (version)
- info/title (service name)
- info/description
- info/version (semantic version)
- servers/url (base URI)
- contact/name, contact/url, contact/email

**Should Include (BØR):**
- termsOfService
- x-klassifikation (FORM/KLE codes)
- x-nextmajorversion
- externalDocs

**Resource Documentation (SKAL):**
- Path relative URI
- HTTP methods per path
- operationId (unique per service)
- operation description
- responses

**Parameter Documentation:**
- name, description, in (location), style

**Request/Response Documentation:**
- description
- content (media type)
- schema
- required flag

**Security Documentation:**
- Security scheme type
- Security description

---

## Error Structure (Bilag 2)

Standard error response structure for all services. Key elements:
- Error code (unique identifier)
- Error name/title
- Description
- Location of error occurrence
- No sensitive information in error messages
- Use appropriate HTTP status codes:
  - 2xx: Success
  - 4xx: Client errors
  - 5xx: Server errors

For async operations:
- Return 202 Accepted with location header
- X-Progress header for status polling
- Final response at completion

---

## Non-Functional Requirements (Bilag 3)

### Mandatory Requirements (MK)

| ID | Requirement |
|----|-------------|
| MK1 | Documentation must cover: basic, semantic, syntactic, developer, security, operations |
| MK2 | Semantic versioning |
| MK3 | Transaction identifier in all calls |
| MK4 | Request ID per call |
| MK5 | Language support (default Danish) |
| MK6 | JSON or XML responses |
| MK7 | UTF-8 encoding |
| MK8 | UTC date format |
| MK9 | Temporal: registration time = call time |
| MK10 | Temporal: validity time as parameter |
| MK11 | Model resources from business domain |
| MK12 | Stable URIs |
| MK13 | OpenAPI specification |
| MK14 | JSON documentation file |
| MK15 | GET for read, POST when query too large |
| MK16 | DELETE for individual resources only |
| MK17 | PUT for client-assigned IDs, POST for server-assigned |
| MK18 | PATCH for partial updates |
| MK19 | HTTP as protocol |
| MK20 | HTTPS required, reject HTTP with error |

---

## HTTP Headers (Bilag 4)

### Request Headers
- Content-Type
- Accept
- Content-Encoding
- Accept-Encoding
- Accept-Language
- OIOIDWS headers
- Accept: version
- X-HTTP-Method-Override
- If-Match

### Response Headers
- Content-Type
- Content-Language
- X-Total-Count (for pagination)
- Link (for pagination)
- Retry-After
- Last-Modified
- Status line
- X-Progress (for async)

### Search Parameters
- q (query)
- sort (sorting)
- fields (projection)
- embed (related objects)

---

## Key Governance Checkpoints for AI Analysis

When analyzing an API against these guidelines, the key decision points are:

1. **Documentation Compliance** (R06, Bilag 1)
   - Is OpenAPI spec complete?
   - Are all mandatory metadata elements present?
   - Is classification (FORM/KLE) specified?

2. **Semantic Versioning** (R11, MK2)
   - Is version format X.Y.Z?
   - Are breaking changes reflected in major version?

3. **Resource Modeling** (R24-R31)
   - Are URIs noun-based?
   - Are resources properly separated?
   - Is HATEOAS implemented?

4. **Error Handling** (R17, Bilag 2)
   - Is error structure standardized?
   - Are HTTP status codes correct?
   - Are all error codes documented?

5. **Security** (R23, R39, R40)
   - Is token-based auth used?
   - Is HTTPS enforced?
   - Is OIO IDWS profile followed?

6. **Temporal Handling** (R18-R22)
   - Are temporal parameters correct?
   - Is default behavior snapshot?
   - Are history endpoints separate?

7. **Logging/Tracing** (R13-R15)
   - Are transaction IDs required?
   - Are request IDs used?
   - Is call logging implemented?

8. **Interoperability** (R32-R36)
   - Are search parameters standard?
   - Is pagination supported?
   - Are formats negotiated via headers?
