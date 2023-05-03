This is an extension to interface gramps with familysearch.com. it's made of :

* a gramplet to compare your individual with that of FamilySearch. From this gramplet, you can also search on familysearch, consult potential duplicates found by FamilySearch, copy events to or from FamilySearch, import ancestors and descendants.
* an import module accessible via the “Tools” menu --> “Modification of the family tree” --> “Import of FamilySearch data”
* a comparison module accessible via the "Tools" menu --> "Modification of the family tree" --> "FamilySearch: compare"

To be able to use the extension you need a familysearch account, this will be requested when launching the gramplet, as well as the associated password.

#Installation
## prerequisites
The gramplet uses “requests” and “gedcomx-v1” (>=1.0.12) python modules.  
Therefore this plugin cannot be used with the official AIO distribution of gramps.  

You can install 'requests' and 'gedcomx-v1' manually, or let the gramplet install them automatically (requires pip).  
For windows, you can try experimental AIO distribution [here](https://github.com/jmichault/gramps-aio/releases) ).


## loading the zip
On the [project homepage](https://github.com/jmichault/PersonFS), click “Releases” (right), and in “Assets” choose the PersonFS.zip file).
Then extract the zip to Gramps plugins folder (~/.gramps/gramps51/plugins for gramps version 5.1)
(or %APPDATA%\gramps\gramps51\plugins for windows).

## with git
In a terminal, run the following commands:

```
cd ~/.gramps/gramps51/plugins
git clone https://github.com/jmichault/PersonFS.git
```
(note: to be adapted if gramps is not in version 5.1)

# the gramplet
## enable
While positioned on the Individuals panel, click on the drop-down menu to the right of the tabs (small “v” button) and choose “Add a Gramplet”, then “FS”.
Once done, a new “FS” tab is added.

## use

The gramplet allows you to compare your gramps person record with that of familysearch for the following information:
* surname/first name
* Date and place of birth
* date and place of baptism
* date and place of death
* date and place of burial
* the parents (surname/first name, years of birth and death)
* the couple
* children
* other events

The first column allows you to quickly visualize which data is not in phase:
* green = in phase (warning: for people only familysearch identifiers are checked, for dates/places only dates are checked)
* red: discordant essential information. (essential information = surname/main first name, sex, dates of birth and death)
* orange: present on both sides, but not in phase.
* yellow: present only in gramps.
* dark yellow: present only in FamilySearch.

Note: the link with _familysearch_ is made using a key attribute _“\_FSFTID”_ and having the identification number _familysearch_ as its value.

Note: to limit the loading time, at launch the detailed data of the spouses and children are not loaded. You can upload them by clicking on the “Upload spouses and children” button.

Dates are displayed whenever possible using the [_«formal»_](https://github.com/FamilySearch/gedcomx/blob/master/specifications/date-format-specification.md) format _familysearch_.

From the gramplet, you can also:
* Access the complete FamilySearch file by clicking on the Identification number (on the right of the screen), which launches your Internet browser.
* Launch a search on FamilySearch, which also allows you to associate your file with an existing familysearch file, or to create the person in FamilySearch if you do not find a match.
  * Attention: the person is created with the minimum of information: surname, first name. It is up to you to transfer the other information, and to link it to its children, spouses, parents.
* Consult the potential duplicates offered by FamilySearch, and from there you can access the complete FamilySearch file of the potential duplicate, or access the FamilySearch merge screen.
* launch the import module to import the FamilySearch data of your individual, and possibly the ancestors and descendants.
* copy names or events to or from FamilySearch by checking the last column, then using the context menu (right click).
  * caution: places that are not standardized in FamilySearch are not copied.
* change individual by double-clicking on the corresponding line.
* edit an event of the person by double-clicking on the corresponding line.

# the import module
You can launch it either from the menu or from the gramplet.
You just have to enter:
* the starting FamilySearch ID
* the number of generations of ancestors to load.
* the number of descendant generations.
* check "Do not re-import existing people" if you want to protect your existing people.
* check "Add spouses" if you want to load the spouses of all persons as well.
  (note: if you load descending generations, the spouses will necessarily be loaded)
* check "Add sources" if you want to load attached sources as well.
* check "Add notes" if you want to load attached notes as well.

Then click on the “Import” button

# the comparison module
* this tool will browse all individuals and position the following labels:
  * FS\_Identa: all compared elements are synchronous
  * FS\_Esenco: there is essential information to be synchronized (main name/surname, dates of birth and death).
  * FS\_Nomo: there is a name (other than the main one) to synchronize.
  * FS\_Gepatro: there is a parent to synchronize.
  * FS\_Familio: there is a spouse or a child to synchronize.
  * FS\_Fakto: there is an event to synchronize (other than birth or death).
  * FS\_Dup: potential duplicate detected by FamilySearch.
  * FS\_Dok: Documents to be bound detected by FamilySearch.
  * FS\_Gramps: changed in gramps since the last time the FS\_Konf tag was set, or everything was correct (FS\_Identa tag and no others)
  * FS\_FS: changed in FamilySearch since the last time the FS\_Konf tag was set, or everything was correct (FS\_Identa tag and no others)
* moreover the label FS\_Konf can be positioned from the gramplet: synchro not perfect but marked compliant.
* the tool can be interrupted during processing.

# suggested working method.
## Create filters
1. create a filter selecting the individuals you are interested in, for example: "ancestors over x generations"

## startup
1. activate the gramplet on the Individuals view
2. go to your stem individual, and link it:
  * with the search button, try to find it in familysearch
  * if you find it: use the Link button.
  * if you can't find it: use the Add button.
3. do the same with his parents, then his parents' parents...

## regularly
1. run the compare module
2. filter the “ancestors” with the label FS_Gepatro
  * sync parents
3. filter "ancestors" with the label FS_Familio
  * sync kids
4. do the same with the labels FS_Esenco, FS_Fakto, FS_Nomo
5. filter the “ancestors” with the label FS_Dok
  * click on the link leading to FamilySearch and check the documents offered.
6. filter the “ascendants” with the label FS_Dup
  * click the “View FS duplicates” button and check whether to merge them.
7. Check out the locations. The FamilySearch data transfer most likely created duplicates: merge them with your pre-existing locations, or bring them up to your own standards.

