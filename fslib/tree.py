#
# Kopirajto © 2022 Jean Michault
# Licenco «GPL-3.0-or-later»
#
# Ĉi tiu programo estas libera programaro; vi povas redistribui ĝin kaj/aŭ modifi
# ĝi laŭ la kondiĉoj de la Ĝenerala Publika Permesilo de GNU kiel eldonita de
# la Free Software Foundation; ĉu versio 3 de la Licenco, aŭ
# (laŭ via elekto) ajna posta versio.
#
# Ĉi tiu programo estas distribuata kun la espero, ke ĝi estos utila,
# sed SEN AJN GARANTIO; sen eĉ la implicita garantio de
# KOMERCEBLECO aŭ TAĜECO POR APARTA CELO. Vidu la
# GNU Ĝenerala Publika Permesilo por pliaj detaloj.
#
# Vi devus esti ricevinta kopion de la Ĝenerala Publika Permesilo de GNU
# kune kun ĉi tiu programo; se ne, skribu al 
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

from typing import Union

import sys
import re
import asyncio
from urllib.parse import unquote

# local imports
from fslib import gedcomx
from fslib.constants import (
    MAX_PERSONS,
    FACT_EVEN,
    FACT_TAGS,
    ORDINANCES_STATUS,
)
from fslib.dateformal import DateFormal
from fslib.json import maljsonigi

import gettext
_ = gettext.gettext

class Note(gedcomx.Note):
    """GEDCOM Note class
    :param id: FS ID
    :param subject: the Note subject
    :param text: the Note content
    :param tree: a Tree object
    :param num: the GEDCOM identifier
    """

    _counter = 0

    def __init__(self, id,subject, text, tree=None, num=None):
        if num:
            self._num = num
        else:
            Note._counter += 1
            self._num = Note._counter
        self.id = id.strip()
        self.subject = subject.strip()
        self.text = text.strip()

        if tree:
            tree._notes.append(self)

class Source:
    """ Source class
    :param data: FS Source data
    :param tree: a Tree object
    :param num: the GEDCOM identifier
    """

    _counter = 0

    def __init__(self, data=None, tree=None, num=None):
        if num:
            self._num = _num
        else:
            Source._counter += 1
            self._num = Source._counter

        self._tree = tree
        self.url = self.citation = self.title = self.id = None
        self.notes = set()
        if data:
            self.id = data["id"]
            if "about" in data:
                self.url = data["about"].replace(
                    "familysearch.org/platform/memories/memories",
                    "www.familysearch.org/photos/artifacts",
                )
            if "citations" in data:
                self.citation = data["citations"][0]["value"]
            if "titles" in data:
                self.title = data["titles"][0]["value"]
            if "notes" in data:
                for n in data["notes"]:
                  self.notes.add(Note(
                     n["id"] if "id" in n else "FS note"
                    ,n["subject"] if "subject" in n else ""
                    ,n["text"] if "text" in n else ""
                    , self._tree))

class Memorie:
  """ Memorie class
  " :param data: FS Memorie data
  """

  def __init__(self, data=None):
    self.description = self.url = None
    if data and "links" in data:
      self.url = data["about"]
      if "titles" in data:
        self.description = data["titles"][0]["value"]
      if "descriptions" in data:
        self.description = (
                "" if not self.description else self.description + "\n"
            ) + data["descriptions"][0]["value"]


class Ordinance:
    """ Ordinance class
    :param data: FS Ordinance data
    """

    def __init__(self, data=None):
        self.date = self.temple_code = self.status = self.famc = None
        if data:
            if "completedDate" in data:
                self.date = data["completedDate"]
            if "completedTemple" in data:
                self.temple_code = data["completedTemple"]["code"]
            self.status = data["status"]

