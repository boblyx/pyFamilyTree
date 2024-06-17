"""
main.py
:author: Bob Lee
"""
import os
#import sys
from graphviz import Graph
from uuid import uuid4
from pprint import pprint
from time import time
import xml.etree.ElementTree as et

eg_folder="./samples/elden_ring"
#eg_folder="./samples/house_beor"
OUT_FORMAT="svg" # "pdf" "png"

DEFAULT_OUT="./out"

class RelGraph:
    def __init__(self, category="relation"):
        self.category = category
        self.time = str(time())
        self.out = os.path.join(DEFAULT_OUT, self.time)
        self.charfolder = self.out + "/characters/"
        os.makedirs(self.charfolder, exist_ok=True)
        pass

    @property
    def dot_path(self):
        return "%s/%s.dot" % (self.out, self.category)

    def gNode(self, character):
        nodes = [] # For alterego
        node = {}
        sex = character["sex"]
        suffix = character["suffix"]
        node["id"] = str(character["id"])
        node["image"] = None
        if suffix == None:
            node["text"] = "%s" % (character["name"])
        else:
            node["text"] = "%s\n%s" % (character["name"], character["suffix"])

        if(sex == "m"): node["color"] = "blue"
        elif(sex == "f"): node["color"] = "red"
        else: node["color"] = "gray"
        return node

    def hasChar(self, dot, character):
        if('\t%s' % character["id"] in dot.body): return True
        return False

    def addNode(self, dot, node):
        if('\t%s' % node["id"] in dot.body): return node["id"]
        if(node["image"] == None):
            dot.node(node["id"], color=node["color"], label=node["text"])
        else:
            dot.node(node["id"], color=node["color"], label="<<table cellspacing=\"0\" \
                     border=\"0\" cellborder=\"1\"><tr><td><img src=\"%s\"/></td></tr> \
                     <tr><td>%s</td></tr></table>>" % (node["image"], node["text"]), headport="n") 
        return node["id"]

class FamilyTreeGraph(RelGraph):
    def __init__(self, characters : dict):
        super().__init__("family_tree");
        self.characters = characters
        self.dot = Graph(comment="pyFamilyTree Graph", graph_attr = {"splines": "ortho", \
                "labelloc": "b"}, node_attr={"shape": "box"}) 
        pass

    def resolveSpouses(self, character, node):
        """
        TODO
        """
        for r in character["relations"]:
            if not r["type"] == "spouse": continue
        pass
    
    def resolveDescendants(self, character, node):
        """
        TODO
        """
        pass

    def resolveAncestors(self, character, completed_unions, edges):
        # Resolve mother and father
        characters = self.characters
        cid = character["id"]
        unions = set()
        ancestors = {"mothers":[], "fathers": [], "ancestor": []}
        for r in character["relations"]:
            """
            if(r["type"] == "spouse"):
                if r["id"] in characters:
                    spouse_node = self.gNode(characters[r["id"]])
                    union = []
                    if character["sex"] == "m":
                        union = [character["id"], r["id"]]
                    else:
                        union= [r["id"], character["id"]]
                    spouse_union = "%s-x-%s" % (union[0], union[1])
                    ug = Graph()
                    ug.attr(rank="same")
                    ug.node(spouse_union, shape="diamond", width="0.1", height="0.1", label="")
                    ug.edge(union[0], spouse_union)
                    ug.edge(spouse_union, union[1])
                    self.dot.subgraph(ug)
                    pass
                pass
            """
            if(r["type"] == "father"):
                ancestors["fathers"].append(r["id"])
                if r["with"] == None: continue
                unions.add(frozenset([r["id"], r["with"]]))
                pass
            if(r["type"] == "mother"):
                ancestors["mothers"].append(r["id"])
                if r["with"] == None: continue
                unions.add(frozenset([r["with"],r["id"]]))
            if(r["type"] == "ancestor"):
                ancestors["ancestor"].append(r["id"])
            pass
        print(character["name"])
        for u in unions:
            umem = list(u)
            if not umem[0] in characters:
                continue
            fid = umem[0]
            father = characters[fid]
            if not umem[1] in characters:
                continue
            mid = umem[1]
            mother = characters[mid]
            fnode = self.gNode(father)
            mnode = self.gNode(mother)
            parents = Graph()
            parents.attr(rank="same")
            self.addNode(parents, mnode)
            self.addNode(parents, fnode)
            fm_union_id = fid+"-x-"+mid
            print("\t"+fm_union_id)
            c_union_id = "c-"+fm_union_id
            if not fm_union_id in completed_unions:
                self.dot.node(fm_union_id, shape="diamond", width="0.1", height="0.1", label="")
                parents.edge(fid, fm_union_id)
                parents.edge(fm_union_id, mid)
                self.dot.subgraph(parents)
                self.dot.node(c_union_id, shape="point", size="0.1")
                completed_unions.add(fm_union_id)
                self.dot.edge(fm_union_id, c_union_id)
            self.dot.edge(c_union_id, cid)

        for a in ancestors["ancestor"]:
            print("\t"+a)
            if not a in characters:
                continue
            ancestor = characters[a]
            anode = self.gNode(ancestor)
            eid = "a-%s-%s" % (a, character["id"])
            if not self.hasChar(self.dot, ancestor): 
                self.addNode(self.dot, anode)
                self.dot.edge(a, character["id"])
                edges.add(eid)
            elif not eid in edges:
                self.dot.edge(a, character["id"])
                edges.add(eid)
            pass

        return {"unions": unions, "ancestors": ancestors}

    def gDot(self, file_format="pdf"):
        count = 0
        completed_unions = set()
        edges = set()
        for key, c in characters.items():
            cnode = self.gNode(c)
            self.addNode(self.dot, cnode)
            ancestors = self.resolveAncestors(c, completed_unions, edges)
            #self.resolveDescendants(c, node)
        print(self.dot_path)
        self.dot.format = file_format
        self.dot.render(filename = self.dot_path)
        return

def xmlToChar(tree):
    """
    Converts an XML ElementTree into
    a Character dict
    """
    root = tree.getroot()
    cid = root.attrib["id"]
    name = root.find("name").text
    sex = root.find("sex").text
    suffix = root.find("suffix").text
    rlist = []
    relations = root.find("relations").findall("relation");
    for r in relations:
        rel = {"type": r.attrib["type"]
               , "with": None
               , "id": None
               , "order": None}
        for k in rel.keys():
            if k in r.attrib: 
                rel[k] = r.attrib[k]
        rlist.append(rel)
        pass
    
    character = {"id": root.attrib["id"]
                 ,"name": name
                 ,"sex": sex
                 ,"suffix": suffix
                 ,"relations": rlist
                 ,"image": None
                 }
    # Optional Tags
    titles = root.find('titles')
    tlist = []
    if not titles == None:
        titles = titles.findall('title')
        for t in titles:
            tlist.append(t.text)
    
    character["titles"] = tlist

    alter_ego = root.find('alter_ego')
    if not alter_ego == None:
        alter_ego = alter_ego.attrib["id"]
        character["alter_ego"] = alter_ego
    return character

def makeCharacters(folder):
    characters = {}
    for data_file in os.listdir(folder):
        fp = os.path.join(eg_folder, data_file)
        tree = et.parse(fp)
        character = xmlToChar(tree)
        characters[character["id"]] = character
        pass
    return characters

if __name__ == "__main__":
    # First create all characters in a family tree dict
    characters = makeCharacters(eg_folder)
    family_tree = FamilyTreeGraph(characters)
    family_tree.gDot(OUT_FORMAT)
    pass
