import re
class ParaWeld:
    def __init__(self, max_join_len:int=120): self.max_join_len=max_join_len
    def fuse(self, t:str)->str:
        ls=t.splitlines(); out=[]
        for ln in ls:
            if not out: out.append(ln); continue
            prev=out[-1]
            if prev.endswith('-') and ln and ln[:1].islower(): out[-1]=prev[:-1]+ln; continue
            if len(prev)<self.max_join_len and not re.search(r"[.?!:;)]$", prev.strip()) and (ln[:1].islower() or ln[:1] in {',',';','—','–'}):
                out[-1]=prev.rstrip()+" "+ln.lstrip()
            else: out.append(ln)
        return "\n".join(out)
