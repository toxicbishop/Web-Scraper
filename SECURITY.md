# Security Policy

## Supported Versions

This project follows a continuous development model on the `master` branch and does not currently maintain tagged semantic releases. Security updates and patches are applied directly to the latest commit on `master`.

| Branch / Version | Supported | Notes |
| :--- | :---: | :--- |
| `master` (latest commit) | :white_check_mark: | Actively maintained with security fixes and updates |
| Historical commits / Forks | :x: | Not maintained; please pull the latest changes from `master` |

If you are running an older checkout or fork, please update to the latest `master` commit before reporting an issue, as the vulnerability may have already been addressed.

---

## Reporting a Vulnerability

We take the security of Web Scraper seriously. If you discover or suspect a security vulnerability, please **do not open a public issue, pull request, or discussion**. Instead, report it privately using GitHub's vulnerability reporting system.

### How to Submit a Report

Please submit your report through GitHub's [Private Vulnerability Reporting](https://github.com/toxicbishop/Web-Scraper/security/advisories/new).

To help us triage and resolve the issue quickly, please include as much of the following information as possible:

- **Description**: A clear overview of the issue and potential impact.
- **Affected Component**: Specify whether the issue affects the Next.js frontend, FastAPI backend, Celery task workers, Redis deduplication/scheduling, or database layer.
- **Steps to Reproduce**: A minimal, reproducible example or step-by-step instructions.
- **Proof of Concept (PoC)**: Sample payload, script, or screenshots demonstrating the vulnerability safely.
- **Remediation**: Any suggested patch or mitigation, if you have one.

---

## Response Process & Timelines

When a private security report is submitted:

1. **Acknowledgment**: We will acknowledge receipt of your report within **48 hours**.
2. **Assessment & Triage**: We will investigate and confirm the vulnerability within **7 business days**, providing an initial evaluation and status update.
3. **Resolution**: Once a fix is verified, we will merge the patch into `master` and publish a GitHub Security Advisory acknowledging your contribution (unless you prefer to remain anonymous).

---

## Responsible Disclosure Guidelines

To protect users and target systems, we ask that reporters adhere to the following principles:

- Allow reasonable time for the maintainer to address the vulnerability before public disclosure.
- Do not access, modify, or destroy user data or system configurations without authorization.
- Do not perform testing that causes Denial of Service (DoS) or disrupts service availability.
- When testing scraping logic, do not target third-party production infrastructure without permission.

---

## Operational Security Guidelines for Deployers

If you are deploying this project, please observe the following recommended security practices:

- **Environment Secrets**: Never commit real `.env` files, API keys, JWT secrets (`SECRET_KEY`), database passwords, or AWS credentials to version control. Always use `.env.example` as a template and set strong random values.
- **Network Boundaries**: Ensure supporting infrastructure services like PostgreSQL and Redis are not exposed to the public internet. Use internal Docker network bridges or private VPC subnets.
- **Ethical Scraping**: Configure rate limits, request delays, and respect target website policies and `robots.txt` to avoid unintended disruption or abuse.
