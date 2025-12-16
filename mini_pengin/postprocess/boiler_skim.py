import re
from collections import Counter
class BoilerSkim:
    def __init__(self,min_len=6,freq_thresh=0.5,min_pages=3):
        self.min_len=min_len; self.freq_thresh=freq_thresh; self.min_pages=min_pages
    def drop(self,pages):
        n=len(pages)
        if n<self.min_pages: return list(pages)
        norm=lambda s: re.sub(r'\s+',' ', s.strip())
        c=Counter(); per=[]
        for p in pages:
            ls=[norm(l) for l in p.splitlines() if len(l.strip())>=self.min_len]
            per.append(ls); c.update(set(ls))
        remove={l for l,cnt in c.items() if cnt/n>=self.freq_thresh}
        return ['\n'.join([l for l in ls if l not in remove]) for ls in per]
