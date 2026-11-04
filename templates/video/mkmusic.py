import json,sys
def write(path,dur,chords,hits): json.dump(dict(dur=dur,chords=chords,hits=hits),open(path,'w'))
