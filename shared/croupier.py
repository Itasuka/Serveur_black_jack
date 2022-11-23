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
    print(data.decode())

def getint(msg):
    """demande une valeur entière à l'utilisateur"""
    while True:
        try:
            y = int(input(msg))
            break
        except ValueError:
            print("Oups!  Réessaie avec un nombre valide...")
    return(y)


async def blackjack_croupier(server):
    reader, writer = await asyncio.open_connection(server, 668)
    await sndrcv(reader,writer,None)
    name = input("Nom de la table ?\n")
    await sndrcv(reader,writer,"NAME "+name)
    time = getint("Temps d'attente entre la connexion du premier joueur et le début de la partie ?\n")
    await sndrcv(reader,writer,"TIME "+str(time))
    

if __name__ == '__main__':
    if len(argv)!=2:
        print("usage: {scriptname} server".format(scriptname= argv[0]))
        exit(1)
    sname=argv[1]
    server=gethostbyname(sname)
    print("connecting to :", sname, server)
    asyncio.run(blackjack_croupier(server))
    
