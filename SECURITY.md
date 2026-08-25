# Security Policy

## Scope

Magic Home Control is designed to run on a trusted local network. It controls Flux LED bulbs through their local network protocol and currently provides:

- A FastAPI backend
- An Angular web frontend
- A Tkinter desktop client
- A SQLite database containing device names, IP addresses, device types, and RGB channel order
- Docker Compose deployment

The project does not currently provide user authentication, authorization, HTTPS, or internet-safe remote access.

## Supported Versions

Only the latest version on the default branch is actively maintained for security fixes.

| Version | Supported |
| --- | --- |
| Latest | Yes |
| Older versions | No |

## Security Model

The backend and frontend are intended for use inside a trusted home or private network. Anyone who can access the backend can potentially:

- Read configured device names and IP addresses
- Add or remove devices
- Turn bulbs on or off
- Change bulb colors and brightness

Treat access to port `8000` and the web interface on port `8080` as access to the light-control system.

## Deployment Requirements

- Do not expose ports `8000` or `8080` directly to the public internet.
- Keep Docker Desktop and its base images updated.
- Run the services only on a trusted network.
- Use firewall rules to restrict access to known local devices where practical.
- Keep the host operating system, Python, Node.js, and browser updated.
- Back up `data/devices.db` securely because it contains home-network device information.

Before allowing remote access, put the application behind an authenticated HTTPS reverse proxy and add backend authentication and authorization. A VPN is preferable to exposing the API directly.

## Sensitive Data

The current application does not store passwords or cloud API tokens. However, `data/devices.db` contains private network information, including bulb IP addresses. Protect it as confidential local configuration:

- Do not commit personal production databases to source control.
- Do not upload database files or logs containing private IP addresses to public issue trackers.
- Do not include real home-network addresses in screenshots or example code unless intentionally redacted.
- Do not add credentials, tokens, or secrets to `compose.yaml`, source files, or frontend code.

The legacy `data/devices.csv` file is used only as a first-start migration source. Remove or protect it after confirming the SQLite migration if it is no longer needed.

## Bulb Network Security

Flux bulbs are controlled over the local network. The backend must be able to reach the bulb's local control port. Network isolation, guest Wi-Fi settings, firewall rules, incorrect IP addresses, or powered-off bulbs can prevent communication.

Do not assume that a bulb's local protocol is encrypted or authenticated. Network access to the bulb network should therefore be limited to trusted devices.

## Reporting a Vulnerability

Please do not disclose security vulnerabilities in a public issue first.

Report a vulnerability privately to the repository maintainer with:

- A clear description of the issue
- The affected component and version or commit
- Reproduction steps or a minimal proof of concept
- The possible security impact
- Any suggested mitigation

Remove private IP addresses, personal information, credentials, and other sensitive data from the report where possible. If no private contact method is configured, open a minimal issue asking for a private reporting channel without including vulnerability details.

You should receive an acknowledgement within 14 days. The maintainer will assess the issue, coordinate a fix, and document the resolution as appropriate.

## Secure Development

When contributing:

- Validate all API input with the existing Pydantic models.
- Keep device-control operations on the backend; never trust the frontend for authorization decisions.
- Avoid logging credentials, tokens, or unnecessary network details.
- Mock physical bulbs in tests instead of requiring real devices.
- Review dependency updates and pin production dependencies where practical.
- Keep the CORS allowlist limited to the actual frontend origins.
- Test error handling for unreachable devices and malformed requests.
- Do not weaken validation or network restrictions to make a local test pass.

## Current Limitations

The following protections are not implemented yet:

- User authentication
- Per-user authorization
- HTTPS by default
- CSRF protection for authenticated browser sessions
- Rate limiting
- Audit logging
- Encrypted device storage
- Automatic IP discovery with validation

These limitations are acceptable for a trusted local development or home network, but must be addressed before deploying the application for multiple users or exposing it beyond the private network.

## Security Checklist Before Remote Deployment

- [ ] Add backend authentication and authorization.
- [ ] Serve the frontend and API through HTTPS.
- [ ] Restrict CORS to the production frontend origin.
- [ ] Put the application behind a VPN or authenticated reverse proxy.
- [ ] Add rate limiting and request logging without sensitive data.
- [ ] Back up and protect the SQLite database.
- [ ] Review Docker, Python, Node.js, and npm dependencies.
- [ ] Confirm that bulbs are isolated from untrusted networks.
