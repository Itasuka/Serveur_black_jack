#!/usr/bin/env python3
# -*- coding: utf-8 -

from sys import argv
from socket import gethostbyname
import asyncio

async def sndrcv(reader,writer,msg):
    """envoie le message [msg] au serveur et affiche la réponse"""
    if msg is not None:
        writer.write(msg.encode() + b"\r\n")
    data = await reader.readline()
    print (data.decode().strip())
    return data.decode().strip()

def getint(msg):
    """demande une valeur entière à l'utilisateur"""
    while True:
        try:
            y = int(input(msg))
            break
        except ValueError:
            print("Oups!  Réessaie avec un nombre valide...")
    return(y)

    
async def blackjack_client(server):
    reader, writer = await asyncio.open_connection(server, 667)
    await sndrcv(reader,writer,None)
    name = input("À quelle table voulez-vous vous connecter ?\n")
    s = await sndrcv(reader,writer,"NAME "+name)
    while s.strip() != "END":
        if s == '.':
            more = getint("Voulez-vous une carte supplémentaire ? 1 pour oui, 0 pour non.\n")
            while more not in range(2):
                print("Une valeur parmi 0 et 1 est attendue.\n")
                more = getint("Voulez-vous une carte supplémentaire ? 1 pour oui, 0 pour non.\n")
            s = await sndrcv(reader,writer,"MORE "+str(more))
        else :
            s = await sndrcv(reader,writer,None)
        
if __name__ == '__main__':
    if len(argv)!=2:
        print("usage: {scriptname} server".format(scriptname= argv[0]))
        exit(1)
    sname=argv[1]
    server=gethostbyname(sname)
    print("connecting to :", sname, server)
    asyncio.run(blackjack_client(server))
    
