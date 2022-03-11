'''
Each value in names is another list
Example: "Weeknd - In Your Eyes" SHOULD become ->
            [["Weeknd", "In Your Eyes"], ["Weeknd", "In Your"], ["Close Eyes", "Weeknd"]]

        In deep_track_combinations() an additional combination is possible:
        ["Weeknd", "In"]

        The query will take in names[i] and process each entry as:
            Artist: names[i][j][0]
            Track:  names[i][j][1]

        If names[i][j] is such that no Artist is scraped, then ["", "Close Eyes"]
'''

def clean_brackets(s):
    '''
    Wanna remove things like (Official Video), (Official Movie Soundtrack) from subqueries
    Example: if "Lady (Hear Me Tonight) (Official Video)" is passed, 
                return "Lady Hear Me Tonight"
    Note: Tested that both "(Hear Me Tonight)" and just "Hear Me Tonight" give the same result
    '''
    s = s.replace("(", "").replace(")", "")
    if "official" in s.lower():
        x = s.split(" ")
        s = []
        for i in range(len(x)):
            if x[i].lower() == "official":
                break
            s.append(x[i])
        s = " ".join([i for i in s])
    return s

def deep_track_combinations(artist, track):
    perms = [track]
    y = track.split(" ")
    if len(y) > 1:
        y = " ".join([i for i in y[:-1]])
        perms.append(y)
        while len(y) > 0:
            y = y.split(" ")
            y = " ".join([i for i in y[:-1]])
            if y != '':
                perms.append(y)
    for i in range(len(perms)):
        perms[i] = [artist, perms[i]]
    return perms

def track_combinations(artist, track):
    perms = [track]
    y = track.split(" ")
    if len(y) > 1:
        y = " ".join([i for i in y[:-1]])
        perms.append(y)
        while len(y) > 0:
            y = y.split(" ")
            y = " ".join([i for i in y[:-1]])
            if y != '':
                perms.append(y)
        perms = perms[:-1]
    for i in range(len(perms)):
        perms[i] = [artist, perms[i]]
    return perms

def create_queries(entry):
    entry = entry.strip()
    entry = entry.replace('"', "")
    entry = clean_brackets(entry)

    if '-' in entry:
        entry = entry.split('-')
        for j in range(len(entry)):
            entry[j] = entry[j].strip()
        entry = entry[:2]
        '''
        At this point entry has two entries and we want to get all "probable" permutations for this
        Once consider entry[0] as artist and get different combinations with entry[1] (track)
        then do the other way around
        '''
        combinations = []
        combinations.extend(track_combinations(artist=entry[0], track=entry[1]))
        combinations.extend(track_combinations(artist=entry[1], track=entry[0]))
        entry = combinations

    else:
        entry = track_combinations(artist="", track=entry)
    return entry