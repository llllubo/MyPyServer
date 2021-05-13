# Preklad domenovych mien
##### Tema:     klient-server aplikacia
##### Autor:    Lubos Bever, xvajco00
##### Datum:    08.03.2020
##### Predmet:  IPK
Skript vytvoreny v jazyku Python _(/src/server.py)_ je schopny vytvorit server a cakat na klienta. Klient sa pripoji na server, ktory bezi na konkretnom porte a zasle na server poziadavku _GET_ alebo _POST_. Po vybaveni poziadavky sa server korektne ukonci.
### Pouzitie
```bash
make run PORT=5353
```
Server sa spusta pomocou skriptu _"/Makefile"_ prikazom vyssie. Prikaz zabezpeci spustenie skriptu _"/src/server.py"_, ktory nasledne vytvory server komunikujuci cez zadany port.
##### Operacia GET
```bash
curl localhost:5353/resolve?name=www.google.com\&type=A
```
Server komunikujuci s klientom na porte _5353_ prelozi domenove meno _www.google.com_ na IPv4 adresu odpovedou 
```bash
HTTP/1.1 200 OK
Content-Length: 

www.google.com:A=216.58.201.68
```
V pripade nenajdenia odpovedajucej IPv4 adresy, zasle serveru informaciu **_"404 Not Found"_**. Taktiez je mozne ziadat o preklad IPv4 adresy na domenove meno, napriklad:
```bash
curl localhost:5353/resolve?name=147.229.14.131\&type=PTR
```
V pripade zle zadaneho poziadavku, resp. neznamych parametrov, server konci so spravou **_"400 Bad Request"_** odoslanou klientovy.
##### Operacia POST
```bash
curl --data-binary @queries.txt -X POST http://localhost:5353/dns-query
```
Server komunikujuci s klientom opat na porte 5353 prelozi zadanu IPv4 adresu _(typ poziadavku: PTR)_ na prislusne domenove meno, alebo v pripade zadania domenoveho mena, prelozi domenu na jemu prisluchajucu IPv4 adresu _(typ poziadavku: A)_. Zoznam poziadavkov sa nachadza v subore _queries.txt_, ktory obsahuje poziadavky v tvare
```bash
DOMENOVE_MENO:A
```
alebo
```bash
IPv4_ADDR:PTR
```
kazdy na samostatnom riadku. Odpovedou je potom zoznam, napriklad:
```bash
147.229.14.131:PTR=dhcpz131.fit.vutbr.cz
www.fit.vutbr.cz:A=147.229.9.23
```
Ak sa nejaky poziadavok nepodarilo vybavit, server ho odignoruje a pokracuje dalej. Ak nie je mozne vybavit ziadnu poziadavku, server vrati chybu **_"404 Not Found"_** alebo **_"400 Bad Request"_**, ak subor obsahoval nejake nezname parametre.
