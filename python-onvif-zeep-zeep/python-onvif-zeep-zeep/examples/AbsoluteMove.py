import asyncio, sys, os
from onvif import ONVIFCamera
import time

IP="192.168.1.64"   # Camera IP address
PORT=80           # Port
USER="admin"         # Username
PASS="intflow3121"        # Password


XMAX = 1
XMIN = -1
XNOW = 0.5
YMAX = 1
YMIN = -1
YNOW = 0.5
Move = 0.1
Velocity = 1
Zoom = 0
positionrequest = None
ptz = None
active = False
ptz_configuration_options = None
media_profile = None

def do_move(ptz, request):
    
    global active
    if active:
        ptz.Stop({'ProfileToken': request.ProfileToken})
    active = True
    ptz.AbsoluteMove(request)

def move_up(ptz, request):
    
    if YNOW - Move <= -1:
        request.Position.PanTilt.y = YNOW
    else:
        request.Position.PanTilt.y = YNOW - Move

    
    do_move(ptz, request)

def move_down(ptz, request):
    
    if YNOW + Move >= 1:
        request.Position.PanTilt.y = YNOW
    else:
        request.Position.PanTilt.y = YNOW + Move
    
    
    do_move(ptz, request)
 
def move_right(ptz, request):

    if XNOW - Move >= -0.99:
        request.Position.PanTilt.x = XNOW - Move
    elif abs(XNOW + Move) >= 0.0:
        request.Position.PanTilt.x = abs(XNOW) - Move
    elif abs(XNOW) <= 0.01:
        request.Position.PanTilt.x = XNOW
    
    request.Position.PanTilt.y = YNOW
    do_move(ptz, request)

def move_left(ptz, request):
    
    if XNOW + Move <= 1.0:
        request.Position.PanTilt.x = XNOW + Move
    elif XNOW <= 1.0 and XNOW > 0.99:
        request.Position.PanTilt.x = -XNOW
    elif XNOW < 0:
        request.Position.PanTilt.x = XNOW + Move
    elif XNOW <= -0.105556 and XNOW > -0.11:
        request.Position.PanTilt.x = XNOW
    
    request.Position.PanTilt.y = YNOW
    do_move(ptz, request)
    

def move_upleft(ptz, request):

    if YNOW == -1:
        request.Position.PanTilt.y = YNOW
    else:
        request.Position.PanTilt.y = YNOW - Move
    if XNOW + Move <= 1.0:
        request.Position.PanTilt.x = XNOW + Move
    elif XNOW <= 1.0 and XNOW > 0.99:
        request.Position.PanTilt.x = -XNOW
    elif XNOW < 0:
        request.Position.PanTilt.x = XNOW + Move
    elif XNOW <= -0.105556 and XNOW > -0.11:
        request.Position.PanTilt.x = XNOW
    do_move(ptz, request)
    
def move_upright(ptz, request):
    
    if YNOW == -1:
        request.Position.PanTilt.y = YNOW
    else:
        request.Position.PanTilt.y = YNOW - Move
    
    if XNOW - Move >= -0.99:
        request.Position.PanTilt.x = XNOW - Move
    elif abs(XNOW + Move) >= 0.0:
        request.Position.PanTilt.x = abs(XNOW) - Move
    elif abs(XNOW) <= 0.01:
        request.Position.PanTilt.x = XNOW
    
    do_move(ptz, request)
    
def move_downleft(ptz, request):

    if YNOW - Move == 1:
        request.Position.PanTilt.y = YNOW
    else:
        request.Position.PanTilt.y = YNOW - Move
  
    if XNOW + Move <= 1.0:
        request.Position.PanTilt.x = XNOW + Move
    elif XNOW <= 1.0 and XNOW > 0.99:
        request.Position.PanTilt.x = -XNOW
    elif XNOW < 0:
        request.Position.PanTilt.x = XNOW + Move
    elif XNOW <= -0.105556 and XNOW > -0.11:
        request.Position.PanTilt.x = XNOW
   
    do_move(ptz, request)
    
def move_downright(ptz, request):

    if YNOW == -1:
        request.Position.PanTilt.y = YNOW
    else:
        request.Position.PanTilt.y = YNOW - Move

    if XNOW - Move >= -0.99:
        request.Position.PanTilt.x = XNOW - Move
    elif abs(XNOW + Move) >= 0.0:
        request.Position.PanTilt.x = abs(XNOW) - Move
    elif abs(XNOW) <= 0.01:
        request.Position.PanTilt.x = XNOW
    
    do_move(ptz, request)

def Zoom_in(ptz,request):

    if Zoom + Move >= 1.0:
        request.Position.Zoom = 1.0
    else:
        request.Position.Zoom = Zoom + Move
    do_move(ptz, request)

def Zoom_out(ptz,request):

    if Zoom - Move <= 0.0:
        request.Position.Zoom = 0.0
    else:
        request.Position.Zoom = Zoom - Move
    do_move(ptz,request)

