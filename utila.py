from gramps.gen.db import DbTxn
from gramps.gen.lib import Attribute, EventRoleType, Date
from gramps.gen.lib.date import gregorian

from gramps.gen.const import GRAMPS_LOCALE as glocale

try:
    _trans = glocale.get_addon_translator(__file__)
except ValueError:
    _trans = glocale.translation
_ = _trans.gettext

def fsdato_al_gr( fsDato) :
  if fsDato:
    grDato = Date()
    grDato.set_calendar(Date.CAL_GREGORIAN)
    jaro=monato=tago= 0
    if fsDato.formal :
      if fsDato.formal.unuaDato and fsDato.formal.unuaDato.jaro:
        jaro = fsDato.formal.unuaDato.jaro
        monato = fsDato.formal.unuaDato.monato
        tago = fsDato.formal.unuaDato.tago
      elif fsDato.formal.finalaDato and fsDato.formal.finalaDato.jaro:
        jaro = fsDato.formal.finalaDato.jaro
        monato = fsDato.formal.finalaDato.monato
        tago = fsDato.formal.finalaDato.tago
      if fsDato.formal.proksimuma :
        grDato.set_modifier(Date.MOD_ABOUT)
      if fsDato.formal.gamo :
        if not fsDato.formal.unuaDato or not fsDato.formal.unuaDato.jaro :
          grDato.set_modifier(Date.MOD_BEFORE)
        elif not fsDato.formal.finalaDato or not fsDato.formal.finalaDato.jaro :
          grDato.set_modifier(Date.MOD_AFTER)
        else :
          grDato.set_modifier(Date.MOD_RANGE)
          if fsDato.formal.finalaDato and fsDato.formal.finalaDato.jaro :
            jaro2 = fsDato.formal.finalaDato.jaro
            monato2 = fsDato.formal.finalaDato.monato
            tago2 = fsDato.formal.finalaDato.tago
    if grDato.modifier == Date.MOD_RANGE :
      grDato.set(value=(tago, monato, jaro, 0, tago2, monato2, jaro2, 0),text=fsDato.original or '',newyear=Date.NEWYEAR_JAN1)
    else : 
      grDato.set(value=(tago, monato, jaro, 0),text=fsDato.original or '',newyear=Date.NEWYEAR_JAN1)
  else : grDato = None
  return grDato

def grdato_al_formal( dato) :
  """
  " konvertas gramps-daton al «formal» dato
  "   «formal» dato : <https://github.com/FamilySearch/gedcomx/blob/master/specifications/date-format-specification.md>
  """
  res=''
  gdato = gregorian(dato)
  if gdato.modifier == Date.MOD_ABOUT :
    res = 'A'
  elif gdato.modifier == Date.MOD_BEFORE:
    res = '/'
  if gdato.dateval[Date._POS_YR] < 0 :
    res = res + '-'
  else :
    res = res + '+'
  if gdato.dateval[Date._POS_DAY] > 0 :
    val = "%04d-%02d-%02d" % (
                gdato.dateval[Date._POS_YR], gdato.dateval[Date._POS_MON],
                gdato.dateval[Date._POS_DAY])
  elif gdato.dateval[Date._POS_MON] > 0 :
    val = "%04d-%02d" % (
                gdato.dateval[Date._POS_YR], gdato.dateval[Date._POS_MON])
  elif gdato.dateval[Date._POS_YR] > 0 :
    val = "%04d" % ( gdato.dateval[Date._POS_YR] )
  else :
    res = gdato.text
    val=''
  res = res+val
  if gdato.modifier == Date.MOD_AFTER:
    res = res + '/'
  if gdato.modifier == Date.MOD_RANGE:
    res = res + '/'
    if gdato.dateval[Date._POS_RYR] < 0 :
      res = res + '-'
    else :
      res = res + '+'
    if gdato.dateval[Date._POS_RDAY] > 0 :
      val = "%04d-%02d-%02d" % (
                gdato.dateval[Date._POS_RYR], gdato.dateval[Date._POS_RMON],
                gdato.dateval[Date._POS_RDAY])
    elif gdato.dateval[Date._POS_RMON] > 0 :
      val = "%04d-%02d" % (
                gdato.dateval[Date._POS_RYR], gdato.dateval[Date._POS_RMON])
    elif gdato.dateval[Date._POS_RYR] > 0 :
      val = "%04d" % ( gdato.dateval[Date._POS_RYR] )
    else:
      val = ''
    res = res+val
  # FARINDAĴOJ : range ?  estimate ? calculate ? heure ?
  
  return res

def get_fsftid(grObj) :
  if not grObj :
    return ''
  for attr in grObj.get_attribute_list():
    if attr.get_type() == '_FSFTID':
      return attr.get_value()
  return ''

def get_fsfact(person, fact_tipo):
  """
  " Liveras la unuan familysearch fakton de la donita tipo.
  """
  for fact in person.facts :
    if fact.type == fact_tipo :
      return fact
  return None

def get_grevent(db, person, event_type):
  """
  " Liveras la unuan gramps eventon de la donita tipo.
  """
  if not person:
    return None
  for event_ref in person.get_event_ref_list():
    if int(event_ref.get_role()) == EventRoleType.PRIMARY:
      event = db.get_event_from_handle(event_ref.ref)
      if event.get_type() == event_type:
        return event
  return None

def ligi_gr_fs(db,grPersono,fsid):
  attr = None
  with DbTxn(_("Aldoni FamilySearch ID"), db) as txn:
    for attr in grPersono.get_attribute_list():
      if attr.get_type() == '_FSFTID':
        attr.set_value(fsid)
        break
    if not attr or attr.get_type() != '_FSFTID' :
      attr = Attribute()
      attr.set_type('_FSFTID')
      attr.set_value(fsid)
      grPersono.add_attribute(attr)
    db.commit_person(grPersono,txn)
    db.transaction_commit(txn)
