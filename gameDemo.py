import pygame
import pyaudio
import librosa
import copy,math,time,random    #built in
import threading
import numpy as np


###########################################
# Classes
###########################################

class Player(object):
    def __init__(self,x,y,data,image):
        self.x=x
        self.y=y
        self.width=data.width
        self.height=data.height
        self.speed=7
        self.angularSpd=5
        self.angle=90
        self.health=100
        self.fullHealth=copy.copy(self.health)
        self.attackSpd=0.25  #cooldown Timer for firing (0.25 seconds)

        self.ship=pygame.image.load(image).convert_alpha()
        self.scale=1/10 #adjusts image size

        smallSide=min(self.width,self.height)
        self.ship=pygame.transform.scale(self.ship, (int(smallSide * self.scale),
                                                       int(smallSide * self.scale)))
        self.size=self.ship.get_rect().size     #returns tuple of size (60,60)
        self.clean=copy.copy(self.ship)
        self.rect=pygame.Rect(self.x,self.y,self.size[0],self.size[1])

    def draw(self,gameDisplay):
        healthBarHeight=5
        gameDisplay.blit(self.ship,(self.x,self.y))

        #drawing the health bar
        pygame.draw.rect(gameDisplay,(255,0,0),
                         (self.rect[0],self.rect[1],self.size[0],healthBarHeight))
        pygame.draw.rect(gameDisplay,(0,255,0),
                         (self.rect[0],self.rect[1],
                          self.size[0]*self.health/self.fullHealth,healthBarHeight))


    def move(self,direction):
        #makes sure ship doesn't fly off the screen
        if direction[0]==1 and self.y>=0:
            self.y-=self.speed
        if direction[0]==-1 and self.y+self.size[1]<=self.height:
            self.y+=self.speed
        if direction[1]==-1 and self.x>=0:
            self.x-=self.speed
        if direction[1]==1 and self.x+self.size[0]<=self.width:
            self.x+=self.speed
        self.rect=pygame.Rect(self.x,self.y,
                              self.size[0],self.size[1])

    def rotate(self,right):
        self.ship=pygame.transform.rotate(self.clean,self.angle)
        self.angle+=self.angularSpd*right
        rotRect = self.ship.get_rect()
        rotRect.center=self.clean.get_rect().center

    def die(self,optional=0):
        if self.health<=0:
            return True


class Turret(Player):
    def __init__(self,x,y,data,image):
        super().__init__(x,y,data,image)
        self.ship=pygame.image.load("turret.png")
        self.scale = 1 / 10  # adjusts image size
        self.health=300
        self.fullHealth=copy.copy(self.health)
        self.speed=4        #different speed from Player
        self.angularSpd=30
        self.attackSpd=0.2

        smallSide = min(self.width, self.height)
        self.ship = pygame.transform.scale(self.ship,
                                           (int(smallSide * self.scale),
                                            int(smallSide * self.scale)))
        self.size = self.ship.get_rect().size  # returns tuple of size (60,60)

        self.ship = pygame.transform.rotate(self.ship,self.angle-90)
        self.clean=copy.copy(self.ship)

    #move turret and rotate in accordance to position on screen
    def move(self,direction):
        if direction==1:
            if self.x<=0 and self.y+self.size[1]<=self.height:
                self.y+=self.speed
                self.angle=0
            elif self.y+self.size[1]>=self.height and \
                    self.x+self.size[0]<=self.width:
                self.x+=self.speed
                self.angle=90
            elif self.x+self.size[0]>=self.width and self.y>=0:
                self.y-=self.speed
                self.angle=180
            elif self.y<=0 and self.x>=0:
                self.x-=self.speed
                self.angle=270

        if direction==-1:
            if self.x<=0 and self.y>=0:
                self.y-=self.speed
                self.angle=0
            elif self.y<=0 and self.x+self.size[0]<=self.width:
                self.x+=self.speed
                self.angle=270
            elif self.x+self.size[0]>=self.width and \
                        self.y+self.size[1]<=self.height:
                self.y+=self.speed
                self.angle=180
            elif self.y+self.size[1]>=self.height and self.x>=0:
                self.x-=self.speed
                self.angle=90

        self.ship=pygame.transform.rotate(self.clean,self.angle)
        self.rect=pygame.Rect(self.x,self.y,
                              self.size[0]*1/2,self.size[1]*1/2)

