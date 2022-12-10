
# les dates «formal»

5 types possibles :
* date simple
* intervalle de dates
  * peut être construit avec 2 dates ou 1 date + 1 durée
  * peut être fermé ou ouvert(l'une des dates manque : = avant ou après)
* date récurrente
  * peut être construite avec 2 dates ou 1 date + 1 durée
* date approximative
* intervalle approximatif

## date simple :

* format :
    ±YYYY[-MM[-DD[Thh:[mm[:ss]][±hh[:mm]|Z]]]]
* ±YYYY est obligatoire, YYYY est complété par des zéros à gauche si nécessaire
* ±hh[:mm] : décalage horaire par rapport à UTC.
* Z : UTC

## durée :
* format :
    PnnnnYnnMnnDTnnHnnMnnS
* ne peut pas être utilisé seule.
* exemple :
    P17Y6M2D = 17 ans 6 mois 2 jours

## intervalle de dates :
* indiqué par la présence d'un / (et l'absence d'un R initial)
* 4 types :
### intervalle avec deux dates simples :
  {date1}/{date2}
### intervalle avec une date et une durée :
  {date1}/durée
### intervalle sans fin (= après x) :
  {date}/
### intervalle sans début (= avant x) :
  /{date}

## dates récurrentes
* format avec 2 dates
    R[n]/{date1}/{date2}
* format avec 1 date et une durée
    R[n]/{date1}/{durée}

## date approximative
  A{date}

## intervalle approximatif
  A{intervalle}