class Person(gedcomx.Person):
    """GEDCOM individual class
    :param id' FamilySearch id
    :param tree: a tree object
    :param num: the GEDCOM identifier
    """

    _counter = 0

    def __init__(self, id=None, tree=None, num=None):
        if num:
            self._num = num
        else:
            Person._counter += 1
            self._num = Person._counter
        self._tree = tree
        self.id = id
        self.famc_fid = set()
        self.fams_fid = set()
        self.famc_num = set()
        self.fams_num = set()
        self.name = None
        self.gender = None
        self.parents = set()
        self.spouses = set()
        self.children = set()
        self.baptism = self.confirmation = self.initiatory = None
        self.endowment = self.sealing_child = None
        self.nicknames = set()
        self.facts = set()
        self.birthnames = set()
        self.married = set()
        self.aka = set()
        self.notes = set()
        self.sources = set()
        self.memories = set()
        self.names = set()

    def add_data(self, data):
        """add FS individual data"""
        maljsonigi(self,data)
        return
        #    # FARINDAĴO : portrait
        #    #if "links" in data:
        #    #    req = self._tree.fs.get_url(
        #    #        "/platform/tree/persons/%s/portrait" % self.id
        #    #        , {"Accept": "image/*"}
        #    #    )
        #    #    if req and req.text:
        #    #      print(req.url)
        #    #      self.portrait = req.text
        #    #      self.portrait_type = req.headers["Content-Type"]
        #    #      self.portrait_url = req.url
        #    if "evidence" in data:
        #        url = "/platform/tree/persons/%s/memories" % self.id
        #        memorie = self._tree.fs.get_url(url)
        #        if memorie and "sourceDescriptions" in memorie:
        #            for x in memorie["sourceDescriptions"]:
        #                # FARINDAĴO : "text/plain" + memory
        #                #if x["mediaType"] == "text/plain":
        #                #    subject = "\n".join(
        #                #        val.get("value", "")
        #                #        for val in x.get("titles", [])
        #                #      )
        #                #    text = "\n".join(
        #                #        val.get("value", "")
        #                #        for val in x.get("descriptions", [])
        #                #      )
        #                #    self.notes.add(Note(x["id"] if "id" in x else "FS memorie",subject,text, self._tree))
        #                #else:
        #                self.memories.add(Memorie(x))

    def add_fams(self, fams):
        """add family fid (for spouse or parent)"""
        self.fams_fid.add(fams)

    def add_famc(self, famc):
        """add family fid (for child)"""
        self.famc_fid.add(famc)

    def get_notes(self):
        """retrieve individual notes"""
        notes = self._tree.fs.get_url("/platform/tree/persons/%s/notes" % self.id)
        if notes:
            for n in notes["persons"][0]["notes"]:
                self.notes.add(Note(
                    n["id"] if "id" in n else ""
                    ,n["subject"] if "subject" in n else ""
                    ,n["text"] if "text" in n else ""
                    , self._tree))

    def get_ordinances(self):
        """retrieve LDS ordinances
        need a LDS account
        """
        res = []
        famc = False
        if self.living:
            return res, famc
        url = "/service/tree/tree-data/reservations/person/%s/ordinances" % self.id
        data = self._tree.fs.get_url(url, {})
        if data:
            for key, o in data["data"].items():
                if key == "baptism":
                    self.baptism = Ordinance(o)
                elif key == "confirmation":
                    self.confirmation = Ordinance(o)
                elif key == "initiatory":
                    self.initiatory = Ordinance(o)
                elif key == "endowment":
                    self.endowment = Ordinance(o)
                elif key == "sealingsToParents":
                    for subo in o:
                        self.sealing_child = Ordinance(subo)
                        relationships = subo.get("relationships", {})
                        father = relationships.get("parent1Id")
                        mother = relationships.get("parent2Id")
                        if father and mother:
                            famc = father, mother
                elif key == "sealingsToSpouses":
                    res += o
        return res, famc

    def get_contributors(self):
        """retrieve contributors"""
        temp = set()
        url = "/platform/tree/persons/%s/changes" % self.id
        data = self._tree.fs.get_url(url, {"Accept": "application/x-gedcomx-atom+json"})
        if data:
            for entries in data["entries"]:
                for contributors in entries["contributors"]:
                    temp.add(contributors["name"])
        if temp:
            text = "\n".join(sorted(temp))
            for n in self._tree._notes:
                if n.text == text:
                    self.notes.add(n)
                    return
            self.notes.add(Note('FS contributors',self._tree.fs._("Contributors"),text, self._tree))

