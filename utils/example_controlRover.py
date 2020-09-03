### Source Code from Sven Erik Jeroschewski for controlling a rover ###
#!/usr/bin/python3
from bottle import route, request, run, static_file
from os import path
import json
import proton
from cli_proton_python import sender
import timeout_decorator

#check for flag files here
FILE="/tmp/email"

device = "roverInst"
host = "40.114.234.49:5672" # "13.81.24.150:5672" # please change the IP address based on the address of Hono instance.
username = "consumer@HONO"
password = "verysecret"
speed = 380
topic_to_publish = "control/DEFAULT_TENANT/"

class Speed:
    def get(self):
        return 0

speed_var = Speed() 

@timeout_decorator.timeout(3)
def sendControlMsg( msg ):
    print ("sending control msg " + str(msg))
    parser = sender.options.SenderOptions()
    opts,_= parser.parse_args()
    opts.broker_url = username + ":" + password +"@"+ host +"/"+ topic_to_publish + device
    opts.count = 1
    opts.msg_content = str(msg)
    opts.msg_id = '1'
    opts.msg_subject = 'light'
    opts.msg_reply_to = 'control/DEFAULT_TENANT/cmd1'
    opts.logs_msgs = 'dict'

    container = proton.reactor.Container(sender.Send(opts))
    container.run()

@route('/turn_right', method='POST')
def turn_right():
    sendControlMsg( "{\"mode\":0,\"command\":\"E\",\"speed\":"+ str(speed_var.get() + 360) +" }" )
    print("turn right clicked")

@route('/turn_right_back', method='POST')
def turn_right_back():
    sendControlMsg( "{\"mode\":0,\"command\":\"D\",\"speed\": "+ str(speed_var.get() + 360) +" }" )
    print("turn right back clicked")

@route('/turn_left', method='POST')
def turn_left():
   sendControlMsg("{\"mode\":0,\"command\":\"Q\",\"speed\": "+ str(speed_var.get() + 360) +" }")
   print("turn left clicked")

@route('/turn_left_back', method='POST')
def turn_left_back():
   sendControlMsg("{\"mode\":0,\"command\":\"A\",\"speed\": "+ str(speed_var.get() + 360) +" }")
   print("turn left back clicked")

@route('/move_forward', method='POST')
def move_forward():
   sendControlMsg("{\"mode\":0,\"command\":\"W\",\"speed\": "+ str(speed_var.get() + 360) +" }")
   print("move forward clicked")

@route('/move_back', method='POST')
def move_back():
   sendControlMsg("{\"mode\":0,\"command\":\"S\",\"speed\": "+ str(speed_var.get() + 360) +" }")
   print("move back clicked")

@route('/spot_right', method='POST')
def spot_right():
   sendControlMsg("{\"mode\":0,\"command\":\"K\",\"speed\": "+ str(speed_var.get() + 360) +" }")
   print("move spot right clicked")

@route('/spot_left', method='POST')
def spot_left():
   sendControlMsg("{\"mode\":0,\"command\":\"J\",\"speed\": "+ str(speed_var.get() + 360) +" }")
   print("move spot left clicked")

@route('/stop_move', method='POST')
def stop_move():
   sendControlMsg("{\"mode\":0,\"command\":\"F\",\"speed\": "+ str(speed_var.get() + 360) +" }")
   print("Stop clicked")


def set_speed(event):
   speed = speed_var.get() + 360
   print("set speed to %d", speed)


#@route('/')
#def defpage():
#    return 'Running. Point browser to <a href="./frontend/index.html">frontend</a>'

@route('/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root='./app/clienthtml')
    
run(host='0.0.0.0', port=8080, debug=False)
