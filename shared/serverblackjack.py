#!/usr/bin/env python3
# -*- coding: utf-8 -

import asyncio,random

#--------------CLASSE CARTE--------------
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



#--------------CLASSE JOUEUR--------------
class Joueur(object):
    def __init__(self):
        self.main = []
        self.score = 0
    


#--------------CLASSE TABLE--------------
class Table(object) :
    def __init__(self,nom):
        self.nom = nom
        self.joueurs_actifs = {}
        self.tps = 0
        self.commence = False
        self.paquet = paquet_de_cartes()
        self.main_donneur = []
        self.score_donneur = 0

    def set_tps(self,tps):
        self.tps = tps
    
    async def ajouter_joueur(self,joueur):
        self.joueurs_actifs[joueur] = False
    
    async def salle_attente(self,writer):
        writer.write(("La partie commence dans "+str(self.tps)+" secondes !\n").encode())
        if self.commence == False :    
            self.commence = True
            while self.tps > 0 :
                await asyncio.sleep(1)
                self.set_tps(self.tps-1)
        else :
            await asyncio.sleep(self.tps)

    def have_everyone_played(self):
        tab = self.joueurs_actifs
        for j in tab :
            if not tab[j] :
                return False
        return True



#--------------FONCTIONS POUR UTILISER LE PAQUET DE CARTES --------------
def paquet_de_cartes():
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
    


#--------------FONCTION CALCULANT LE NOUVEAU SCORE DU JOUEUR OU DU DONNEUR EN FONCTION DE SES CARTES--------------
async def nouveau_score(cartes):
    les_as=0
    res=0
    for c in cartes :
        if c.valeur!=1:
            if c.valeur==11 or c.valeur==12 or c.valeur==13 :
                res+=10
            else :
                res+=c.valeur
        else:
            les_as+=1
    if (les_as!=0) and ((res+11+(les_as-1))<=21) :
        res+=11
        les_as-=1
    res+=les_as
    return res



#--------------FONCTION POUR RECUPERER UNE TABLE DANS UN TABLEAU EN FONCTION DE SON NOM--------------
def get_table(tab,nom):
    for table in tab :
        if table.nom == nom :
            return table
    return -1


#--------------TABLES ACCESSIBLES CREEES PAR LES CROUPIERS--------------
tables = []



#--------------DEROULEMENT DU JEU DU BLACKJACK--------------
async def jouer(reader,writer,table,joueur):
    #DISTRIBUTION ET AFFICHAGE DES CARTES UNE A UNE AUX JOUEURS AINSI QU'AU DONNEUR
    for i in range (2):
        carte,table.paquet = await piocher(table.paquet)
        joueur.main.append(carte)
        joueur.score = await nouveau_score(joueur.main)
        writer.write(carte.afficher().encode())
        if len(table.main_donneur) < 2 :
            carte_donneur,table.paquet = await piocher(table.paquet)
            table.main_donneur.append(carte_donneur)
            table.score_donneur = await nouveau_score(table.main_donneur)
    
    #MONTRER LE SCORE DU JOUEUR AINSI QUE LA PREMIERE CARTE DU DONNEUR
    writer.write(("Votre score actuel : "+str(joueur.score)+"\n").encode())
    writer.write(("Premiere carte du donneur : \n"+table.main_donneur[0].afficher()).encode())

    #TANT QUE DES JOUEURS SONT ENCORE EN TRAIN DE PIOCHER
    while joueur in table.joueurs_actifs :
        writer.write(".\n".encode())
        data = await reader.readline()
        choix = data.decode().split()
        if (choix[0]=="MORE"):
            #LE JOUEUR PIOCHE
            if (choix[1] == '1'):
                carte,table.paquet = await piocher(table.paquet)
                joueur.main.append(carte)
                writer.write(carte.afficher().encode())
                joueur.score = await nouveau_score(joueur.main)
                writer.write(("Votre score actuel : "+str(joueur.score)+"\n").encode())
                table.joueurs_actifs[joueur] = True
                #SI SON NOUVEAU SCORE DEPASSE 21 IL EST ENLEVE DES JOUEURS QUI SONT EN TRAIN DE PIOCHER
                if joueur.score > 21:
                    table.joueurs_actifs.pop(joueur)
            #LE JOUEUR ARRETE DE PIOCHER
            else :
                table.joueurs_actifs.pop(joueur)
        #SI LE JOUEUR NE FAIT PLUS PARTI DES JOUEURS ACTIFS IL ATTEND QUE LES JOUEURS ACTIFS TERMINENT
        if joueur not in table.joueurs_actifs :
            writer.write("En attente des autres joueurs !\n".encode())
            while len(table.joueurs_actifs) > 0 :
                await asyncio.sleep(1)
        #SI LE JOUEUR A PIOCHE ET ATTEND QUE LES AUTRES JOUEURS PRENNENT LEUR DECISION
        while not table.have_everyone_played() :
            await asyncio.sleep(1)

    #QUAND TOUS LES JOUEURS ONT FINI DE PIOCHER
    #LE CROUPIER MONTRE SA 2EME CARTE ET PIOCHE EVENTUELLEMENT EN MONTRANT SES CARTES PIOCHEE AU FUR ET A MESURE
    writer.write(("Deuxieme carte du donneur : \n"+table.main_donneur[1].afficher()).encode())
    while table.score_donneur < 17 :
        carte,table.paquet = await piocher(table.paquet)
        table.main_donneur.append(carte)
        table.score_donneur = await nouveau_score(table.main_donneur)
    for i in range(2,len(table.main_donneur)):
        writer.write(("Le donneur pioche : \n"+table.main_donneur[i].afficher()).encode())

    #AFFICHAGE DU SCORE DU DONNEUR ET CALCUL DU GAGNANT
    writer.write(("Le score du donneur = "+str(table.score_donneur)+"\n").encode())
    #SI LE SCORE DU JOUEUR EST > A 21
    if joueur.score>21 : 
        writer.write("Vous avez perdu !\n".encode())
    elif table.score_donneur > 21 : 
        writer.write("Vous avez gagné !\n".encode())
    elif joueur.score>table.score_donneur :
        writer.write("Vous avez gagné !\n".encode())
    elif joueur.score==table.score_donneur:
        writer.write("Vous avez fait une égalité !\n".encode())
    else :
        writer.write("Vous avez perdu !\n".encode())
    #FIN DE LA PARTIE
    writer.write("END\n".encode())
    


