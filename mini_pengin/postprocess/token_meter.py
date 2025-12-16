import re
def split_tokens(text:str)->int: return len(re.findall(r"[A-Za-z0-9_]+|[^\sA-Za-z0-9_]", text))
class TokenMeter:
    def count(self,text:str)->int: return split_tokens(text)
