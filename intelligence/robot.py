import time
import math
from intelligence.communicationRobot import CommunicationRobot
from cartographie.ligne import Ligne

#Define the colors of the year, must be in english for a proper display color
COULEUR_A="violet"
COULEUR_B="green"

#Starting position of the robot for each colors
COULEUR_A_X=150
COULEUR_A_Y=950
COULEUR_A_ANGLE=0

COULEUR_B_X=2850
COULEUR_B_Y=950
COULEUR_B_ANGLE=180

class Robot:

    def __init__(self,port,largeur,chercher,listPointInteret, fenetre=None):
        self.communication = CommunicationRobot(port)
        self.fenetre = fenetre
        self.largeur = largeur
        self.chercher = chercher
        self.listPointInteret = listPointInteret
        self.couleur=COULEUR_A
        self.ascenseurID = 6 #AX12 with id 6
        self.pinceAscenseurID = 4 #AX12 with id 4
        self.brasBalleID = 3 #AX12 with id 3
        self.chargeurPopCornID = 1 #AX12 with id 1
        self.brasBalayageID = 5 #AX12 with id 5
        self.porteGobletDroitID = 2 #AX12 with id 2
        self.startTime = time.time()

    def attendreDepart(self):
        if self.communication.portserie == '':
            self.startTime = time.time()
            self.couleur=COULEUR_B
            print("Le robot est "+self.couleur)
            self.x=COULEUR_B_X
            self.y=COULEUR_B_Y
            self.angle=COULEUR_B_ANGLE #0 degres =3 heures
            self.startX = self.x
            self.startY = self.y
            return True
        rcv = self.communication.recevoir()
        print rcv
        while(not rcv.__contains__("GO")):
            self.startTime = time.time()
            rcv = self.communication.recevoir()
            print rcv
            #check if we recieved the color
            if(rcv.__contains__("VERT")):
                self.couleur=COULEUR_A
                print("Le robot est "+self.couleur)
            if(rcv.__contains__("JAUNE")):
                self.couleur=COULEUR_B
                print("Le robot est "+self.couleur)

        #Set the initial positions
        if(self.couleur==COULEUR_A):
            self.x=COULEUR_A_X
            self.y=COULEUR_A_Y
            self.angle=COULEUR_A_ANGLE #0=3h
        else:
            self.x=COULEUR_B_X
            self.y=COULEUR_B_Y
            self.angle=COULEUR_B_ANGLE #180=9h

        print("Le robot est " + self.couleur + " a la position x:" + str(self.x) + " y:" + str(self.y) + " angle:" + str(self.angle))
        self.startTime = time.time()
        self.startX = self.x
        self.startY = self.y
        return True

    def getRunningTime(self):
        return time.time() - self.startTime

    def attendreMilliseconde(self,duree):
        time.sleep(float(duree)/1000.0);
        return True

    def aveugler(self):
         time.sleep(500/1000.0);
         self.communication.envoyer("A\r\n")
         time.sleep(500/1000.0);
         return True

    def rendreVue(self):
         time.sleep(500/1000.0);
         self.communication.envoyer("B\r\n")
         time.sleep(500/1000.0);
         return True

    def executer(self,action):
        tabParam=[]
        for param in action.tabParametres:
            tabParam.append(param.getValue())
        if hasattr(self,action.methode):
            return getattr(self,action.methode)(*tabParam) #Run the requested method
        else:
            print "ERREUR: La methode",action.methode,"n'existe pas!!!"
            return False

    def demarrageSecours(self): #blind the robot if he didn't move for the first 10 seconds
        if( (abs(self.x-self.startX) <= 100) and (abs(self.y-self.startY) <= 100) and (self.getRunningTime() > 10) ):
            self.aveugler()
            print "### BIG WARNING ###: demarrageSecours a ete active, verifier les seuils des capteurs de distance."
        return True

    def positionAtteinte(self,x,y,x1,y1,erreur):
        if( (abs(x-x1) <= erreur) and (abs(y-y1) <= erreur) ):
            return True
        return False

    def distanceAtteinte(self,dist1, angle1, dist2, angle2 , erreurDist, erreurAngle):
        if( (abs(dist1-dist2) <= erreurDist) and (abs(angle1-angle2) <= erreurAngle) ):
            return True
        return False


    def getAngleToDo(self,angle):
        res = angle - self.angle
        if res > 180:
            res = -360 + res
        if res < -180:
            res = 360 + res
        return res

    def seDeplacerXY(self,x,y,angle, vitesse=1):
        print "\t \t Deplacement: x:",x," y:",y," angle:",angle
        chemin = self.chercher.trouverChemin(self.x,self.y,x,y,self.listPointInteret)
        if chemin == None:
            print "\t \t Chemin non trouve"
            return False
        for ligne in chemin:
            if not self.seDeplacerDistanceAngle(ligne.getlongeur(),self.getAngleToDo(ligne.getAngle())):
                return False
            #print "\t \tDeplacement: distance:",str(ligne.getlongeur())," angle:",str(ligne.getAngle())
        if not self.seDeplacerDistanceAngle(0,self.getAngleToDo(angle),vitesse):
            return False
        if self.communication.portserie != '':
            return self.positionAtteinte(x, y, self.x, self.y,50)
        else:
            return True

    def updatePositionRelative(self,distance,angle):
        angleDiff=(angle+self.angle)*0.0174532925 #rad
        xprev=self.x
        yprev=self.y
        self.x += distance*math.cos(angleDiff)
        self.y += distance*math.sin(angleDiff)
        self.angle += angle
        if self.angle > 180:
            self.angle = -360 + self.angle
        if self.angle < -180:
            self.angle = 360 + self.angle
        if self.fenetre != None:
            ligne = Ligne("",xprev,yprev,self.x,self.y,"blue")
            ligne.dessiner(self.fenetre)

    def seDeplacerDistanceAngle(self,distance,angle,vitesse=1, retry=1, recalage = 0):
        print "\t \tDeplacement: distance:",str(distance)," angle:",str(angle)
        if self.communication.portserie != '':
            self.communication.envoyer("M;"+str(distance)+";"+str(angle)+";"+str(vitesse)+";1\r\n")
            self.encodeur = self.communication.recevoir()

        if self.communication.portserie != '':
            status = ""
            while(not status.__contains__("mouvement")):
                status = self.communication.recevoir()
                print status
            while(not self.encodeur.__contains__("ANGLE")):
                self.encodeur = self.communication.recevoir()
                print self.encodeur

            #Update Position / Angle
            distanceDone = float(self.encodeur.split(";")[0].split("=")[1])
            angleDone = float(self.encodeur.split(";")[1].split("=")[1])
            self.updatePositionRelative(distanceDone,angleDone)
            if(recalage == 1):
                print "recalage"
                return True
            if( (status.__contains__("immobile") or status.__contains__("obstacle")) and not recalage==1 ):
                print "Error " + status
                return self.distanceAtteinte(distance, angle, distanceDone, angleDone, 30, 5)
            print "\t \tMouvement Fini, encodeur: "+self.encodeur
            if(self.encodeur.__len__() != 0):
                if not self.distanceAtteinte(distance, angle, distanceDone, angleDone, 50, 5):
                    if(retry):
                        self.seDeplacerDistanceAngle(distance, angle, vitesse, 0)
                    else:
                        return False
                else:
                    return True;
            else:
                return False
        else:
            self.updatePositionRelative(distance, angle)
            return True
        return False

    def seDeplacerVersUnElement(self,type,vitesse=1,couleur=None):
        element = None
        if couleur==None:
            couleur = self.couleur
        #recherche de l'objet
        for obj in self.listPointInteret:
            if obj.type == type and (obj.couleur == couleur or obj.couleur== "orange"):  #modifie pour pouvoir aller chercher objets de couleur orange (neutres)
                element = obj
                break
        if element == None:
            print "\t \tElement non trouve!!!!" + type
            return False
        zoneAcces = element.zoneAcces
        if zoneAcces == None:
            print "\t \tL'element \""+element.nom+"\" n'a pas de zone d'acces"
            return False
        #calcul du chemin vers l'objet
        chemin = self.chercher.trouverChemin(self.x,self.y,zoneAcces.x,zoneAcces.y,self.listPointInteret)
        if chemin == None:
            print "\t \tChemin non trouve vers \""+element.nom+"\"."
            return False
        for ligne in chemin:
            if not self.seDeplacerDistanceAngle(ligne.getlongeur(), self.getAngleToDo(ligne.getAngle()),vitesse):
                #Don't forget to get the new position in seDeplacerDistanceAngle
                print "\t \tErreur lors d'un deplacement"
                return False
        #the angle of the AccesZone
        if not self.seDeplacerDistanceAngle(0,self.getAngleToDo(zoneAcces.angle),vitesse):
            print "\t \tErreur lors de la rotation"
            return False
        return True


    def retirerElementCarte(self,type,couleur=None):
        element = None
        if couleur==None:
            couleur = self.couleur
        #recherche de l'objet
        for obj in self.listPointInteret:
            if obj.type == type and (obj.couleur == couleur or obj.couleur =="orange"):
                element = obj
                break
        if element == None:
            print "Element non trouve!!!!"
            return False
        self.listPointInteret.remove(element)
        return True

    def avancer(self,distance,vitesse=0.5):
        return self.seDeplacerDistanceAngle(distance,0,vitesse)

    def reculer(self,distance,vitesse=0.5):
        return self.seDeplacerDistanceAngle(-distance,0,vitesse)

    def recaler(self,distance,vitesse=0.5):
        return self.seDeplacerDistanceAngle(distance,0,vitesse, 1, 1)

    def setServomoteur(self, idServo, angle):
        if self.communication.portserie != '':
            self.communication.envoyer("S;"+str(idServo)+";0;"+str(angle)+"\r\n")
            valid = ""
            #OK
            while(not valid.__contains__("K")):
                valid = self.communication.recevoir()
                #PB
                if(valid.__contains__("B")):
                    return False
        return True

    def setProgressiveServomoteur(self, idServo, startAngle, endAngle, seconds, blocking=True):
        #Methode not tested, not sure we need to wait for OK or PB, ask fabrice AND check in the Mbed code
        if self.communication.portserie != '':
            self.communication.envoyer("X;"+str(idServo)+";"+str(startAngle)+";"+str(endAngle)+";"+str(seconds)+"\r\n")
            if(blocking):
                time.sleep(seconds)
            valid = ""
            #OK
            while(not valid.__contains__("K")):
                valid = self.communication.recevoir()
                #PB
                if(valid.__contains__("B")):
                    return False
        return True

