#!/usr/bin/env python3

import sys
import socket
import re


PORT = sys.argv[1]


def choose_response(code):
    switcher = {
        400:
            "400 Bad Request\n",
        404:
            "404 Not Found\n",
        405:
            "405 Method Not Allowed\n",
        500:
            "500 Internal Server Error\n"
    }
    return switcher.get(code, "200 OK\n")



def make_header(http, errCode = 200):
    hdr = http + ' ' + choose_response(errCode)
    return hdr



def make_content_len(value):
    hdr = 'Content-Length: '
    try:
        strVal = str(value)
        hdr += strVal + "\n\n"

    except:
        hdr = make_header(500)

    finally:
        return hdr



def convert_port(port):
    try:
        port = int(port)
        return port
   
    except:
        hdr = make_header(500)
        return hdr

    else:
        if not (port > 0 and port < 65535):
            raise Exception("ERROR. Chybna/nespravna hodnota portu.\n")


def send_to_client():
    global resStr, conn
    resStr = resStr.encode('ASCII', 'strict')
    conn.sendall(resStr)


######################### HLAVNA CAST SKRIPTU #########################

# Kontrola hodnoty portu.
PORT = convert_port(PORT)

# Vytvorenie a spojenie serveru s klientom.
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', PORT))
    s.listen()
except:
    raise Exception("ERROR. Nepodarilo sa vytvorit socket.\n")

