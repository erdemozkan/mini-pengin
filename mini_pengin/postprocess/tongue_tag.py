try:
    from langdetect import detect
except Exception:
    detect=None
class TongueTagger:
    def guess(self,text:str)->str:
        if detect is None: return "unknown"
        try: return detect(text[:10000])
        except Exception: return "unknown"
