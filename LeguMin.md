
Ĉi tio estas [_gramplet_](https://www.gramps-project.org/wiki/index.php/Gramplets) por interfacigi _gramps_ kun _familysearch.com_.

En la nuna stato ĝi estas tre limigita, ĝi permesas kompari la dosieron de via persono gramps kun tiu de familysearch por la sekvaj informoj:  
* familia nomo/antaŭnomo
* Dato kaj Loko de Naskiĝo
* dato kaj loko de bapto
* dato kaj loko de morto
* dato kaj loko de entombigo
* familia nomo/antaŭnomo de patro kaj patrino

la ligo kun _familysearch_ estas farita per ŝlosila atributo _“\_FSFTID”_ kaj havanta la identigan numeron _familysearch_ kiel sia valoro.  
Notu: la python-skripto [_GetMyAncestors_]() plenigas ĉi tiun atributon.

Datoj estas montrataj kiam ajn eblas uzante la formato [_“formal”_](https://github.com/FamilySearch/gedcomx/blob/master/specifications/date-format-specification.md) de _familysearch_.

Por povi uzi la gramplet vi bezonas _familysearch_-konton, ĉi tio estas enigota en la preferoj, same kiel la rilata pasvorto.

# instalado
## antaŭkondiĉoj
La gramplet uzas la "petojn" kaj "gedcomx-v1" (>=1.0.12) python-modulojn.  
Tial ĉi tiu kromaĵo ne povas esti uzata kun la oficiala AIO-distribuo de gramps.  

Vi povas instali 'requests' kaj 'gedcomx-v1' permane, aŭ lasi la gramplet instali ilin aŭtomate (postulas pip).  

Por fenestroj, vi povas provi la AIO-distribuon kiu venas kun PersonFS.  

## ŝarĝante la zipon
Sur la [hejmpaĝo de la projekto] (https://github.com/jmichault/PersonFS), alklaku "Eldonoj" (dekstre), kaj en "Aktivoj" elektu la dosieron PersonFS.zip).  
Tiam ĉerpi la zip al dosierujo de Gramps-kromaĵoj (~/.gramps/gramps51/plugins por gramps-versio 5.1)  

## kun git
En terminalo, rulu la jenajn komandojn:  

```
cd ~/.gramps/gramps51/plugins
git clone https://github.com/jmichault/PersonFS.git
```
(noto: adaptenda se gramps ne estas en versio 5.1)


