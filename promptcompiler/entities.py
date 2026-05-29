"""Protected entity extraction for values that should survive compression."""

from __future__ import annotations

from functools import lru_cache
import re


_ENTITY_PATTERNS = [
    re.compile(r"https?://[^\s)\"']+"),
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"),
    re.compile(r"[$€£]\s?\d+(?:,\d{3})*(?:\.\d+)?"),
    re.compile(r"\b\d+(?:\.\d+)?%"),
    re.compile(r"\b[A-Z]{2,}[A-Z0-9]*-\d+[A-Z0-9-]*\b"),
    re.compile(r"(?:>=|<=|>|<)\s?\d+(?:\.\d+)?\b"),
    re.compile(r"\b(?:GET|POST|PUT|DELETE|PATCH|WebSocket)\s+/[^\s,]+", re.IGNORECASE),
    re.compile(r"\b(?:HIPAA|GDPR|PCI\s*DSS|SOC\s*2|SOX|FERPA|CCPA|HITECH)\b"),
    re.compile(r"\b(?:OAuth2?|OIDC|SAML|JWT|TOTP|HOTP|MFA|2FA|SSO)\b"),
    re.compile(r"\b(?:FHIR\s*R[45]?|HL7|DICOM|HL7\s*v2)\b"),
    re.compile(r"\b(?:AES-?\d{3}|RSA|TLS\s*1\.\d|SSL|E2EE)\b"),
    re.compile(r"\b(?:AWS\s+S[0-3]|Azure\s+\w+|GCP\s+\w+|Cloudflare\s+R2)\b"),
    re.compile(r"\b(?:PostgreSQL|MySQL|MongoDB|Redis\s*\d*|Elasticsearch\s*\d*|RabbitMQ|Kafka)\b"),
    re.compile(r"\b(?:Docker|Kubernetes|K8s|Terraform|Helm|ArgoCD|GitHub\s+Actions)\b"),
    re.compile(r"\b(?:Stripe|PayPal|Twilio|SendGrid|Firebase|Sentry|Datadog|PagerDuty)\b"),
    re.compile(r"\b\d+(?:\.\d+)?\s*(?:ms|MB|GB|TB|req/s|rps|QPS)\b"),
    re.compile(r"\b[0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5}\b"),
    re.compile(r"\b(?:p\d{1,2})\b", re.IGNORECASE),
]


@lru_cache(maxsize=256)
def extract_entities(text: str) -> list[str]:
    """Return protected entities in first-seen order."""

    seen: set[str] = set()
    entities: list[str] = []

    for pattern in _ENTITY_PATTERNS:
        for match in pattern.finditer(text):
            value = match.group(0).rstrip(".,;:")
            if value and value not in seen:
                seen.add(value)
                entities.append(value)

    return entities
