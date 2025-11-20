from typing import Dict, Tuple


def render_onboarding_email(
    tenant_name: str, links: Dict[str, str], note: str = ""
) -> Tuple[str, str, str]:
    subject = "Coach Flow setup: connect Notion & email"
    text = f"""Hi {tenant_name},

Please connect your accounts so we can get you up and running:

- Connect Notion: {links.get('notion')}
- Connect Email/Calendar (Microsoft): {links.get('microsoft')}

{note or ''}

Thanks,
Sean
Coach Flow"""
    html = f"""<p>Hi {tenant_name},</p>
<p>Please connect your accounts so we can get you up and running:</p>
<ul>
  <li><a href="{links.get('notion')}">Connect Notion</a></li>
  <li><a href="{links.get('microsoft')}">Connect Email/Calendar (Microsoft)</a></li>
  </ul>
<p>{note or ''}</p>
<p>Thanks,<br/>Sean<br/>Coach Flow</p>"""
    return html, text, subject