# Server bezi.
while True:

    conn, addr = s.accept()

    # Prijatie spravy od klienta.
    fromClient = conn.recv(4096)
    fromClient = fromClient.decode('ASCII', 'strict') 
    if not fromClient:
        break

    # Inicializacia dolezitych globalnych premennych.
    resStr = ''
    domainPattern = r'(?:[A-Za-z0-9](?:[A-Za-z0-9-]{,61}[A-Za-z0-9])?\.)+[A-Za-z0-9][A-Za-z0-9-]{,61}[A-Za-z0-9]'
    IPv4Pattern = r'(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])'

    # Spracovanie stringu od klienta na pole slov.
    fromClient = fromClient.split()

    # Detekovany GET.
    if fromClient[0] == 'GET':#fromClient[0]

        data = fromClient[1].split('?')

        # Kontrola vstupneho URL '/resolve' (chyba 400 a ukoncenie servera).
        if data[0] != '/resolve':
            resStr = make_header(fromClient[2], 400)
            resStr += "\n"
            send_to_client()
            conn.close()
            continue

        # Ziskanie parametrov 'name' a 'type'.
        names = re.findall(r'(?<=name=)' + domainPattern + r'|(?<=name=)' + IPv4Pattern, data[1])
        types = re.findall(r'(?<=type=)(?:A|PTR)', data[1])
        
        data = data[1].split('&')

        # Podrobna kontrola poziadavku (odchyti napr. nnname=...).
        rightDataCntr = 0
        i = 0
        while i < len(data):
            if re.fullmatch(r'name=' + domainPattern, data[i]) != None:
                rightDataCntr += 1
            elif re.fullmatch(r'name=' + IPv4Pattern, data[i]) != None:
                rightDataCntr += 1
            elif re.fullmatch(r'type=A', data[i]) != None:
                rightDataCntr += 1
            elif re.fullmatch(r'type=PTR', data[i]) != None:
                rightDataCntr += 1
            i += 1

        # Chyba 400. V poziadavke sa nachadzaju nezname parametre.
        if (len(data) > (len(names) + len(types))) or (rightDataCntr < len(data)):
            resStr = make_header(fromClient[2], 400)
            resStr += "\n"
            send_to_client()
            conn.close()
            continue

        # Prekladana bude IPv4 adresa na domenove meno.
        if re.fullmatch(IPv4Pattern, names[0]) != None:
            # Kontrola, ci ide o spravny typ poziadavku (PTR).
            if len(types) and re.fullmatch(r'PTR', types[0]) != None:
                try:
                    gotDomain = socket.gethostbyaddr(names[0])
                except:
                    resStr = make_header(fromClient[2], 404)
                    resStr += "\n"
                    send_to_client()
                    conn.close()
                    continue
                resStr = make_header(fromClient[2])
                result = names[0] + ':' + types[0] + '=' + gotDomain[0] + '\n'
                resStr += make_content_len(len(result)) + result
            # Koniec s chybou 400.
            else:
                resStr = make_header(fromClient[2], 400)
                resStr += "\n"
                send_to_client()
                conn.close()
                continue

        # Prekladane bude domenove meno na IPv4 adresu.
        elif re.fullmatch(domainPattern, names[0]) != None:
            # Kontrola, ci ide o spravny typ poziadavku (A).
            if len(types) and re.fullmatch(r'A', types[0]) != None:
                try:
                    gotIP = socket.gethostbyname(names[0])
                except:
                    resStr = make_header(fromClient[2], 404)
                    resStr += "\n";
                    send_to_client()
                    conn.close()
                    continue
                resStr = make_header(fromClient[2])
                result = names[0] + ':' + types[0] + '=' + gotIP + '\n'
                resStr += make_content_len(len(result)) + result
            # Koniec s chybou 400.
            else:
                resStr = make_header(fromClient[2], 400)
                resStr += "\n"
                send_to_client()
                conn.close()
                continue


    # Detekovany POST.
    elif fromClient[0] == 'POST':

        # Kontrola vstupneho URL '/dns-query' (chyba 400).
        if fromClient[1] != '/dns-query':
            resStr = make_header(fromClient[2], 400)
            resStr += "\n"
            send_to_client()
            conn.close()
            continue

        mustExit = False
        err = 200
        for i in range(13, len(fromClient)):
            # Naslo sa IPv4:TYPE
            if re.fullmatch(IPv4Pattern + r':PTR', fromClient[i]) != None:
                dataParts = fromClient[i].split(':')
                try:
                    gotDomain = socket.gethostbyaddr(dataParts[0])
                except:
                    if err == 200:
                        err = 404
                else:
                    resStr += dataParts[0] + ':' + dataParts[1] + '=' + gotDomain[0] + '\n'
            # Naslo sa DOMAIN:TYPE
            elif re.fullmatch(domainPattern + r':A', fromClient[i]) != None:
                dataParts = fromClient[i].split(':')
                try:
                    gotIP = socket.gethostbyname(dataParts[0])
                except:
                    if err == 200:
                        err = 404
                else:
                    resStr += dataParts[0] + ':' + dataParts[1] + '=' + gotIP + '\n'
            # Nasiel sa prazdny riadok (chyba 400).
            elif re.fullmatch(r'\\r\\n|\\n', fromClient[i]) != None:
                resStr = make_header(fromClient[2], 400)
                resStr += "\n"
                send_to_client()
                mustExit = True
                break

            # Nasiel sa zly parameter (chyba 400).
            else:
                err = 400

        # Okamzite ukoncenie behu servera s chybou.
        if mustExit == True:
            conn.close()
            continue

        # Bol zadany len jeden dotaz, ktory vykazuje chybu alebo ich bolo viac a ani jeden nebol OK.
        if (err != 200) and (len(resStr) == 0):
            resStr = make_header(fromClient[2], err)
            resStr += "\n"
            send_to_client()
            conn.close()
            continue

        # Uspesny koniec, vracia prelozene poziadavky.
        if len(resStr) != 0:
            resStr = make_header(fromClient[2]) + make_content_len(len(resStr)) + resStr

    # Detekovana neznama operacia (chyba 405).
    else:
        resStr = make_header(fromClient[2], 405)
        resStr = "\n"
        send_to_client()
        conn.close()
        continue

    # Poslanie spravy klientovy (200 OK).
    resStr = resStr.encode('ASCII', 'strict')
    conn.sendall(resStr)

# Server konci, socket sa uzavrie.
conn.close()
s.close()
