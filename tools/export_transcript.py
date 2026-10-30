"""Export a Claude Code session transcript (.jsonl) as readable, redacted Markdown.

Keeps what was said (user and assistant text) and one line per tool call (name plus a short
summary of its input). Drops tool outputs, thinking and attachments, which is where secrets and
bulk live. Redacts common credential shapes plus any extra strings listed in a file.

usage: python3 tools/export_transcript.py SESSION.jsonl OUT.md [--redact-file FILE] [--title T]
"""
import json, re, sys

PATTERNS = [
    r"sk-ant-[A-Za-z0-9_\-]{10,}", r"sk-[A-Za-z0-9]{20,}", r"gh[pousr]_[A-Za-z0-9]{20,}",
    r"github_pat_[A-Za-z0-9_]{20,}", r"(?:AKIA|ASIA)[A-Z0-9]{16}", r"xox[abpr]-[A-Za-z0-9\-]{10,}",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----",
    r"(?i)(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*\S{8,}",
    r"(?i)verification code is \d{4,8}", r"eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{10,}",
]

def redactor(extra):
    rx = [re.compile(p) for p in PATTERNS]
    def red(s):
        for e in extra:
            s = s.replace(e, "[REDACTED]")
        for r in rx:
            s = r.sub("[REDACTED]", s)
        return s
    return red

def summarize(inp, limit=300):
    if isinstance(inp, dict):
        for k in ("description", "command", "prompt", "message", "query", "url", "file_path", "pattern"):
            if k in inp:
                v = str(inp[k]).replace("\n", " ")
                return f"{k}: {v[:limit]}" + ("..." if len(v) > limit else "")
        return json.dumps(inp)[:limit]
    return str(inp)[:limit]

def main(argv):
    src, dst = argv[0], argv[1]
    extra, title = [], "Session transcript"
    if "--redact-file" in argv:
        extra = [l.strip() for l in open(argv[argv.index("--redact-file") + 1]) if l.strip()]
    if "--title" in argv:
        title = argv[argv.index("--title") + 1]
    red = redactor(extra)
    out = [f"# {title}\n", "Redacted export: conversation text and one line per tool call; tool outputs omitted.\n"]
    for line in open(src, errors="ignore"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        m = d.get("message") if isinstance(d, dict) else None
        if not isinstance(m, dict):
            continue
        role, ts = m.get("role"), str(d.get("timestamp", ""))[:16].replace("T", " ")
        content = m.get("content")
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]
        for c in content or []:
            if not isinstance(c, dict):
                continue
            if c.get("type") == "text" and c.get("text", "").strip():
                t = c["text"].strip()
                if role == "user" and (t.startswith("<system-reminder>") or t.startswith("<task-notification>")):
                    continue
                out.append(f"\n**{'Cham' if role == 'user' else 'Claude'}** {ts}\n\n{t}\n")
            elif c.get("type") == "tool_use":
                out.append(f"- `{c.get('name')}` {summarize(c.get('input'))}")
    text = red("\n".join(out))
    open(dst, "w").write(text)
    print(f"{dst}: {len(text)/1e6:.2f} MB")

if __name__ == "__main__":
    main(sys.argv[1:])
