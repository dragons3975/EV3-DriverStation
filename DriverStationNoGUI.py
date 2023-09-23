import socket
import sys
import time
import pygame
import struct
from datetime import datetime, timedelta

if __name__ == '__main__':

    #ev3_ip = "localhost"
    ev3_ip = "192.168.0.189"
    
    # Décommenter le mode voulu
    mode = "auto" # 1min de mode auto
    #mode = "teleop" # 2min de mode teleop
    #mode = "test" # Aucune limite de temps (teleop infini)
    
    modes = ["disabled", "auto", "teleop", "test"]
    compteur_disabled = 0

    # Socket UDP
    socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    pygame.init()
    pygame.joystick.init()

    nbJoysticks = pygame.joystick.get_count()

    joysticks = []
    for i in range(nbJoysticks):
        joysticks.append(pygame.joystick.Joystick(i))
        joysticks[i].init()
    
    start = datetime.now()
    if mode == "auto":
        end_autonomous = start + timedelta(minutes=1)
    else:
        end_autonomous = start
    end_teleop = end_autonomous + timedelta(minutes=2)        

    print(mode)
    
    while True:
        
        # Passage du mode auto au mode disabled après 1min
        if mode == "auto" and datetime.now() > end_autonomous:
            mode = "disabled"
            print(mode)
        # Passage du mode teleop au mode disabled après 2min
        if mode == "teleop" and datetime.now() > end_teleop:
            mode = "disabled"
            print(mode)
        
        # Préparation du prochain message (tableau d'octets)
        
        # Mode. Type integer sur un octet ("b") : 1 octet.
        message = modes.index(mode).to_bytes(1, sys.byteorder)

        # Nombre de joysticks. Type int ("i") : 4 octets.
        message = message + struct.pack("i", nbJoysticks)

        pygame.event.pump()
        for joystick in joysticks:
            # Nombre d'axes. Type int ("i") : 4 octets.
            message = message + struct.pack("i", joystick.get_numaxes())
            for i in range(joystick.get_numaxes()):
                # Valeur de l'axe. Type float ("f") : 4 octets.
                message = message + struct.pack("f", joystick.get_axis(i))
            
            buttons = 0
            numbuttons = joystick.get_numbuttons()
            for i in range(numbuttons):
                if joystick.get_button(i):
                    buttons += 1 << i
            
            for i in range(joystick.get_numhats()):
                hat = joystick.get_hat(i)
                if hat[0] == -1:
                    buttons += 1 << numbuttons
                numbuttons = numbuttons + 1
                if hat[0] == 1:
                    buttons += 1 << numbuttons
                numbuttons = numbuttons + 1
                if hat[1] == 1:
                    buttons += 1 << numbuttons
                numbuttons = numbuttons + 1
                if hat[1] == -1:
                    buttons += 1 << numbuttons
                numbuttons = numbuttons + 1
            
            # Valeurs des boutons. Incluant les hat. 1 bit par bouton. Type int ("i") : 4 octets.
            message = message + struct.pack("i", buttons)

        # Envoi du message par UDP
        socket_udp.sendto(message, (ev3_ip, 5005))
        
        # Quitter automatiquement après 10 paquets envoyés à la fin (disabled)
        if mode == "disabled":
            compteur_disabled += 1
            if compteur_disabled > 10:
                break

        # Temps avant le prochain envoi
        time.sleep(0.1)

    # Fermeture du socket UDP
    socket_udp.close()
    pygame.quit()
    print("Fin du programme - le relancer pour la prochaine partie")
