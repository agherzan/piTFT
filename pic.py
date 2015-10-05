import os
import pygame
import time
import urllib2
import json
from signal import alarm, signal, SIGALRM
import picamera
import RPi.GPIO as GPIO
import sh
import io
import yuv2rgb
from threading import Timer
import pickle

liveFlag    = 4
pushFlag    = 0

takePicFlag = False
sleepFlag   = False


mytft    = 0
font     = 0
camera   = 0
sizeData = 0
sizeMode = 0

os.chdir("/data/piTFT_mBeast")

def sleepMode():
    global pushFlag
    print "You can take push again"

    pushFlag = 0

def picButton(channel):
    global takePicFlag
    print "event", channel, GPIO.input(channel) 
    takePicFlag = True

def liveFeed(channel):
    global liveFlag

    print "event", channel, GPIO.input(channel)

    #if liveFlag == 1:
    #    liveFlag = 2
        
    #elif liveFlag == 3:
    #    liveFlag = 4

    print "live feed is " + str(liveFlag)

def gitPush(channel):
    global pushFlag, liveFlag 

    print "event", channel, GPIO.input(channel) 
    
    if pushFlag == 2:
        pushFlag = 3

        if liveFlag == 1:
            liveFlag = 3

    elif pushFlag == 0:
        pushFlag = 1

        if liveFlag == 1:
            liveFlag = 3

#set up the screen so we can push stuff onto it.
class pitft :
    screen = None
    colourBlack = (0, 0, 0)

    def __init__(self):
        "Ininitializes a new pygame screen using the framebuffer"
        # Based on "Python GUI in Linux frame buffer"
        # http://www.karoltomala.com/blog/?p=679
        disp_no = os.getenv("DISPLAY")
        if disp_no:
            print "I'm running under X display = {0}".format(disp_no)

        os.putenv('SDL_FBDEV', '/dev/fb1')

        # Select frame buffer driver
        # Make sure that SDL_VIDEODRIVER is set
        driver = 'fbcon'
        if not os.getenv('SDL_VIDEODRIVER'):
            os.putenv('SDL_VIDEODRIVER', driver)
        class Alarm(Exception):
            pass
        def alarm_handler(signum, frame):
            raise Alarm
        signal(SIGALRM, alarm_handler)
        alarm(3)
        try:
            pygame.display.init()
            print 'getting screen size'
            size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
            self.screen = pygame.display.set_mode(size, 0, 32)
            print size
            alarm(0)
        except Alarm:
            raise KeyboardInterrupt
        print 'setting up framebuffer'



        # Clear the screen to start
        self.screen.fill((0, 0, 0))
        # Initialise font support
        pygame.font.init()
        # Render the screen
        pygame.display.update()

    def __del__(self):
        "Destructor to make sure pygame shuts down, etc."

def main():
    global mytft, font, liveFlag, takePicFlag, pushFlag, camera, sizeMode, sizeData

    #this path is where we store our arrow icons
    installPath = "/usr/src/app/img/"

    # font colours
    colourWhite = (255, 255, 255)
    colourBlack = (0, 0, 0)
    colourGreen = (3, 192, 60)
    colourRed = (220, 69, 69)

    # Create an instance of the pitft class
    mytft = pitft()

    #hide the mouse from screen
    pygame.mouse.set_visible(False)

    # set up the fonts
    # choose the font
    fontpath = pygame.font.match_font('dejavusansmono')
    font = pygame.font.Font(fontpath, 10)

    #read the ENV VAR, use GE if 'STOCK' isn't there
    #companyName = os.getenv('STOCK', "GE")
    #print 'company name: '+companyName

    logo = pygame.image.load( "/usr/src/app/resin.png")
    mytft.screen.blit(logo, (0, 0))

    pygame.display.update()

    GPIO.setmode(GPIO.BCM)

    GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)  
