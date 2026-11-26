"""Self-contained Atlas candidate identity landing. No script or external assets."""
from base64 import b64encode
from hashlib import sha256
from html import escape

STYLE = """*{box-sizing:border-box}
:root{color-scheme:light;--paper:#f5f2e9;--surface:#faf8f2;--ink:#25382d;--muted:#536258;--action:#254b3a;--accent:#a74429;--rule:#cfd2c5}
body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 system-ui,sans-serif}
header{display:flex;justify-content:space-between;align-items:center;gap:18px;padding:20px clamp(20px,5vw,76px);border-bottom:1px solid var(--rule)}
.brand{display:flex;align-items:center;gap:12px;font-weight:700;letter-spacing:-.03em}
.mark{display:grid;place-items:center;background:var(--action);color:white;width:42px;height:42px;flex:none;font:700 20px Georgia,serif}
.mode,.kicker{font-size:11px;text-transform:uppercase;letter-spacing:.13em;font-weight:700;color:var(--muted)}
main{max-width:1440px;margin:auto;padding:clamp(24px,5vw,72px);display:grid;grid-template-columns:minmax(0,1.12fr) minmax(0,.88fr);gap:clamp(24px,6vw,90px);align-items:center;min-height:calc(100vh - 170px)}
h1{font:400 clamp(42px,6vw,88px)/1.02 Georgia,serif;letter-spacing:-.055em;margin:18px 0 24px}
p{margin:0 0 18px;color:var(--muted);max-width:53ch}
.hero-note{border-top:1px solid var(--rule);padding-top:18px;font-size:13px}
.access{background:var(--surface);border:1px solid var(--rule);border-top:4px solid var(--action);padding:clamp(22px,4vw,42px)}
h2{font:400 32px/1.15 Georgia,serif;letter-spacing:-.025em;margin:14px 0}
button,.action{display:block;width:100%;min-height:48px;border:1px solid var(--action);background:var(--action);color:white;padding:12px 16px;text-align:center;text-decoration:none;font:650 15px/1.4 system-ui,sans-serif;cursor:pointer}
button.secondary{background:transparent;color:var(--action)}
button:focus-visible,a:focus-visible{outline:3px solid var(--accent);outline-offset:4px}
form{margin:20px 0 12px}.action+form{margin-top:12px}
.access small{display:block;color:var(--muted);font-size:13px;line-height:1.55}
footer{padding:16px clamp(20px,5vw,76px);border-top:1px solid var(--rule);font-size:12px;color:var(--muted)}
@media(max-width:760px){header{padding:16px 20px;flex-wrap:wrap}main{display:grid;grid-template-columns:1fr;min-height:0;gap:24px;padding:24px 20px 32px}h1{font-size:clamp(38px,10vw,58px);margin:12px 0 18px}.access{padding:22px}h2{font-size:27px}}
"""
STYLE_SOURCE="'sha256-"+b64encode(sha256(STYLE.encode("utf-8")).digest()).decode("ascii")+"'"


def render_landing(*,buyer,csrf=None):
    """Use only fixed copy and the validated session CSRF field."""
    mode="Private fictional buyer workspace" if buyer else "HPI identity qualification"
    if csrf is None:
        title="Look beyond the asking price." if buyer else "A secure entry to HPI."
        description=("Explore historical comparable evidence and compare your options in a private fictional workspace."
                     if buyer else "This local qualification verifies identity only. No property data or buyer workspace is available.")
        access=('<div class="kicker">01 / Account access</div><h2>Sign in</h2>'
                '<p>Continue with the configured identity provider.</p>'
                '<form method="post" action="/auth/start"><button type="submit">Sign in</button></form>'
                '<small>Authentication is handled by Auth0. HPI does not collect your password on this page. Access is restricted to approved accounts.</small>')
    else:
        title="Identity verified"
        description=("Your authenticated private fictional workspace is ready." if buyer else
                     "Local identity qualification only. No property data.")
        access=('<div class="kicker">02 / Session verified</div><h2>Continue securely</h2>'+
                ('<a class="action" href="/private-beta-rehearsal">Open buyer workspace</a>' if buyer else
                 '<p>The identity check is complete. No buyer workspace is enabled in this mode.</p>')+
                '<form method="post" action="/auth/logout">'
                f'<input type="hidden" name="csrf" value="{escape(csrf,quote=True)}">'
                '<button class="secondary" type="submit">Sign out</button></form>'
                '<small>Sign out ends the HPI session on this device. It does not promise sign-out from every identity-provider session.</small>')
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>House Price Intelligence | Account access</title><style>'+STYLE+'</style></head><body>'
            '<header><div class="brand"><span class="mark" aria-hidden="true">H/</span>House Price Intelligence</div>'
            '<span class="mode">'+mode+'</span></header><main><section>'
            '<div class="kicker">PRIVATE ACCESS / LOCAL QUALIFICATION</div><h1>'+title+'</h1><p>'+description+'</p>'
            '<p class="hero-note">'+('Fictional evidence only. No current valuation, real property coordinates or public property records.' if buyer else
            'Identity-only mode. No property records are served by this qualification.')+'</p></section>'
            '<section class="access" aria-label="Account access">'+access+'</section></main>'
            '<footer>HPI · Restricted development access · Historical evidence, not valuation</footer></body></html>')
