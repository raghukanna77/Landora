import re

def extract_entities(text:str):
    t=text.lower()
    entities=[]
    keywords=["compensation","sia","survey","land records","court","award","consent","possession","notification","rehabilitation","resettlement","documentation"]
    for kw in keywords:
        if kw in t:
            entities.append(kw)
    # extract survey numbers like 123/4
    surv=re.findall(r"\b\d+/\d+\b", text)
    entities.extend(surv)
    # dates
    dates=re.findall(r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b", text)
    entities.extend(dates)
    return list(dict.fromkeys(entities))[:10]