def setup_move():
    mycam = ONVIFCamera(IP, PORT, USER, PASS)
    # Create media service object
    media = mycam.create_media_service()
    
    # Create ptz service object
    global ptz , ptz_configuration_options, media_profile
    ptz = mycam.create_ptz_service()

    # Get target profile
    media_profile = media.GetProfiles()[0]

    
    request = ptz.create_type('GetConfigurationOptions')
    request.ConfigurationToken = media_profile.PTZConfiguration.token
    ptz_configuration_options = ptz.GetConfigurationOptions(request)

    request_configuration = ptz.create_type('GetConfiguration')
    request_configuration.PTZConfigurationToken  = media_profile.PTZConfiguration.token
    ptz_configuration = ptz.GetConfiguration(request_configuration)

    request_setconfiguration = ptz.create_type('SetConfiguration')
    request_setconfiguration.PTZConfiguration = ptz_configuration

    global  positionrequest
    
    positionrequest = ptz.create_type('AbsoluteMove')
    positionrequest.ProfileToken = media_profile.token

    if positionrequest.Position is None :
        positionrequest.Position = ptz.GetStatus({'ProfileToken': media_profile.token}).Position
        positionrequest.Position.PanTilt.space = ptz_configuration_options.Spaces.AbsolutePanTiltPositionSpace[0].URI
        positionrequest.Position.Zoom.space = ptz_configuration_options.Spaces.AbsoluteZoomPositionSpace[0].URI
    if positionrequest.Speed is None :
        positionrequest.Speed = ptz.GetStatus({'ProfileToken': media_profile.token}).Position
        positionrequest.Speed.PanTilt.space = ptz_configuration_options.Spaces.PanTiltSpeedSpace[0].URI
 
def Get_Status():
    # Get range of pan and tilt
    global XMAX, XMIN, YMAX, YMIN, XNOW, YNOW, Velocity, Zoom
    XMAX = ptz_configuration_options.Spaces.AbsolutePanTiltPositionSpace[0].XRange.Max
    XMIN = ptz_configuration_options.Spaces.AbsolutePanTiltPositionSpace[0].XRange.Min
    YMAX = ptz_configuration_options.Spaces.AbsolutePanTiltPositionSpace[0].YRange.Max
    YMIN = ptz_configuration_options.Spaces.AbsolutePanTiltPositionSpace[0].YRange.Min
    XNOW = ptz.GetStatus({'ProfileToken': media_profile.token}).Position.PanTilt.x
    YNOW = ptz.GetStatus({'ProfileToken': media_profile.token}).Position.PanTilt.y
    Velocity = ptz_configuration_options.Spaces.PanTiltSpeedSpace[0].XRange.Max
    Zoom = ptz.GetStatus({'ProfileToken': media_profile.token}).Position.Zoom.x


def readin():
    """Reading from stdin and displaying menu"""
    global positionrequest, ptz
    
    selection = sys.stdin.readline().strip("\n")
    lov=[ x for x in selection.split(" ") if x != ""]
    if lov:
        
        if lov[0].lower() in ["u","up"]:
            move_up(ptz,positionrequest)
        elif lov[0].lower() in ["d","do","dow","down"]:
            move_down(ptz,positionrequest)
        elif lov[0].lower() in ["l","le","lef","left"]:
            move_left(ptz,positionrequest)
        elif lov[0].lower() in ["l","le","lef","left"]:
            move_left(ptz,positionrequest)
        elif lov[0].lower() in ["r","ri","rig","righ","right"]:
            move_right(ptz,positionrequest)
        elif lov[0].lower() in ["ul"]:
            move_upleft(ptz,positionrequest)
        elif lov[0].lower() in ["ur"]:
            move_upright(ptz,positionrequest)
        elif lov[0].lower() in ["dl"]:
            move_downleft(ptz,positionrequest)
        elif lov[0].lower() in ["dr"]:
            move_downright(ptz,positionrequest)
        elif lov[0].lower() in ["s","st","sto","stop"]:
            ptz.Stop({'ProfileToken': positionrequest.ProfileToken})
            active = False
        else:
            print("What are you asking?\tI only know, 'up','down','left','right', 'ul' (up left), \n\t\t\t'ur' (up right), 'dl' (down left), 'dr' (down right) and 'stop'")
         
    print("")
    print("Your command: ", end='',flush=True)

# Test  Define      
# def move(ptz, request):
    
#     request.Position.PanTilt.y = -1
#     request.Position.PanTilt.x = 0

#     do_move(ptz,request)

if __name__ == '__main__':

    setup_move()
    # Get_Status()
    # Zoom_out(ptz,positionrequest)
    # Get_Status()
    # move(ptz,positionrequest)
    while True:
        if active == True:
            time.sleep(1)
            active = False
        else:
            Get_Status()
 
            move_up(ptz, positionrequest)