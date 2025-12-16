import re
from collections import Counter
class PageTagWiper:
    PAGE_PATTERNS=[r'^page\s+\d+(\s*/\s*\d+| of \d+)?$',r'^p[aá]gina\s+\d+(\s*de\s*\d+)?$',r'^sayfa\s+\d+(\s*/\s*\d+)?$',r'^seite\s+\d+(\s*/\s*\d+)?$',r'^p[aà]ge\s+\d+(\s*/\s*\d+)?$',r'^\d+\s*/\s*\d+$',r'^第?\s*\d+\s*頁?$']
    def strip_headers_footers(self,pages,top_k=2,bottom_k=2,repeat_thresh=0.4,min_pages=3):
        n=len(pages)
        if n<min_pages: return list(pages)
        def top_lines(t,k): return [l.strip() for l in t.splitlines()[:k] if l.strip()]
        def bottom_lines(t,k):
            ls=[l.strip() for l in t.splitlines() if l.strip()]; return ls[-k:] if ls else []
        tc,bc=Counter(),Counter()
        for p in pages:
            for l in top_lines(p,top_k): tc[l]+=1
            for l in bottom_lines(p,bottom_k): bc[l]+=1
        top_remove={l for l,c in tc.items() if c/n>=repeat_thresh}
        bot_remove={l for l,c in bc.items() if c/n>=repeat_thresh}
        cleaned=[]
        for p in pages:
            ls=[x for x in p.splitlines() if x.strip()]
            filt=[l for l in ls if l.strip() not in top_remove and l.strip() not in bot_remove]
            cleaned.append("\n".join(filt))
        return cleaned
    def remove_page_labels(self,text:str)->str:
        for pat in self.PAGE_PATTERNS:
            text=re.sub(pat,"",text,flags=re.IGNORECASE|re.MULTILINE)
        return re.sub(r'\n{3,}','\n\n',text)