#--------------FONCTION QUI PERMET AU CROUPIER DE CREER UNE TABLE DE JEU--------------
async def croupier_blackjack(reader,writer):
    addr = writer.get_extra_info('peername')[0]
    bienvenue = f"Bienvenue croupier {addr} !\n"
    writer.write(bienvenue.encode())
    data = await reader.readline()
    command = data.decode()[:4]
    nom = data.decode()[4:]
    table = None
    #LE CROUPIER CHOISI UN NOM DE TABLE
    if command=="NAME":
        table = Table(nom)
        tables.append(table)
    writer.write("OK\n".encode())

    data = await reader.readline()
    command = data.decode()[:4]
    temps = data.decode()[4:]
    #LE CROUPIER CHOISI LE TEMPS D'ATTENTE AVANT LE DEBUT DE LA PARTIE
    if command=="TIME":
        table.set_tps(int(temps))
    writer.write("OK\n".encode())
    


#--------------FONCTION PERMETTANT AU JOUEUR DE REJOINDRE UNE TABLE EXISTANTE ET DE JOUER UNE PARTIE--------------
async def joueur_blackjack(reader,writer):
    addr = writer.get_extra_info('peername')[0]
    bienvenue = f"Bienvenue joueur {addr} !\n"
    writer.write(bienvenue.encode())
    data = await reader.readline()
    command = data.decode()[:4]
    nom = data.decode()[4:]
    #LE JOUEUR CHOISI LA TABLE QU'IL VEUT REJOINDRE EN FONCTION DE SON NOM
    if command=="NAME":
        table = get_table(tables,nom)
        #SI LA TABLE EXISTE ET QU'ELLE N'A PAS ENCORE COMMENCE DE PARTIE
        if table != -1 and table.tps != 0 :
            await table.salle_attente(writer)
            joueur = Joueur()
            await table.ajouter_joueur(joueur)
            #LANCEMENT DU JEU
            await jouer(reader,writer,table,joueur)
            #LA PARTIE EST TERMINEE ON SUPPRIME LA TABLE
            if table in tables:
                tables.remove(table)
        #LA TABLE N'EXISTE PAS OU A DEJA COMMENCE SA PARTIE
        else :
            message = "Impossible de rejoindre cette table. Fin du programme !\n"
            writer.write(message.encode())
            writer.write("END\n".encode())



async def blackjack_server():
    #START THE SERVER
    server_croupier = await asyncio.start_server(croupier_blackjack,'0.0.0.0',668)
    server_joueur = await asyncio.start_server(joueur_blackjack,'0.0.0.0',667)
    async with server_croupier,server_joueur:
        await server_croupier.serve_forever()
        await server_joueur.serve_forever()

if __name__ == '__main__':
    asyncio.run(blackjack_server())