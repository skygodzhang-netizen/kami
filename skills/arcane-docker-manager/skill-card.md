## Description: <br>
Manage Docker containers, stacks, templates, images, networks, volumes, users, and system resources through the Arcane Docker Management API. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[cougz](https://clawhub.ai/user/cougz) <br>

### License/Terms of Use: <br>


## Use Case: <br>
Developers and operators use this skill to have an agent produce API calls, code snippets, and operating guidance for managing a personal Arcane Docker environment. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The skill gives an agent broad Docker infrastructure and credential-management capability. <br>
Mitigation: Install only where the agent is trusted with administrator-level Docker access, prefer scoped credentials, and test on non-production systems first. <br>
Risk: Destructive or privileged operations can stop, delete, prune, deploy, execute commands, change users or roles, or manage API keys. <br>
Mitigation: Require explicit user confirmation before delete, prune, stop, exec, stack deploy, user or role, and API-key actions. <br>
Risk: Tokens, API keys, logs, and error output may expose sensitive operational data. <br>
Mitigation: Avoid broad tokens, store credentials outside prompts when possible, and redact logs and errors before sharing them. <br>


## Reference(s): <br>
- [ClawHub Skill Page](https://clawhub.ai/cougz/skills/arcane-docker-manager) <br>


## Skill Output: <br>
**Output Type(s):** [Text, Markdown, Code, Shell commands, Configuration guidance] <br>
**Output Format:** [Markdown with inline curl, Python, JSON, and shell code blocks] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Produces API-operation guidance, authenticated request examples, troubleshooting notes, and Docker management workflow steps.] <br>

## Skill Version(s): <br>
1.0.0 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
