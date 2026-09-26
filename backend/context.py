"""Bound historical context without deleting stored conversations."""
MAX_HISTORY_MESSAGES = 12
MAX_HISTORY_CHARACTERS = 8000

def truncate_history(messages):
    # Keep a contiguous suffix of complete user/assistant exchanges.
    pairs=[]
    for index in range(len(messages)-1):
        if messages[index].role == 'user' and messages[index+1].role == 'assistant':
            pairs.append(messages[index:index+2])
    kept=[]
    used=0
    for pair in reversed(pairs):
        cost=sum(len(message.content) for message in pair)
        if len(kept)+2 > MAX_HISTORY_MESSAGES or used+cost > MAX_HISTORY_CHARACTERS: break
        kept=pair+kept
        used+=cost
    return kept
