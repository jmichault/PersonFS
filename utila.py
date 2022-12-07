def getfsid(grPersono) :
  if not grPersono :
    return ''
  for attr in grPersono.get_attribute_list():
    if attr.get_type() == '_FSFTID':
      return attr.get_value()
  return ''


