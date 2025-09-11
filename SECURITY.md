# Security Policy

We take security seriously. This document explains how to report vulnerabilities and provides guidance on hardening deployments.

## Reporting a Vulnerability

- Prefer private disclosure. If GitHub Security Advisories are available for this repository, open a private advisory.
- If not available, open a minimal public issue asking for a secure contact channel (do not include sensitive details).
- Provide:
  - A clear description of the issue and security impact
  - Minimal reproduction steps and affected version/commit
  - Environment details (OS, Python version)
  - Proof‑of‑concept if safe to share privately

We aim to acknowledge reports within 7 days and, where applicable, provide a remediation plan or patch within 30 days. Timelines may vary based on complexity and severity.

## Scope

In scope:

- Command handlers and admin‑only gating
- Configuration secrets and sensitive data handling
- Injection risks from user content (e.g., replies, Markdown rendering)
- Tool/MCP execution paths and network behaviors
- Dependency and transport vulnerabilities that affect the bot

Out of scope:

- Vulnerabilities in Ollama, IRC networks/servers, or other third‑party providers/libraries
- Social engineering or policy issues unrelated to code or configuration
- Unsupported branches or old releases
- Misconfigurations in self‑hosted environments not caused by code defects

## Coordinated Disclosure and Safe Harbor

Please make a good‑faith effort to avoid privacy breaches, service disruption, or data loss. We support common‑sense safe‑harbor principles for security research conducted and reported responsibly and privately.

## Hardening Guide

See the Security Hardening Guide at `docs/security.md` for practical steps to harden your deployment (channels and admin controls, config secrets, logging, tools/MCP, and more).
