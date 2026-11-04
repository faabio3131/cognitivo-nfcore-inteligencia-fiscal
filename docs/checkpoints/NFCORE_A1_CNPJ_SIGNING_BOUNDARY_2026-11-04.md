# NFCore V1 — A1 issuer-bound signing boundary (2026-11-04)

## Baseline and scope

- Canonical repository: `faabio3131/nf-core-v001` (formerly `kordena-fiscal-engine-v2`, same repository ID).
- Base: PR #348, `47410f8cc13243622bae3fc15b6761d4a7546635`, originally against `main@16b320e41726e846ac3cf1ffb753b566e979842b`.
- This increment uses the existing `FiscalSignatureRequest`, `CryptographyFiscalDocumentSigner`, scoped `SecretResolutionService`, and `validate_a1_for_issuer` from PR #348.
- No second signing engine, vault, authentication, tenant authority, storage or HTTP endpoint.

## Current to target

- Before: the generic detached signer checked the PKCS#12 identity and certificate validity but did not bind the A1 certificate's ICP-Brasil SAN CNPJ to an issuing CNPJ.
- Increment: `FiscalSignatureRequest.issuer_cnpj` is an explicit optional `Cnpj` value; `CryptographyFiscalDocumentSigner(require_issuer_cnpj=True)` rejects unsigned issuer context and verifies that the **same Vault material used for signing** has valid certificate metadata and exactly the expected SAN CNPJ.
- Default mode remains backward compatible for historical detached-signature callers. For any accountant pilot operation, trusted runtime composition MUST enable `require_issuer_cnpj=True` and obtain `issuer_cnpj` from the canonical persisted fiscal issuer, never a client-supplied header or form field.
- The preflight does not certify ICP-Brasil chain trust/revocation, legal representation, SEFAZ registration, official mTLS, XMLDSig schema profiles or authorization to issue.
- This increment does not provision a certificate into the external Vault: existing Vault adapters are read-only. A governed onboarding/rotation/revocation write workflow remains a separate blocked dependency.

## Acceptance and evidence

- Synthetic certificate with valid CNPJ: signs and verifies.
- No issuer CNPJ when required: fail-closed before resolving the secret.
- Wrong CNPJ, absent SAN/keyUsage, and cross-tenant secret: fail-closed with sanitized errors.
- Existing signer/vault/gateway behavior preserved.
- Locally verified (Python 3.12, `PYTHONPATH=src`): 45 directed tests PASS, Ruff PASS. Mypy and remote CI/Governance to be captured on the final candidate SHA.
- No real certificate, real customer data, fiscal provider traffic, migration, Contabo deploy, production activation or `main` merge in this increment.

## Outstanding build and external gates

1. Approved issuer registry/binding of tenant + unit + environment + CNPJ, RBAC/step-up and external vault certificate onboarding with rotation/revocation/audit.
2. Enforce bound signer on the actual composed preparation/issuance path, including NF-e, NFC-e and approved NFS-e-specific signature capability.
3. Use officially versioned XML/XSD and endpoint configs for the exact jurisdiction/operation; authenticated HTTP/SOAP mTLS; safe timeout/idempotency/reconciliation.
4. CI/Governance on exact SHA, targeted integration with PostgreSQL and E2E authenticated issuer/isolation.
5. Official SEFAZ/NFS-e homologation using companies' own credentials and evidence, followed by separate human production approval.

Status: **IMPLEMENTED_NOT_CERTIFIED** until remote gates succeed. Fiscal production remains **BLOCKED_EXTERNAL**.