############################################################
############################################################

class Projectile(object):
    def __init__(self,x,y,data):
        self.x=x
        self.y=y
        self.width=data.width
        self.height=data.height
        self.speed=8
        self.scale=1/20
        self.bullet=pygame.image.load("otherBullet.png").convert_alpha()
        self.bullet=pygame.transform.scale(self.bullet,
            (int(self.width*self.scale),int(self.height*self.scale)))
        self.bullet=pygame.transform.rotate(self.bullet,-90)
        self.clean=copy.copy(self.bullet)
        self.size=self.bullet.get_rect().size     #returns tuple of size
        self.rect=pygame.Rect(self.x,self.y,self.size[0]*1/2,self.size[1]*1/2)


    def move(self,angle):
        self.bullet = pygame.transform.rotate(self.clean, angle)
        angle=math.radians(angle)
        self.y-=self.speed*math.sin(angle)
        self.x+=self.speed*math.cos(angle)
        self.rect=pygame.Rect(self.x,self.y,self.size[0],self.size[1])


    def draw(self, gameDisplay):
        gameDisplay.blit(self.bullet, (self.x, self.y))

    def collide(self, obj1):
        if pygame.sprite.collide_rect(obj1, self):
            return True


class PlayerBullet(Projectile):
    def __init__(self,x,y,data):
        super().__init__(x,y,data)
        self.bullet=pygame.image.load("shipBullet.png").convert_alpha()
        self.bullet=pygame.transform.scale(self.bullet,
            (int(self.width*self.scale),int(self.height*self.scale)))
        self.bullet=pygame.transform.rotate(self.bullet,-90)
        self.clean=copy.copy(self.bullet)
        self.rect=pygame.Rect(self.x,self.y,self.size[0]*1/2,self.size[1]*1/2)

############################################################
############################################################


class Interactable(Projectile): #default as health orb
    def __init__(self,data):
        #define bullet to find x and y for super call
        self.bullet = pygame.image.load('healthOrb.png').convert_alpha()
        self.scale=1/20
        self.bullet=pygame.transform.scale(self.bullet,
            (int(data.width*self.scale),int(data.height*self.scale)))
        self.size=self.bullet.get_rect().size     #returns tuple of size
        x=random.randint(0,data.width-self.size[0])
        y=random.randint(0,data.height-self.size[1])
        super().__init__(x,y,data)

        #recall bullet since super overrides bullet
        self.bullet = pygame.image.load('healthOrb.png').convert_alpha()
        self.bullet=pygame.transform.scale(self.bullet,
            (int(self.width*self.scale),int(self.height*self.scale)))
        self.rect=pygame.Rect(self.x,self.y,self.size[0],self.size[1])

    def collide(self, obj1,data):
        if pygame.sprite.collide_rect(obj1, self):
            obj1.health=obj1.fullHealth
            data.score+=300
            return True

class voidOrb(Interactable):
    def __init__(self,data):
        super().__init__(data)
        self.bullet = pygame.image.load('voidOrb.png').convert_alpha()
        self.scale=1/20
        self.bullet=pygame.transform.scale(self.bullet,
            (int(data.width*self.scale),int(data.height*self.scale)))

    def collide(self, obj1,data):
        if pygame.sprite.collide_rect(obj1, self):
            obj1.health-=20
            return True


class attackOrb(Interactable):
    def __init__(self, data):
        super().__init__(data)
        self.bullet = pygame.image.load('attackOrb.png').convert_alpha()
        self.scale = 1 / 20
        self.bullet = pygame.transform.scale(self.bullet,
                                             (int(data.width * self.scale),
                                              int(data.height * self.scale)))

    def collide(self, obj1,data):
        if pygame.sprite.collide_rect(obj1, self):
            obj1.attackSpd -= 0.05
            if obj1.attackSpd<0.05:
                obj1.attackSpd+=0.05
                #change back to normal if attackSpd is 0
            data.score+=200
            return True


##################################################
# Variables Stored
##################################################

