import json

look = json.loads(open('look.json').read())

def recur(tree, func, path=""): # recursively iterates through files in a tree
    if tree["type"] == "file":
        return func(tree["name"], path)

    for children in tree["children"]:
        recur(children, func, str(path + "/" + tree["name"]))

# jak ta funkcja zostanie naprawiona (czyt. dowiem sie jak poprawnie zaimplementowac cutdepth, i bedzie poprawnie upierdalal year/date i sam hash zostawial to ten skrypt juz powinien dzialac)
# przekombinowane w chuj, ale cóż... nie mam łba do tego, to jest chyba wlasnie powod dlaczego nie dostalem sie na technika programiste - ta selekcja madrych ludzi ma sens
# w ogole to jeszcze zrozumialem jak bardzo przejebana przyszlosc bede mial, dostalem tego taska tylko dlatego ze gpt nie potrafilo napisac kodu ktory posiada jakakolwiek logike
# wszystkie miejsca dla programistow gdzie beda same latwe taski ktore chatgpt moze wygenerowac zostana zajete przez innych ludzi, i tacy ludzie po techniku informatyku nie beda mogli sobie roboty znalezc :c
def cutdepth(tree, min_depth, max_depth, path="", currentdepth=0):
    tree["parent"] = path
    path += "/" + tree["name"]

    files = []

    for children in tree["children"]:
        if children["type"] == 'directory': 
            if currentdepth >= min_depth and currentdepth <= max_depth: # znalazlem ten kod bruteforcem, calkiem przypadkiem... 
                # chyba to tak ma dzialac, ale nie jestem pewien??
                files.append(children)

            files.extend(cutdepth(children, min_depth, max_depth, path, currentdepth + 1))

    return files

def cutmaxdepth(tree, path="", currentdepth=0):
    tree = dict(tree)
    
    tree["parent"] = path
    path += "/" + tree["name"]

    for children in tree["children"]:
        if children["type"] == 'directory': 
            del children['type']
            if children['name'] == '2E':
                children["children"] = [
                                {
                                    "name": "I",
                                    "children": []
                                },
                                {
                                    "name": "II",
                                    "children": []
                                },
                                {
                                    "name": "III",
                                    "children": []
                                }
                            ] # XDDDDDDDDDDD
                continue
            if currentdepth >= 2: 
                children["children"] = []
                continue

            cutmaxdepth(children, path, currentdepth + 1)

    return tree

punkty_firmowe = {}

def merge(dict1, dict2):
    dict3 = dict1

    for key in dict2:
        if key in dict3:
            dict3[key] += dict2[key]
        else:
            dict3[key] = dict2[key]

    return dict3

def get_max_points(path):
    points = 0

    for entry in look[path]:
        points += look[path][entry]

    return points

def get_organizations_from_tree(file_tree):
    organizations = []
 
    for entry in file_tree['children']:
        if len(entry["name"]) == 5: # E0000
            organizations.append(entry["name"])

    return organizations

def generate_points(file_tree, organization, filtered_paths=[]):
    output = []

    def find(name): # finds a node by path
        tree = file_tree

        for entry in name.split("/"):
            for children in tree["children"]:
                if children["name"] == entry:
                    tree = children

        return tree

    def is_path_allowed(path: str): 
        if "I" in path:
            print(path)
        for filtered_path in filtered_paths:
            if path.startswith(filtered_path):
                return True
        return False

    punkty_okresowe = {}

    for child in cutdepth(find(f"/{organization}"), 2, 2):
        def process(file, path):
            punkciory_by_path = {}

            path = path[1:]

            absolute_path = child["parent"] + "/" + path
            absolute_path_without_org = "/" + "/".join(absolute_path.split("/")[2:])
            if not is_path_allowed(absolute_path_without_org):
                return


            file_name = file[:file.find(".")]
            year, month = child["parent"].split("/")[2:] # 1 - empty, 2 - organization, 3 - year, 4 - month
            if path in look:
                for entry in look[path]:
                    file_compared = entry\
                        .replace("X0000", organization)\
                        .replace("YYYY", year)\
                        .replace("mm", month)\
                        .lower()
                    if file_name.lower() == file_compared:
                        entry_punkty = look[path][entry]
                        output.append(f"BOING! punkciki za {entry} z katalogu {absolute_path}  (plik: {file})")
                        punkciory_by_path[path] = punkciory_by_path.get(path, 0) + entry_punkty
                    elif file == "BD.txt":
                        punkciory_by_path[path] = 9999
                        output.append(f"BOING! full punkty za {absolute_path} = {punkciory_by_path[path]}")

            for entry in look: # dodaje foldery ktorych nie ma w dykcie
                if entry not in punkciory_by_path:
                    punkciory_by_path[entry] = 0

            punkty_okresowe[child["parent"]] = merge(punkciory_by_path, punkty_okresowe.get(child["parent"], {})) 

        recur(child, process)

    punkty_okresowe2 = {}
    for month in punkty_okresowe:
        for subdirectory in punkty_okresowe[month]:
            points = punkty_okresowe[month][subdirectory]
            punkty_okresowe2[month[6:] + "/" + subdirectory] = { # cuts organization
                "points": punkty_okresowe[month][subdirectory],
                "max": get_max_points(subdirectory),
                "skipped": points >= 9999
            }

    return punkty_okresowe2, output

def add_keys(data, parent=""):
    data['key'] = parent + "/" + data['name']
    if 'children' in data:
        for child in data['children']:
            add_keys(child, data['key'])
    return data
        
def get_simplified_tree(file_tree):
    def find(name): # finds a node by path
        tree = file_tree

        for entry in name.split("/"):
            for children in tree["children"]:
                if children["name"] == entry:
                    tree = children

        return tree
        
    orgs = {}

    for meow in get_organizations_from_tree(file_tree):
        depth = cutmaxdepth(find(f"/{meow}/SUR")) 

        children = depth['children']
        for year in children:
            add_keys(year, "")
        orgs[meow] = children

    return orgs