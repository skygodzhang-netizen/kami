## Description: <br>
Set up Gmail API access via gog CLI with manual OAuth flow. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[kai-jar](https://clawhub.ai/user/kai-jar) <br>

### License/Terms of Use: <br>


## Use Case: <br>
Developers and operators use this skill to configure Gmail API OAuth credentials for gog, renew expired tokens, and troubleshoot Gmail authentication on headless servers. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The skill handles Gmail OAuth client secrets and refresh tokens that can grant meaningful mailbox access. <br>
Mitigation: Use the narrowest Gmail scope that meets the task, protect OAuth client secrets and refresh tokens, and revoke the Google app when access is no longer needed. <br>
Risk: File-based keyring use on headless systems can expose credentials if passwords are stored in shell startup files. <br>
Mitigation: Avoid storing keyring passwords in shell startup files when possible and restrict access to credential and token files. <br>


## Reference(s): <br>
- [Google Cloud Console](https://console.cloud.google.com) <br>


## Skill Output: <br>
**Output Type(s):** [Guidance, Shell commands, Configuration] <br>
**Output Format:** [Markdown with inline bash commands and an interactive shell helper] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Produces OAuth setup steps, authorization URLs, token exchange commands, and gog import guidance.] <br>

## Skill Version(s): <br>
1.0.0 (source: server release metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