def init(data):
    data.song='30beat.wav'

    bgm = data.song
    pygame.mixer.init()
    pygame.mixer.music.load(bgm)

    y, sr = librosa.load(data.song)

    # beat related
    data.fps = 50
    data.tempo, data.beats = librosa.beat.beat_track(y=y, sr=sr)
    data.beats = librosa.frames_to_time(data.beats, sr=sr)
    data.beatList = []
    for beat in data.beats:
        data.beatList.append(round(beat, 1))

    ##############################################
    # Game #
    ##############################################

    data.timePassed = pygame.time.get_ticks() // 100 / 10
    # keep track of time in seconds.00
    data.x=data.width/2
    data.y=data.height/2
    data.clock = pygame.time.Clock()
    data.ship = Player(data.x, data.y, data, 'playerShip.png')
    data.direction=[0,0] #updown and leftright, list because multiple inputs
    data.turretBullets=[]
    data.playerBullets=[]
    data.sec=0
    data.damageToShip=8
    data.score=0

    data.turrets=[]
    data.turrets.append(Turret(0,0,data,'turret.png'))
    offset=data.turrets[0].size[0]
    data.turrets.append(Turret(data.width-offset,0,data,'turret.png'))
    data.turrets.append(Turret(0,data.height-offset,data,'turret.png'))
    data.turrets.append(Turret(data.width-offset,data.height-offset,data,'turret.png'))
    data.turretDirection=1
    data.damageToTurret=15

    data.spawn=0
    data.spawnTime=3
    data.orbs=[]
    data.orbList=[Interactable(data),attackOrb(data),
                  voidOrb(data),attackOrb(data),voidOrb(data)]

    offset=60
    data.ship2=Player(data.x, data.y+offset, data, 'playerTwo.png')
    data.direction2 = [0, 0]
    data.sec2=0  #for attack counter 2
    data.multi=False

    data.recordMode=False
    data.beat=False
    data.recordOver=False
    data.secTurret=0

################################################
# Pygame Functions
################################################


def shipMove(data):
    keys = pygame.key.get_pressed()
    #up down methods
    if keys[pygame.K_w]:
        data.direction[0] = 1
    elif keys[pygame.K_s]:
        data.direction[0] = -1
    else:
        data.direction[0] = 0

    #left right methods
    if keys[pygame.K_a]:
        data.direction[1] = -1
    elif keys[pygame.K_d]:
        data.direction[1] = 1
    else:
        data.direction[1] = 0

    # Multiplayer Mode ###
    if keys[pygame.K_UP]:
        data.direction2[0] = 1
    elif keys[pygame.K_DOWN]:
        data.direction2[0] = -1
    else:
        data.direction2[0] = 0

    # left right methods
    if keys[pygame.K_LEFT]:
        data.direction2[1] = -1
    elif keys[pygame.K_RIGHT]:
        data.direction2[1] = 1
    else:
        data.direction2[1] = 0
    return (data.direction,data.direction2)    #list of directions

def shootBullet(data,gameDisplay,bulletType,collider):
    for bullet in bulletType:
        if bullet[0].y<=data.height and bullet[0].y>=0 and \
            bullet[0].x<=data.width and bullet[0].x>=0:
                bullet[0].move(bullet[1])
                bullet[0].draw(gameDisplay)

                #bullet collides with ship
                if type(collider)!=list and bullet[0].collide(collider):
                    bulletType.pop(bulletType.index(bullet))
                    collider.health-=data.damageToShip

                #bullet collides with turret
                elif type(collider)==list:
                    for turret in collider:
                        if bullet[0].collide(turret):
                            bulletType.pop(bulletType.index(bullet))
                            turret.health -= data.damageToTurret
                            data.score+=100
        else:
            bulletType.pop(bulletType.index(bullet))
            #pop turretBullets that go off the screen

