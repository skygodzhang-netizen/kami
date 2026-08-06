## Description: <br>
Control Home Assistant smart home devices, run automations, and receive webhook events through REST API calls and webhooks. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[seanford](https://clawhub.ai/user/seanford) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External users and developers use this skill to let an agent inspect and control Home Assistant entities, trigger scenes, scripts, and automations, and respond to Home Assistant webhook events. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The skill can give an agent broad authority over smart-home devices and arbitrary Home Assistant services. <br>
Mitigation: Use a least-privilege Home Assistant token, limit exposed entities and scripts, and require explicit confirmation before actions with physical, security, or privacy impact. <br>
Risk: Long-lived Home Assistant tokens can expose the home instance if stored or shared carelessly. <br>
Mitigation: Store tokens outside shared project files, avoid committing configuration files, and rotate tokens if they may have been exposed. <br>
Risk: Inbound webhook handling can trigger agent actions from Home Assistant automations. <br>
Mitigation: Protect webhook requests with a secret authorization header and restrict which automations can call the agent webhook. <br>


## Reference(s): <br>
- [Home Assistant REST API Reference](references/api.md) <br>
- [ClawHub Skill Page](https://clawhub.ai/seanford/skills/home-assistant) <br>
- [Publisher Profile](https://clawhub.ai/user/seanford) <br>


## Skill Output: <br>
**Output Type(s):** [guidance, markdown, shell commands, configuration, API calls] <br>
**Output Format:** [Markdown guidance with shell, JSON, and YAML examples] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Requires curl and jq; uses a Home Assistant URL and long-lived access token supplied by config file or environment variables.] <br>

## Skill Version(s): <br>
1.0.0 (source: ClawHub release metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