class Relationship(gedcomx.Relationship):
    """GEDCOM family class
    :param husb: husbant fid
    :param wife: wife fid
    :param tree: a Tree object
    :param num: a GEDCOM identifier
    """

    _counter = 0

    def __init__(self, husb=None, wife=None, tree=None, num=None):
        if num:
            self._num = num
        else:
            Relationship._counter += 1
            self._num = Relationship._counter
        self.husb_fid = husb if husb else None
        self.wife_fid = wife if wife else None
        self._tree = tree
        self.husb_num = self.wife_num = self.fid = None
        self.facts = set()
        self.sealing_spouse = None
        self.chil_fid = set()
        self.chil_num = set()
        self.notes = set()
        self.sources = set()

    def add_child(self, child):
        """add a child fid to the family"""
        if child not in self.chil_fid:
            self.chil_fid.add(child)

    def add_marriage(self, fid):
        """retrieve and add marriage information
        :param fid: the marriage fid
        """
        if not self.fid:
            self.fid = fid
            url = "/platform/tree/couple-relationships/%s" % self.fid
            data = self._tree.fs.get_url(url)
            if data:
                maljsonigi(self._tree,data)
                #if "facts" in data["relationships"][0]:
                #    for x in data["relationships"][0]["facts"]:
                #        self.facts.add(Fact(x, self._tree))
                if self._tree._getsources and "sources" in data["relationships"][0]:
                    quotes = dict()
                    for x in data["relationships"][0]["sources"]:
                        quotes[x["descriptionId"]] = (
                            x["attribution"]["changeMessage"]
                            if "changeMessage" in x["attribution"]
                            else None
                        )
                    new_sources = quotes.keys() - self._tree._sources.keys()
                    if new_sources:
                        sources = self._tree.fs.get_url(
                            "/platform/tree/couple-relationships/%s/sources" % self.fid
                        )
                        for source in sources["sourceDescriptions"]:
                            if (
                                source["id"] in new_sources
                                and source["id"] not in self._tree._sources
                            ):
                                self._tree._sources[source["id"]] = Source(
                                    source, self._tree
                                )
                    for source_fid in quotes:
                        self.sources.add(
                            (self._tree._sources[source_fid], quotes[source_fid])
                        )

    def get_notes(self):
        """retrieve marriage notes"""
        if self.fid:
            notes = self._tree.fs.get_url(
                "/platform/tree/couple-relationships/%s/notes" % self.fid
            )
            if notes:
                for n in notes["relationships"][0]["notes"]:
                    self.notes.add(Note(
                         n["id"] if "id" in n else ""
                        ,n["subject"] if "subject" in n else ""
                        ,n["text"] if "text" in n else ""
                        , self._tree))

    def get_contributors(self):
        """retrieve contributors"""
        if self.fid:
            temp = set()
            url = "/platform/tree/couple-relationships/%s/changes" % self.fid
            data = self._tree.fs.get_url(
                url, {"Accept": "application/x-gedcomx-atom+json"}
            )
            if data:
                for entries in data["entries"]:
                    for contributors in entries["contributors"]:
                        temp.add(contributors["name"])
            if temp:
                text = "\n".join(sorted(temp))
                for n in self._tree._notes:
                    if n.text == text:
                        self.notes.add(n)
                        return
                self.notes.add(Note('FS contributors',self._tree.fs._("Contributors"),text, self._tree))

