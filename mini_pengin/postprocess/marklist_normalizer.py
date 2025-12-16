import re
class MarklistNormalizer:
    BULLETS="•◦‣⁃▪▫●○♦▶►▸−–—"
    def normalize(self,text:str)->str:
        b=re.escape(self.BULLETS)
        pat=re.compile(r'^[\t ]*([%s\-–—])\s*(.*)$'%b, re.MULTILINE)
        def repl(m): return "- "+(m.group(2) or "")
        text=pat.sub(repl,text)
        text=re.sub(r'^[\t ]*\[(x|X)\]\s*','- [x] ',text,flags=re.MULTILINE)
        text=re.sub(r'^[\t ]*\[\s*\]\s*','- [ ] ',text,flags=re.MULTILINE)
        return text
