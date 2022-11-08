#!/usr/bin/env python3

import asyncio,random

class Carte(object) :
    def __init__(self,symbole,valeur):
        self.symbole = symbole
        self.valeur = valeur
    
    def afficher(self):
        if self.valeur == 1:
            return ("--- As de "+self.symbole+" ---\n")
        if self.valeur == 11:
            return ("--- Valet de "+self.symbole+" ---\n")
        elif self.valeur == 12:
            return("--- Reine de "+self.symbole+" ---\n")
        elif self.valeur == 13:
            return("--- Roi de "+self.symbole+" ---\n")
        else:
            return("--- "+str(self.valeur)+" de "+self.symbole+" ---\n")

    async def nouveau_score(self,ancien_score):
        if self.valeur == 1 :
            if ancien_score + 11 > 21 :
                return int(ancien_score) + 1
        elif self.valeur == 11 or self.valeur == 12 or self.valeur == 13 :
            return int(ancien_score) + 10
        else:
            return int(ancien_score) + self.valeur

def packet_de_cartes():
    couleurs = ["Coeur","Carreau","Trefle","Pique"]
    deck = []
    for i in couleurs:
        for j in range(1,14):
            deck.append(Carte(i,j))
    return deck

async def piocher(deck):
    n = random.randint(0,len(deck)-1)
    carte = deck[n]
    deck.remove(carte)
    return carte,deck
    



class Table(object) :
    def __init__(self,nom):
        self.nom = nom
        self.personne = []
        self.tps = 0
        self.commence = False
        self.packet = packet_de_cartes()
        self.main_donneur = []

    def set_tps(self,tps):
        self.tps = tps
    
    def ajouter_personne(self,personne):
        self.personne.append(personne)

    def afficher(self):
        s = ("\nTable "+self.nom[:-2])
        for p in self.personne :
            s = s+("\t"+p+"\n")
        return s
    
    async def salle_attente(self):
        if self.commence == False :    
            self.commence = True
            while self.tps > 0 :
                if self.tps<=10 :
                    print(self.tps)
                await asyncio.sleep(1)
                self.set_tps(self.tps-1)
        else :
            await asyncio.sleep(self.tps)



def get_table(tab,nom):
    for table in tab :
        if table.nom == nom :
            return table
    return -1



tables = []




async def croupier_blackjack(reader,writer):
    addr = writer.get_extra_info('peername')[0]
    bienvenue = f"Bienvenue croupier {addr} !\n"
    writer.write(bienvenue.encode())
    data = await reader.readline()
    command = data.decode()[:4]
    nom = data.decode()[4:]
    table = None
    if command=="NAME":
        table = Table(nom)
        tables.append(table)
    writer.write("OK\n".encode())

    data = await reader.readline()
    command = data.decode()[:4]
    temps = data.decode()[4:]
    if command=="TIME":
        table.set_tps(int(temps))
    writer.write("OK\n".encode())
    


async def jouer(reader,writer,table):
    main = []
    score = 0
    score_donneur = 0
    for i in range (2):
        carte,table.packet = await piocher(table.packet)
        main.append(carte)
        score = await carte.nouveau_score(score)
        writer.write(carte.afficher().encode())
        carte_donneur,table.packet = await piocher(table.packet)
        table.main_donneur.append(carte_donneur)
        score_donneur = await carte_donneur.nouveau_score(score_donneur)
    #Montrer la première carte du donneur
    writer.write(("Premiere carte du donneur : \n"+table.main_donneur[0].afficher()).encode())
    #demander aux joueurs s'il veulent piocher
    #faire cette demande en boucle
    while score <= 21 :
        writer.write(".\n".encode())
        data = await reader.readline()
        choix = data.decode().split()
        if (choix[0]=="MORE"):
            if (choix[1] == '1'):
                carte,table.packet = await piocher(table.packet)
                main.append(carte)
                writer.write(carte.afficher().encode())
                score = await carte.nouveau_score(score)
            else :
                break
    #si tout les joueurs ont fini :
    if score>21 : 
        writer.write("Vous avez perdu !\n".encode())
    else:
        #si arrêt montrer la deuxieme carte du donneur et le donneur complète sa main
        #while en fonction du score du donneur
        while score_donneur <= 17 :
            carte,table.packet = await piocher(table.packet)
            table.main_donneur.append(carte)
            score_donneur = await carte.nouveau_score(score_donneur)
            print("le score du donneur : ",score_donneur,"\n")
             
        writer.write(("Deuxieme carte du donneur : \n"+table.main_donneur[1].afficher()).encode())
        #calcule du gagnant
        writer.write(("Le score du donneur = "+score_donneur+"\n").encode())
        if score>score_donneur :
            writer.write("Vous avez gagné !\n".encode())
        elif score==score_donneur:
            writer.write("Vous avez fait une égalité !\n".encode())
        else :
            writer.write("Vous avez perdu !\n".encode())
    #fin
    writer.write("END\n".encode())
    



async def joueur_blackjack(reader,writer):
    addr = writer.get_extra_info('peername')[0]
    bienvenue = f"Bienvenue joueur {addr} !\n"
    writer.write(bienvenue.encode())
    data = await reader.readline()
    command = data.decode()[:4]
    nom = data.decode()[4:]
    if command=="NAME":
        table = get_table(tables,nom)
        if table != -1 and table.tps != 0 :
            table.ajouter_personne(addr)
            await table.salle_attente()
            await jouer(reader,writer,table)
            tables.remove(table)
        else :
            message = "Impossible de rejoindre cette table. Fin du programme !\n"
            writer.write(message.encode())
            writer.write("END\n".encode())


async def blackjack_server():
    #start the server
    server_croupier = await asyncio.start_server(croupier_blackjack,'0.0.0.0',668)
    server_joueur = await asyncio.start_server(joueur_blackjack,'0.0.0.0',667)
    addr_c = server_croupier.sockets[0].getsockname()
    print(f'Serving on {addr_c}')
    addr_j = server_joueur.sockets[0].getsockname()
    print(f'Serving on {addr_j}')
    async with server_croupier,server_joueur:
        await server_croupier.serve_forever()
        await server_joueur.serve_forever()

if __name__ == '__main__':
    asyncio.run(blackjack_server())