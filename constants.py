
MAX_PERSONS = 200

from gramps.gen.const import GRAMPS_LOCALE as glocale
try:
    _trans = glocale.get_addon_translator(__file__)
except ValueError:
    _trans = glocale.translation
_ = _trans.gettext

# Subject to change: see https://www.familysearch.org/developers/docs/guides/facts
#   kaj https://github.com/FamilySearch/gedcomx/blob/master/specifications/fact-types-specification.md
from gramps.gen.lib import EventType
from gramps.gen.lib import PlaceType

GEDCOMX_GRAMPS_FAKTOJ = {
  "http://gedcomx.org/Adoption": EventType.ADOPT,
  "http://gedcomx.org/AdultChristening": EventType.ADULT_CHRISTEN,
  "http://gedcomx.org/Annulment": EventType.ANNULMENT,
  "http://gedcomx.org/Baptism": EventType.BAPTISM,
  "http://gedcomx.org/BarMitzvah": EventType.BAR_MITZVAH,
  "http://gedcomx.org/BatMitzvah": EventType.BAS_MITZVAH,
  "http://gedcomx.org/Birth": EventType.BIRTH,
  "http://gedcomx.org/Blessing": EventType.BLESS,
  "http://gedcomx.org/Burial": EventType.BURIAL,
  "http://gedcomx.org/Census": EventType.CENSUS,
  "data:,http://gedcomx.org/Census": EventType.CENSUS,
  "http://gedcomx.org/Christening": EventType.CHRISTEN,
  "http://gedcomx.org/CommonLawMarriage": EventType.MARR_ALT,
  "http://gedcomx.org/Confirmation": EventType.CONFIRMATION,
  "http://gedcomx.org/Cremation": EventType.CREMATION,
  "http://gedcomx.org/Death": EventType.DEATH,
  "http://gedcomx.org/Divorce": EventType.DIVORCE,
  "http://gedcomx.org/DivorceFiling": EventType.DIV_FILING,
  "http://gedcomx.org/Education": EventType.EDUCATION,
  "http://gedcomx.org/Emigration": EventType.EMIGRATION,
  "http://gedcomx.org/Engagement": EventType.ENGAGEMENT,
  "http://gedcomx.org/FirstCommunion": EventType.FIRST_COMMUN,
  "http://gedcomx.org/Graduation": EventType.GRADUATION,
  "http://gedcomx.org/Immigration": EventType.IMMIGRATION,
  "http://gedcomx.org/MilitaryService": EventType.MILITARY_SERV,
  "http://gedcomx.org/Marriage": EventType.MARRIAGE,
  "http://gedcomx.org/MarriageBanns": EventType.MARR_BANNS,
  "data:,Marriage Banns": EventType.MARR_BANNS,
  "http://gedcomx.org/MarriageContract": EventType.MARR_CONTR,
  "http://gedcomx.org/MarriageLicense": EventType.MARR_LIC,
  "http://gedcomx.org/Medical": EventType.MED_INFO,
  "http://gedcomx.org/Naturalization": EventType.NATURALIZATION,
  "http://gedcomx.org/NumberOfMarriages": EventType.NUM_MARRIAGES,
  "http://gedcomx.org/Occupation": EventType.OCCUPATION,
  "http://gedcomx.org/Ordination": EventType.ORDINATION,
  "http://gedcomx.org/Probate": EventType.PROBATE,
  "data:,http://gedcomx.org/Property": EventType.PROPERTY,
  "http://gedcomx.org/Religion": EventType.RELIGION,
  "http://gedcomx.org/Residence": EventType.RESIDENCE,
  "http://gedcomx.org/Retirement": EventType.RETIREMENT,
# gramps 5.2 :  "http://gedcomx.org/Stillbirth": EventType.STILLBIRTH,
  "data:,http://gedcomx.org/Will": EventType.WILL,
  "http://familysearch.org/v1/TitleOfNobility": EventType.NOB_TITLE,
#
  "http://familysearch.org/v1/LifeSketch": _('Vivskizo'),
  "data:,Birth Registration": _('Deklaro de naskiĝo'),
  "data:,Birth+Registration": _('Deklaro de naskiĝo'),
  "data:,Death Registration": _('Deklaro de morto'),
  "data:,Death+Registration": _('Deklaro de morto'),

}

#    MARR_SETTL = 2
#    CAUSE_DEATH = 20
#    DEGREE = 25
#    ELECTED = 27

# oftaj kutimaj eventoj
ALIAJ_FAKTOJ = {
  "data:,Profession": EventType.OCCUPATION,
  "data:,Baptism": EventType.CHRISTEN,
  "data:,Will": EventType.WILL,
  "data:,Testament": EventType.WILL,
}

def reversed_dict(d):
    return {val: key for key, val in d.items()}

GRAMPS_GEDCOMX_FAKTOJ = reversed_dict( GEDCOMX_GRAMPS_FAKTOJ )

GEDCOMX_GRAMPS_FAKTOJ.update(ALIAJ_FAKTOJ)

# familysearch tipolokoj : <https://www.familysearch.org/platform/places/types> .

GEDCOMX_GRAMPS_LOKOJ = {
  "https://www.familysearch.org/platform/places/types/580": PlaceType.COUNTRY
 ,"https://www.familysearch.org/platform/places/types/362": PlaceType.STATE
 ,"https://www.familysearch.org/platform/places/types/209": PlaceType.COUNTY
 ,"https://www.familysearch.org/platform/places/types/521": PlaceType.COUNTY
 ,"https://www.familysearch.org/platform/places/types/186": PlaceType.CITY
 ,"https://www.familysearch.org/platform/places/types/520": PlaceType.CITY
 ,"https://www.familysearch.org/platform/places/types/312": PlaceType.PARISH
 ,"https://www.familysearch.org/platform/places/types/323": PlaceType.LOCALITY
 ,"https://www.familysearch.org/platform/places/types/337": PlaceType.REGION
 ,"https://www.familysearch.org/platform/places/types/215": PlaceType.DEPARTMENT
 ,"https://www.familysearch.org/platform/places/types/308": PlaceType.NEIGHBORHOOD
 ,"https://www.familysearch.org/platform/places/types/221": PlaceType.DISTRICT
 ,"https://www.familysearch.org/platform/places/types/171": PlaceType.BOROUGH
 ,"https://www.familysearch.org/platform/places/types/201": PlaceType.MUNICIPALITY
 ,"https://www.familysearch.org/platform/places/types/376": PlaceType.TOWN
 ,"https://www.familysearch.org/platform/places/types/391": PlaceType.VILLAGE
 ,"https://www.familysearch.org/platform/places/types/266": PlaceType.HAMLET
 ,"https://www.familysearch.org/platform/places/types/38": PlaceType.FARM
 ,"https://www.familysearch.org/platform/places/types/23": PlaceType.BUILDING
 ,"https://www.familysearch.org/platform/places/types/61": PlaceType.BUILDING
 ,"https://www.familysearch.org/platform/places/types/115": PlaceType.BUILDING
 ,"https://www.familysearch.org/platform/places/types/142": PlaceType.BUILDING
}