def turretFunction(data,gameDisplay):
    try:
        offset=data.turrets[0].size[1]/4
    except:
        return True
        #no more turrets left

    if not data.recordMode:
        for turret in data.turrets:
            if not turret.die():
                if data.timePassed in data.beatList:
                    b = Projectile(turret.x + offset, turret.y + offset, data)
                    data.turretBullets.append((b, turret.angle))
                    data.turretDirection = random.choice([-1, 1, 1])
                    # higher chance of moving forward
                turret.move(data.turretDirection)
                turret.draw(gameDisplay)
            else:
                data.turrets.remove(turret)
    else:
        if data.beat and attackCounter(data.secTurret, data.turrets[0]):
            for turret in data.turrets:
                if not turret.die():
                    b = Projectile(turret.x + offset, turret.y + offset, data)
                    data.turretBullets.append((b, turret.angle))
                    data.turretDirection = random.choice([-1, 1, 1, 1])
                    data.secTurret = time.time()
                else:
                    data.turrets.remove(turret)
    for turret in data.turrets:
        turret.move(data.turretDirection)
        turret.draw(gameDisplay)


def attackCounter(sec,ship):
    if time.time()-sec>=ship.attackSpd:
        return True
    return False

def shipFunction(data,gameDisplay,keys):
    # Ship shooting
    if not data.ship.die():
        if keys[pygame.K_SPACE] and attackCounter(data.sec,data.ship):
            offset=data.ship.size[0]/4  #same offset becasue of square
            b=PlayerBullet(data.ship.x+offset,data.ship.y+offset,data)
            data.playerBullets.append((b,data.ship.angle))
            data.sec=time.time()
        right=0
        if keys[pygame.K_g]:
            right=1
        if keys[pygame.K_h]:
            right=-1


        data.ship.rotate(right)
        data.ship.move(data.direction)
        data.ship.draw(gameDisplay)

    # Multiplayer Mode ###
    if data.multi:
        if not data.ship2.die():
            if keys[pygame.K_o] and attackCounter(data.sec2, data.ship2):
                offset = data.ship2.size[0] / 4  # same offset becasue of square
                b = PlayerBullet(data.ship2.x + offset, data.ship2.y + offset, data)
                data.playerBullets.append((b, data.ship2.angle))
                data.sec2 = time.time()
            right2 = 0
            if keys[pygame.K_i]:
                right2 = 1
            if keys[pygame.K_p]:
                right2 = -1
            data.ship2.rotate(right2)
            data.ship2.move(data.direction2)
            data.ship2.draw(gameDisplay)

def spawnObstacles(data,gameDisplay):
    sec=time.time()
    if sec-data.spawn>=data.spawnTime:
        Orb = random.choice(data.orbList)
        data.orbs.append(Orb)
        data.spawn=time.time()
    for orb in data.orbs:
        orb.draw(gameDisplay)
        if orb.collide(data.ship,data) or orb.collide(data.ship2,data):
            data.orbs.pop(data.orbs.index(orb))

def showScore(data,gameDisplay):
    scoreText = pygame.font.SysFont('impact', int(data.width / 20))
    scoreText = scoreText.render(str(data.score), 1, (255, 255, 255))
    offset = 10
    scoreTextRect = scoreText.get_rect(topright=(data.width - offset, offset))
    gameDisplay.blit(scoreText, (scoreTextRect))

########################################################
# Page related Functions
########################################################

#creates Game Over, You Win, and Title
def mainText(data,gameDisplay, text):
    startText = pygame.font.SysFont('impact', int(data.width / 10),
                                    False, True)
    startText = startText.render(text, 1, (255, 255, 255))
    startTextRect = startText.get_rect(center=(data.width / 2,
                                               data.height * 3 / 10))
    gameDisplay.blit(startText, (startTextRect))


#Creates Button, Returns True when clicked on
def buttonFunction(data,gameDisplay,text,height):
    buttonHeight = data.height / 15
    buttonWidth = buttonHeight * 4
    buttonPosTup = (data.width / 2 - buttonWidth / 2,
                    height - buttonHeight / 2,
                    buttonWidth, buttonHeight)
    pygame.draw.rect(gameDisplay, (255, 255, 255), buttonPosTup)
    goText = pygame.font.SysFont('impact', int(data.width / 30))
    goText = goText.render(text, 1, (0, 0, 0))
    goTextRect = goText.get_rect(center=(buttonPosTup[0] + buttonWidth / 2,
                                         buttonPosTup[1] + buttonHeight / 2))
    gameDisplay.blit(goText, (goTextRect))

    if pygame.mouse.get_pressed()[0] == 1:
        x = pygame.mouse.get_pos()[0]
        y = pygame.mouse.get_pos()[1]
        if x > buttonPosTup[0] and x < buttonPosTup[0] + buttonWidth:
            if y > buttonPosTup[1] and y < buttonPosTup[1] + buttonHeight:
                return True