#    GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP) 

 
#    GPIO.add_event_detect(18, GPIO.RISING, callback=picView)  # add rising edge detection on a channel
    GPIO.add_event_detect(27, GPIO.RISING, callback=liveFeed)  # add rising edge detection on a channel    
    GPIO.add_event_detect(23, GPIO.RISING, callback=picButton)  # add rising edge detection on a channel
    GPIO.add_event_detect(22, GPIO.RISING, callback=gitPush)  # add rising edge detection on a channel


    sizeMode = 0

    sizeData = [ # Camera parameters for different size settings
     # Full res      Viewfinder  Crop window
     [(2592, 1944), (320, 240), (0.0   , 0.0   , 1.0   , 1.0   )], # Large
     [(1920, 1080), (320, 180), (0.1296, 0.2222, 0.7408, 0.5556)], # Med
     [(1440, 1080), (320, 240), (0.2222, 0.2222, 0.5556, 0.5556)]] # Small

    # Buffers for viewfinder data
    rgb = bytearray(320 * 240 * 3)
    yuv = bytearray(320 * 240 * 3 / 2)

    updates = pickle.load(open( "save.p", "rb" ) )

    while True:

        if liveFlag == 1:

            stream = io.BytesIO() # Capture into in-memory stream
            camera.capture(stream, use_video_port=True, format='raw')
            stream.seek(0)
            stream.readinto(yuv)  # stream -> YUV buffer
            stream.close()
            yuv2rgb.convert(yuv, rgb, sizeData[sizeMode][1][0], sizeData[sizeMode][1][1])
            img = pygame.image.frombuffer(rgb[0: (sizeData[sizeMode][1][0] * sizeData[sizeMode][1][1] * 3)], sizeData[sizeMode][1], 'RGB')
            if img is None or img.get_height() < 240: # Letterbox, clear background
                mytft.screen.fill(0)
            if img:
                mytft.screen.blit(img,((320 - img.get_width() ) / 2, (240 - img.get_height()) / 2))

            pygame.display.update()

            if takePicFlag :
                print "taking pic"
                #camera.resolution = (1024,768)
                name = 'image.jpg'

                liveFlag = 1
                pushFlag = 0
                takePicFlag = False
                camera.capture(name, resize=(320, 240))
                time.sleep(0.1)

                print "Pic to screen"
                logo = pygame.image.load(name)
                mytft.screen.blit(logo, (0, 0))

                #pygame.display.flip()
                # # refresh the screen with all the changes
                pygame.display.update()
                print "Screen updated"
                time.sleep(5)
                camera.resolution = sizeData[sizeMode][1]
                camera.crop       = (0.0, 0.0, 1.0, 1.0)

        # elif liveFlag == 2:
            
        #     camera.close()
            
        #     logo = pygame.image.load( "/usr/src/app/resin.png")
        #     mytft.screen.blit(logo, (0, 0))

        #     pygame.display.update()

        #     liveFlag = 3

        elif liveFlag == 3:
            # if takePicFlag:
            #     name = 'image.jpg'
            #     if os.path.isfile(name) :
            #         print "Previous pic to screen"
            #         logo = pygame.image.load(name)
            #         mytft.screen.blit(logo, (0, 0))

            #         #pygame.display.flip()
            #         # # refresh the screen with all the changes
            #         pygame.display.update()
            #     else :
            #         print "no Pic found"
            #     takePicFlag = False
            
            if pushFlag == 1:

                colourWhite = (255, 255, 255)
                colourBlack = (0, 0, 0)
                colourGreen = (3, 192, 60)
                colourRed = (220, 69, 69)
                colourPink = (255, 20, 147)

                noCommitFlag = False

                # clear the screen
                mytft.screen.fill(colourBlack)
                # set the anchor/positions for the current stock data text
                textAnchorX = 10
                textAnchorY = 10
                textYoffset = 10
                listMax = 240/textYoffset

                line = "git status"
                print line
                text_surface = font.render(line, True, colourRed)
                mytft.screen.blit(text_surface, (textAnchorX, textAnchorY))
                textAnchorY += textYoffset
                pygame.display.update()

                stripped = lambda s: "".join(i for i in s if 31 < ord(i) < 127)


                for line in sh.git( "status", _iter=True):
                    print(line)
                    line = stripped(line)

                    if line.find("nothing to commit") == 0 :
                        print "found"
                        noCommitFlag = True

                    text_surface = font.render(line, True, colourWhite)
                    mytft.screen.blit(text_surface, (textAnchorX, textAnchorY))

                    pygame.display.update()
                    textAnchorY += textYoffset
                    if textAnchorY + textYoffset > 240:
                        textAnchorY = 10
                        mytft.screen.fill(colourBlack)

                    time.sleep(0.1)

                if noCommitFlag == True:

                    line = "Please take a Pic "
                    print line
                    text_surface = font.render(line, True, colourRed)
                    mytft.screen.blit(text_surface, (textAnchorX, textAnchorY))

                    pygame.display.update()

                    pushFlag = 0 

                    continue

                updates += 1 
                pickle.dump( updates, open( "save.p", "wb" ))

                time.sleep(5)

                mytft.screen.fill(colourBlack)

                textAnchorX = 10
                textAnchorY = 10    

                line = "git add ."
                print line
                text_surface = font.render(line, True, colourRed)
                mytft.screen.blit(text_surface, (textAnchorX, textAnchorY))
                textAnchorY += textYoffset
                pygame.display.update()

                for line in sh.git.add ("image.jpg", "save.p", _iter=True):
                    print(line)
                    line = stripped(line)

                    text_surface = font.render(line, True, colourWhite)
                    mytft.screen.blit(text_surface, (textAnchorX, textAnchorY))

                    pygame.display.update()
                    textAnchorY += textYoffset
                    if textAnchorY + textYoffset > 240:
                        textAnchorY = 10
                        mytft.screen.fill(colourBlack)

                    time.sleep(0.1)

                time.sleep(5)

                mytft.screen.fill(colourBlack)

                textAnchorX = 10
                textAnchorY = 10

                line = "git commit -m "
                print line
                text_surface = font.render(line, True, colourRed)
                mytft.screen.blit(text_surface, (textAnchorX, textAnchorY))
                textAnchorY += textYoffset
                pygame.display.update()

                for line in sh.git( "commit", "-m", "Auto commit", _iter="out"):
                    print(line)
                    line = stripped(line)

                    text_surface = font.render(line, True, colourWhite)
                    mytft.screen.blit(text_surface, (textAnchorX, textAnchorY))

                    pygame.display.update()
                    textAnchorY += textYoffset
                    if textAnchorY + textYoffset > 240:
                        textAnchorY = 10
                        mytft.screen.fill(colourBlack)
                    
                    time.sleep(0.1)           

                pushFlag = 2
                     
                time.sleep(10)



            elif pushFlag == 3:


                mytft.screen.fill(colourBlack)

                textAnchorX = 10
                textAnchorY = 10

                line = "git push resin master"
                print line
                text_surface = font.render(line, True, colourRed)
                mytft.screen.blit(text_surface, (textAnchorX, textAnchorY))
                textAnchorY += textYoffset
                pygame.display.update()

                color = colourWhite

                sc = []

                sc.append("git push resin master")

                for line in sh.git( "push", "resin", "master", "--force", _iter="err"):
                    print(line)
                    line = stripped(line)

                    color = colourWhite                    

                    sc.append(line)
                    if len(sc) >= listMax :
                        sc.pop(1)

                    textAnchorY = 0
                    mytft.screen.fill(colourBlack)
                    for idx, lines in enumerate(sc):
                        if idx == 0:
                            text_surface = font.render(lines, True, colourRed)
                            mytft.screen.blit(text_surface, (textAnchorX, textAnchorY))
                            textAnchorY += textYoffset
                        else:
                            if lines.find("Build took") == 0 or  lines.find("_.-\' : ``") == 0 :
                                print "Unicorn found"
                                color = colourPink

                            text_surface = font.render(lines, True, color)
                            mytft.screen.blit(text_surface, (textAnchorX, textAnchorY))
                            textAnchorY += textYoffset

                    pygame.display.update()

                    time.sleep(0.1)

                pushFlag = 0

                #t = Timer(30.0, sleepMode)
                #t.start() 
                
                
                time.sleep(10)

            liveFlag = 1
            
        elif liveFlag == 4:

            camera            = picamera.PiCamera()

            camera.resolution = sizeData[sizeMode][1]
            camera.crop       = (0.0, 0.0, 1.0, 1.0)

            liveFlag = 1
        
        #time.sleep(1)

if __name__ == '__main__':
    print 'starting main()'
    main()