class Tree(gedcomx.Gedcomx):
    """ gedcomx tree class
    :param fs: a Session object
    """
    def __init__(self, fs=None):
        self.fs = fs
        self._persons = dict()
        self._fam = dict()
        self._places = dict()
        self._getsources = True
        self._sources = dict()
        self._notes = list()

    def add_persons(self, fids):
        """add individuals to the family tree
        :param fids: an iterable of fid
        """

        async def add_datas(loop, data):
            futures = set()
            for person in data["persons"]:
                self._persons[person["id"]] = Person(person["id"], self)
                futures.add(
                    loop.run_in_executor(None, self._persons[person["id"]].add_data, person)
                )
            for future in futures:
                await future

        new_fids = [fid for fid in fids if fid and fid not in self._persons]
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        while new_fids:
            data = self.fs.get_url(
                "/platform/tree/persons?pids=" + ",".join(new_fids[:MAX_PERSONS])
            )
            if data:
                #if "places" in data:
                #    for place in data["places"]:
                #        if place["id"] not in self._places:
                #            self._places[place["id"]] = (
                #                str(place["latitude"]),
                #                str(place["longitude"]),
                #                place["names"],
                #            )
                loop.run_until_complete(add_datas(loop, data))
                if "childAndParentsRelationships" in data:
                    for rel in data["childAndParentsRelationships"]:
                        father = (
                            rel["parent1"]["resourceId"] if "parent1" in rel else None
                        )
                        mother = (
                            rel["parent2"]["resourceId"] if "parent2" in rel else None
                        )
                        child = rel["child"]["resourceId"] if "child" in rel else None
                        if child in self._persons:
                            self._persons[child].parents.add((father, mother))
                        if father in self._persons:
                            self._persons[father].children.add((father, mother, child))
                        if mother in self._persons:
                            self._persons[mother].children.add((father, mother, child))
                if "relationships" in data:
                    for rel in data["relationships"]:
                        if rel["type"] == "http://gedcomx.org/Couple":
                            person1 = rel["person1"]["resourceId"]
                            person2 = rel["person2"]["resourceId"]
                            relfid = rel["id"] or 'xxxx'
                            if person1 in self._persons:
                                self._persons[person1].spouses.add(
                                    (person1, person2, relfid)
                                )
                            if person2 in self._persons:
                                self._persons[person2].spouses.add(
                                    (person1, person2, relfid)
                                )
                            self.add_fam(person1,person2)
                            family = self._fam[(person1, person2)]
                            family.add_marriage(relfid)
            new_fids = new_fids[MAX_PERSONS:]

    def add_fam(self, father, mother):
        """add a family to the family tree
        :param father: the father fid or None
        :param mother: the mother fid or None
        """
        if (father, mother) not in self._fam:
            self._fam[(father, mother)] = Relationship(father, mother, self)

    def add_trio(self, father, mother, child):
        """add a children relationship to the family tree
        :param father: the father fid or None
        :param mother: the mother fid or None
        :param child: the child fid or None
        """
        if father in self._persons:
            self._persons[father].add_fams((father, mother))
        if mother in self._persons:
            self._persons[mother].add_fams((father, mother))
        if child in self._persons and (father in self._persons or mother in self._persons):
            self._persons[child].add_famc((father, mother))
            self.add_fam(father, mother)
            self._fam[(father, mother)].add_child(child)

    def add_parents(self, fids):
        """add parents relationships
        :param fids: a set of fids
        """
        parents = set()
        for fid in fids & self._persons.keys():
            for couple in self._persons[fid].parents:
                parents |= set(couple)
        if parents:
            self.add_persons(parents)
        for fid in fids & self._persons.keys():
            for father, mother in self._persons[fid].parents:
                if (
                    mother in self._persons
                    and father in self._persons
                    or not father
                    and mother in self._persons
                    or not mother
                    and father in self._persons
                ):
                    self.add_trio(father, mother, fid)
        return set(filter(None, parents))

    def add_spouses(self, fids):
        """add spouse relationships
        :param fids: a set of fid
        """

        async def add(loop, rels):
            futures = set()
            for father, mother, relfid in rels:
                if (father, mother) in self._fam:
                    futures.add(
                        loop.run_in_executor(
                            None, self._fam[(father, mother)].add_marriage, relfid
                        )
                    )
            for future in futures:
                await future

        rels = set()
        for fid in fids & self._persons.keys():
            rels |= self._persons[fid].spouses
        loop = asyncio.get_event_loop()
        if rels:
            self.add_persons(
                set.union(*({father, mother} for father, mother, relfid in rels))
            )
            for father, mother, _ in rels:
                if father in self._persons and mother in self._persons:
                    self._persons[father].add_fams((father, mother))
                    self._persons[mother].add_fams((father, mother))
                    self.add_fam(father, mother)
            loop.run_until_complete(add(loop, rels))

    def add_children(self, fids):
        """add children relationships
        :param fids: a set of fid
        """
        rels = set()
        for fid in fids & self._persons.keys():
            rels |= self._persons[fid].children if fid in self._persons else set()
        children = set()
        if rels:
            self.add_persons(set.union(*(set(rel) for rel in rels)))
            for father, mother, child in rels:
                if child in self._persons and (
                    mother in self._persons
                    and father in self._persons
                    or not father
                    and mother in self._persons
                    or not mother
                    and father in self._persons
                ):
                    self.add_trio(father, mother, child)
                    children.add(child)
        return children