def startFunction(data):
    # spawn items timer
    data.spawn = time.time()

    # start playing the music
    if not data.recordMode:
        pygame.mixer.music.play()

    # re-adjust when the turrets shoot to match game start
    data.timePassed = pygame.time.get_ticks() // 100 / 10
    data.beatList = list(map(lambda x: round(x + data.timePassed, 1), data.beatList))

def instructions(data,gameDisplay,page=1):
    gameOver = pygame.image.load("gameOver.jpg")
    gameDisplay.blit(gameOver, (0, 0))

    instructList=[]
    instructList.append("Use the WASD Keys to move, G H to rotate,")
    instructList.append("and the SPACEBAR to shoot. Your goal is to")
    instructList.append("survive for the duration of the song by dodging")
    instructList.append("the bullets fired by the menacing Beat Turrets.")
    instructList.append("Collect the Red and Green Orbs for Power ups.")
    instructList.append("avoid the black holes, which do damage!!")

    instructList2 = []
    instructList2.append("Player 2: Use Arrow Keys to move, J L to rotate,")
    instructList2.append("Use K to Shoot. Work with Player 1 to reach ")
    instructList2.append("a higher score. Collecting Orbs and hitting ")
    instructList2.append("turrets grant you points!")
    instructList2.append("Play Music in the background for Recorder Mode!")

    lineHeight=1

    if page==1:
        for line in instructList:
            howText = pygame.font.SysFont('impact', int(data.width / 25),
                                          False, True)
            howText = howText.render(line, 1, (255, 255, 255))
            howTextRect = howText.get_rect(center=(data.width / 2,
                                            data.height * lineHeight/10))
            gameDisplay.blit(howText, (howTextRect))
            lineHeight+=1
    elif page==2:
        for line in instructList2:
            howText = pygame.font.SysFont('impact', int(data.width / 25),
                                          False, True)
            howText = howText.render(line, 1, (255, 255, 255))
            howTextRect = howText.get_rect(center=(data.width / 2,
                                            data.height * lineHeight/10))
            gameDisplay.blit(howText, (howTextRect))
            lineHeight+=1

def highScores(data,gameDisplay):
    startText = pygame.font.SysFont('impact', int(data.width / 15))
    startText = startText.render('High Scores:', 1, (255, 255, 255))
    startTextRect = startText.get_rect(center=(data.width / 2,
                                               data.height * 2 / 10))
    gameDisplay.blit(startText, (startTextRect))

    # find top 8 scores:
    scores = list(open('score.txt', 'r'))
    scores = list(map(lambda x: int(x), scores))
    scoreStyle = pygame.font.SysFont('impact', int(data.width / 24),
                                     False, True)
    try:
        for i in range(7,15):
            highScore=max(scores)
            scoreText = scoreStyle.render('%d. %d' % (i-7,highScore), 1, (255, 255, 255))
            scoreTextRect = scoreText.get_rect(center=(data.width / 2,
                                                   data.height * i / 20))
            gameDisplay.blit(scoreText, (scoreTextRect))
            scores.remove(highScore)
    except:     #no more scores left (less than 8 scores total)
        pass

def quitFunction():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return True

def newPage(pageList,next):
    for page in pageList:
        pageList[page] = False
    pageList[next] = True
    return pageList


###################################################
# Recording Mode
###################################################


