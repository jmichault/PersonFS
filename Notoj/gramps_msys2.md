
d'abord suivre :  
https://gramps-project.org/wiki/index.php/Gramps_for_Windows_with_MSYS2
sauf : ne pas installer msys/gcc

note : l'installation de fontconfig échoue. Pas grave ?  

ensuite :

```
pacman -S mingw-w64-x86_64-python3-requests mingw-w64-x86_64-python3-pip mingw-w64-x86_64-python3-packaging unzip
pip install gedcomx-v1
cd ~/grampsdev
git checkout v5.1.5
python3 -m build
cd gramps/plugins
wget https://github.com/jmichault/PersonFS/releases/download/v1.4.4/PersonFS.zip
unzip PersonFS
```
