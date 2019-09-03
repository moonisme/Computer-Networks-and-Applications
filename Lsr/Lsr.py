import sys
import threading
from socket import *

UPDATE_INTERVAL = 1
ROUTE_UPDATE_INTERVAL = 30
HEART_BEAT = 3

class Link:
    def __init__(self,neighbour,dist):
        self.neighbour = neighbour
        self.dist = dist

class Router:
    def __init__(self,id,port):
        self.id = id
        self.port = port
        self.links = []

    def insert_link(self,id,dist):
        link = Link(id,dist)
        self.links.append(link)

def link_state_packet(message):
    message = message.split('\n')
    message.pop(-1)
    source = Router(message[0],message[1])  #(ID,PORT)
    neighbour_num = int(message[2])
    destinations = []
    for i in range(3,neighbour_num+3):
        info = message[i].split()           # ['B', '6.5' , '5051'] ['F','2.2','5055']
        destinations.append(info[0])
        source.insert_link(Router(info[0],int(info[2])),float(info[1]))
    return (source, destinations)

def send_packets(source):
    global localhost
    global message
    global sent_message
    sent_message = set()
    for i in source.links:
        socket.sendto(message,(localhost,i.neighbour.port))
    Thread_A = threading.Timer(UPDATE_INTERVAL,send_packets,[source])
    Thread_A.daemon = True
    Thread_A.start()

def heartbeat():
    global alive
    global routers
    dead = []
    for i in alive.keys():
        if alive[i] == 0:
            dead.append(i)
            #print('Router '+str(i)+' is dead.')
    for i in routers:
        if i.id in dead:
            alive.pop(i.id)
            routers.remove(i)
    for i in alive.keys():
        alive[i] = 0
    Thread_B = threading.Timer(HEART_BEAT,heartbeat)
    Thread_B.daemon = True
    Thread_B.start()

def Dijkstra(source, routers):
    path = [source.id]
    dist = {source.id:0}
    previous = {source.id:source.id}
    visited = []
    while len(path) > 0:
        for i in path:
            min = dist[i]
            nearest_router = i
            if dist[i] < min:
                nearest_router = i
        count = 0
        path.remove(nearest_router)
        for i in routers:
            if i.id == nearest_router:
                current = i
                break
            count +=1
        if count == len(routers):
            continue
        visited.append(current.id)
        for i in current.links:
             total = i.dist + float(dist[current.id])
             if not i.neighbour.id in dist.keys():
                 dist[i.neighbour.id] = total
                 previous[i.neighbour.id] = current.id
             elif total < dist[i.neighbour.id]:
                 dist[i.neighbour.id] = total
                 previous[i.neighbour.id] = current.id
             if i.neighbour.id not in path and i.neighbour.id not in visited:
                 path.append(i.neighbour.id)
    print('I am router ' + str(source.id))
    for i in routers:
        if i != source:
            path = str(i.id)
            curr = i.id
            while previous[curr] != source.id:
                path = previous[curr] + path
                curr = previous[curr]
            path = source.id + path
            print('least-cost path to node '+str(i.id)+': '+str(path)+' and the cost is '+str(dist[i.id]))
    Thread_C = threading.Timer(ROUTE_UPDATE_INTERVAL,Dijkstra,[source,routers])
    Thread_C.daemon = True
    Thread_C.start()

if __name__=='__main__':

    config_file = sys.argv[1]
    with open(config_file) as f:
        info = f.readline()
        message = f.read()
    start_router = info[0]
    start_router_port = info[2:]

    source = Router(start_router,start_router_port)
    message = start_router + '\n' + str(start_router_port) + message
    source, destinations = link_state_packet(message)

    localhost = '127.0.0.1'
    socket = socket(AF_INET,SOCK_DGRAM)
    socket.bind((localhost,int(start_router_port)))

    routers = [source]
    sent_message = set()
    alive = {}
    send_packets(source)
    heartbeat()
    Dijkstra(source,routers)

    while True:
        broadcast,source_router = socket.recvfrom(4096)
        neighbours,destinations = link_state_packet(broadcast)
        source_router_port = source_router[1]
        destinations.append(neighbours.id)

        for i in source.links:
            if i.neighbour.id not in destinations and i.neighbour.port != source_router_port and neighbours.id not in sent_message:
                socket.sendto(broadcast,(localhost,i.neighbour.port))
        sent_message.add(neighbours.id)
        status = False
        for i in routers:
            if neighbours.id == i.id and alive:
                status = True
                alive[neighbours.id] += 1
            else:
                pass
        if not status:
            alive[neighbours.id] = 0
            routers.append(neighbours)
            for i in alive.keys():
                alive[i] = 0