#This Function was Borrowed and changed from StackOverflow
def micDemo(data,name):
    CHUNK = 2 ** 11
    RATE = 44100

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True,
                    frames_per_buffer=CHUNK)

    #balance out speed
    for turret in data.turrets:
        turret.speed=6
    startTime=time.time()
    while time.time()-startTime<=30:    #goes for 30 seconds
        soundData = np.fromstring(stream.read(CHUNK), dtype=np.int16)    #list
        peak = np.average(np.abs(soundData)) * 2     #averages list
        bars = "#" * int(50 * peak / 2**14)
        if len(bars)>8:
            data.beat=True
        else:
            data.beat=False

        #stop threading when dead
        if data.ship.health<=0:
            break

    stream.stop_stream()
    stream.close()
    p.terminate()
    for turret in data.turrets:
        turret.speed=4
    data.recordOver=True


########################################################
# Run
########################################################

def run(width,height):
    pygame.init()
    gameDisplay = pygame.display.set_mode((width,height))
    pygame.display.set_caption("Game Demo")
    background=pygame.image.load("spaceBG.png")

    class Struct(object): pass
    data = Struct()
    data.width = width
    data.height = height
    writeScore = True

    startOver=True

    # Keeps track of what page user is on
    pageList={'menu': True, 'start': False,
              'howTo': False,'level':False,
              'dead':False, 'winner':False,
              'scores':False,'howTo2':False}

    exit=False
    while exit!=True:

        # menu screen   #################################
        if pageList['menu']:
            gameOver = pygame.image.load("gameOver.jpg")
            gameDisplay.blit(gameOver, (0, 0))
            writeScore=True

            mainText(data,gameDisplay,'UNSAFE   AND   SOUND')

            exit=quitFunction()

            startButton = buttonFunction(data,gameDisplay,'One Player', data.height * 5 / 10)
            recordButton = buttonFunction(data,gameDisplay,'Recorder Mode', data.height * 6 / 10)
            multiButton = buttonFunction(data,gameDisplay,'Co-op', data.height * 7 / 10)
            howToButton = buttonFunction(data,gameDisplay,'How To Play', data.height * 8 / 10)
            scoresButton = buttonFunction(data,gameDisplay,'High Scores', data.height * 9 / 10)

            if startButton:
                pageList=newPage(pageList,'level')
                data.multi=False
                data.recordMode=False
            elif recordButton:
                t = threading.Thread(target=micDemo, name='thread1', args=(data,'thread1'))
                t.start()
                data.recordMode=True
                data.ship.speed=12
                keys = pygame.key.get_pressed()
                pageList = newPage(pageList, 'start')
                startFunction(data)
            elif multiButton:
                pageList=newPage(pageList,'level')
                data.multi=True
                data.recordMode=False
            elif howToButton:
                pageList=newPage(pageList,'howTo')
            elif scoresButton:
                pageList=newPage(pageList,'scores')

            if startOver:
                init(data)  #IMPORTANT: initializing info
                startOver=False

        # High Scores Screen
        elif pageList['scores']:
            gameOver = pygame.image.load("gameOver.jpg")
            gameDisplay.blit(gameOver, (0, 0))
            exit = quitFunction()

            highScores(data,gameDisplay)
            menuButton = buttonFunction(data,gameDisplay,'menu',data.height * 9 / 10)
            if menuButton:
                pageList=newPage(pageList,'menu')

        # Instructions Screen
        elif pageList['howTo']:
            gameOver = pygame.image.load("gameOver.jpg")
            gameDisplay.blit(gameOver, (0, 0))
            exit=quitFunction()
            instructions(data,gameDisplay)
            page2Button = buttonFunction(data, gameDisplay, 'Next', data.height * 8 / 10)
            menuButton = buttonFunction(data, gameDisplay, 'Menu', data.height * 9 / 10)
            if menuButton:
                pageList=newPage(pageList,'menu')
            if page2Button:
                pageList=newPage(pageList,'howTo2')

        elif pageList['howTo2']:
            gameOver = pygame.image.load("gameOver.jpg")
            gameDisplay.blit(gameOver, (0, 0))
            exit=quitFunction()
            instructions(data,gameDisplay,2)
            menuButton = buttonFunction(data, gameDisplay, 'Menu', data.height * 9 / 10)
            if menuButton:
                pageList=newPage(pageList,'menu')

        # Choose a Level
        elif pageList['level']:
            gameOver = pygame.image.load("gameOver.jpg")
            gameDisplay.blit(gameOver, (0, 0))
            exit=quitFunction()

            mainText(data,gameDisplay,'Difficulty')
            easy = buttonFunction(data, gameDisplay, 'easy', data.height * 6 / 10)
            medium = buttonFunction(data, gameDisplay, 'medium', data.height * 7 / 10)
            hard = buttonFunction(data, gameDisplay, 'hard', data.height * 8 / 10)
            menuButton = buttonFunction(data, gameDisplay, 'Menu', data.height * 9 / 10)
            if menuButton:
                pageList = newPage(pageList, 'menu')

            Start=True
            if easy:
                data.damageToShip=4
                data.damageToTurret=20
            elif medium:
                data.damageToShip=8
                data.damageToTurret=15
            elif hard:
                data.damageToShip=12
                data.damageToTurret=10
            else:
                Start=False
                #only start when button pressed

            if Start:
                pageList=newPage(pageList,'start')
                keys = pygame.key.get_pressed()
                startFunction(data)

        #Game Start   ##########################################
        elif pageList['start']:
            gameDisplay.blit(background,(0,0))
            if not data.recordMode:
                songEnd = pygame.USEREVENT
                pygame.mixer.music.set_endevent(songEnd)

            for event in pygame.event.get():
                keys = pygame.key.get_pressed()
                if event.type == pygame.QUIT:
                    exit=True
                if not data.recordMode:
                    if event.type == songEnd:
                        pageList=newPage(pageList,'winner')
                else:
                    if data.recordOver:
                        pageList = newPage(pageList, 'winner')
                # Ship movement
                if keys[pygame.K_ESCAPE]:
                    pageList = newPage(pageList, 'dead')
                data.direction = shipMove(data)[0]
                data.direction2 = shipMove(data)[1]

            # controls turrets and checks if all dead
            if turretFunction(data,gameDisplay):
                pageList=newPage(pageList,'winner')
            shipFunction(data,gameDisplay,keys)

            if not data.ship.die():
                shootBullet(data, gameDisplay, data.turretBullets, data.ship)

            # turret bullets collide with the ship
            shootBullet(data, gameDisplay, data.playerBullets, data.turrets)
            # ship bullets collide with the turrets
            spawnObstacles(data,gameDisplay)
            data.timePassed = pygame.time.get_ticks() // 100 / 10
            # to help keep track of time in seconds.00
            data.clock.tick(data.fps)  #frames per second
            showScore(data,gameDisplay)

            if data.multi==False:
                if data.ship.die():
                    pageList=newPage(pageList,'dead')

            #Both Players must be dead
            elif data.multi:
                if not data.ship2.die():
                    shootBullet(data, gameDisplay, data.turretBullets, data.ship2)
                if data.ship.die() and data.ship2.die():
                    pageList=newPage(pageList,'dead')

        #when player loses or wins
        elif pageList['dead'] or pageList['winner']:
            pygame.mixer.music.stop()

            gameOver = pygame.image.load("gameOver.jpg")
            gameDisplay.blit(gameOver, (0, 0))

            exit=quitFunction()

            if pageList['dead']:
                mainText(data,gameDisplay,'Game Over!')
            elif pageList['winner']:
                mainText(data, gameDisplay, 'Level Completed!')

            scoreText = pygame.font.SysFont('impact', int(data.width / 20))
            scoreText = scoreText.render('score: %d' % (data.score), 1, (255, 255, 255))
            scoreTextRect = scoreText.get_rect(midtop=(data.width/2, data.height/2))
            gameDisplay.blit(scoreText, (scoreTextRect))


            if writeScore:
                scoreList = open('score.txt', 'a')
                scoreList.write(str(data.score) + '\n')
                scoreList.close()
                writeScore = False

            menuButton = buttonFunction(data,gameDisplay,'menu',data.height * 7 / 10)

            if menuButton:
                loadText = pygame.font.SysFont('impact', int(data.width / 20))
                loadText = loadText.render('loading...', 1, (255, 255, 255))
                offset=10
                loadTextRect = loadText.get_rect(topright=(data.width-offset, offset))
                gameDisplay.blit(loadText, (loadTextRect))

                pageList=newPage(pageList,'menu')
                startOver=True

        pygame.display.update()
    pygame.quit()

run(700,600)