#Special methods for each year has to be wrote under there

#SPECIAL 2016 METHODS (Can be suppressed for another year)
    def lireMessagesMbed(self):
        if self.communication.portserie == '':
            self.startTime = time.time()
            return True
        rcv = self.communication.recevoir()
        print rcv
        while(True):
            rcv = self.communication.recevoir()
            print rcv
        return True

    def interrogerCapteurIR(self):
        self.communication.envoyer("I\r\n")
        if self.communication.portserie == '':
           return True
        rcv = self.communication.recevoir()
        print rcv
        return True

    def sortirGrille(self):
        return self.setProgressiveServomoteur(2,10,180,2)

    def deplacerServoProgressivementDescenteGrille(self):
        return self.setProgressiveServomoteur(1,10,190,2)

    def deplacerServoProgressivementMonteGrille(self):
        return self.setProgressiveServomoteur(1,190,250,2)

    def oscillerGrillePoissons(self,idServo, angle1, angle2, tempsPause, nombre):
        for i in range(0, nombre):
            pause = float(tempsPause/1000.0)
            self.setServomoteur(idServo, angle1)
            time.sleep(pause)
            self.setServomoteur(idServo, angle2)
            time.sleep(pause)
        return True

    def rangerGrille(self):
        self.setServomoteur(2,100)
        time.sleep(0.100)
        self.setServomoteur(1,230)
        return True

    def setPelle(self,deployee):
        if deployee == 1:
            self.setServomoteur(4,150)
        elif deployee == 0:
            self.setServomoteur(4,235)
        return True

    #SPECIAL 2016 METHODS