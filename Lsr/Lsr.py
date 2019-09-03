# Python 3
import sys, threading, time
from socket import *
from decimal import Decimal

class Node():
    def __init__(self, router, port, edges, status, time):
        self.name = router
        self.port = port
        self.num_neighbours = 0
        self.neighbours = edges # dictionary
        self.status = status
        self.time = time

UPDATE_INTERVAL = 1
ROUTE_UPDATE_INTERVAL = 15
DEAD_NODE_INTERVAL = 10

def parse_config(config_file, my_node, graph):
    file = open(config_file)
    text = file.readlines()
    pos = 1
    my_node.num_neighbours = int(text[0])
    while pos <= my_node.num_neighbours:
        line = text[pos].split()
        my_node.neighbours.update({line[0] : float(line[1])})
        neighbours_ports.update({line[0] : int(line[2])})
        pos += 1


def add_new_node(link_state):
    packet = link_state.splitlines()
    new_node = Node(str(packet[0]), int(packet[1]), {}, True, time.time())
    pos = 4
    new_node.num_neighbours = int(packet[3])
    while (pos < (4 + new_node.num_neighbours)):
        line = packet[pos].split()
        new_node.neighbours.update({line[0] : float(line[1])})
        pos += 1 
    graph.update({new_node.name : new_node})


def find_dead_nodes(graph):
    for node in graph.values():
        if node.name == my_node.name: continue
        if DEAD_NODE_INTERVAL < (time.time() - float(node.time)):
            node.status = False
        else:
            node.status = True


def min_dist(vertex_set, dist):
    minimum_dist = float("inf")
    min_vertex = '-'
    for v in vertex_set:
        if dist[v] <= minimum_dist:
            min_vertex = v
            minimum_dist = dist[v]
    return min_vertex

# finds the shortest path from one node to another and returns that path
# code based on the psuedocode of Djikstra's algorithm as specified in : https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm
# Since I am using dictionaries, changes have been made in the implementation
def djikstra(end):
    vertex_set = set(); dist = {}; prev = {}
    for v in graph.values():
        if v.status == False: continue
        dist.update({v.name : float("inf")})
        prev.update({v.name: '-'})
        vertex_set.add(v.name)
    dist[my_node.name] = 0.0
    while vertex_set != set():
        # get minimum distance
        u = min_dist(vertex_set, dist)
        if u == end.name: break
        vertex_set.discard(u)
        for v in graph[u].neighbours:
            if graph[v].status == False: continue
            if v not in vertex_set: continue
            alt = dist[u] + graph[u].neighbours[v]
            if alt < dist[v]:
                dist[v] = alt
                prev[v] = u
    path = ""
    if prev[u] != '-' or u == my_node.name:
        while u != '-':
            path = u + path
            u = prev[u]
    cost = Decimal(dist[end.name])
    rounded_cost = round(cost,1)
    return (path, rounded_cost)
        
# thread a = receives packets
class Receive(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self, name=name)
        self.name = name
        self.end = False
    def run(self):
        while not self.end:
            server_socket = socket(AF_INET, SOCK_DGRAM)
            server_socket.bind(("127.0.0.1", port))
            # receive data
            link_packet = server_socket.recv(2000).decode("utf-8")
            # put it in (received = {})
            received.update({link_packet[0] : link_packet})
        

# thread b = determines if the received packets need to be sent, and then sends them if they do
class Restrict(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self, name=name)
        self.name = name
        self.end = False
    def run(self):
        while not self.end:
            # this copy avoids issues with 'dictionary changed size during iteration'
            received_copy = received.copy()
            for node in received_copy:
                if node == my_node.name: continue
                if received_copy.get(node) == restricted.get(node) and restricted.get(node) != None: continue
                # add it to the graph if new/update data
                if (restricted.get(node)) == None:
                        add_new_node(received_copy[node])
                else:
                    # update time and status a packet has been received from that node - for node failures
                    packet = restricted[node].splitlines()
                    graph[node].time = packet[2]
                # send packet
                restricted[node] = received_copy[node]
                for n_port in neighbours_ports.values():
                    neighbours_socket = socket(AF_INET, SOCK_DGRAM)
                    neighbours_socket.connect(("127.0.0.1", n_port))
                    neighbours_socket.send(restricted[node].encode())
                    neighbours_socket.close()
        

# thread c = sends own packets
class Send(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self, name=name)
        self.name = name
        self.end = False
    def run(self):
        while not self.end:
            # send packet
            link_state_packet = my_node.name + "\n" + str(port) + "\n" + str(time.time()) + "\n" + config_txt
            for n_port in neighbours_ports.values():
                neighbours_socket = socket(AF_INET, SOCK_DGRAM)
                neighbours_socket.connect(("127.0.0.1", n_port))
                neighbours_socket.send(link_state_packet.encode())   
                neighbours_socket.close()             
                time.sleep(UPDATE_INTERVAL)


# thread d = dijkstra's algorithm
class Djikstra(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self, name=name)
        self.name = name
        self.end = False
    def run(self):
        while not self.end:
            time.sleep(ROUTE_UPDATE_INTERVAL)
            # create vertex set
            # Q = {}; dist = {}; prev = ['0' * len(graph)]
            # find dead nodes and set their 'status' field to false if its been more than 10 seconds since we havent received a packet
            find_dead_nodes(graph)
            text = "I am Router " + my_node.name + "\n"
            # for each node:
            for v in graph.values():
                if v.name == my_node.name or v.status == False: continue
                result = djikstra(v)
                text += "Least cost path to router " + v.name + ": " + result[0] + " and the cost is " + str(result[1]) + "\n"
            print(text)
                


graph = {}; received = {}; restricted = {}; neighbours_ports = {}; config_txt = ""
router_id = str(sys.argv[1])
port = int(sys.argv[2])
config_file = str(sys.argv[3])
file = open(config_file)

text = file.readlines()
for line in text:
    config_txt = config_txt + line

my_node = Node(router_id, port, {}, True, time.time())
graph.update({my_node.name : my_node})
parse_config(config_file, my_node, graph)


# create threads
threads = []
receive_packets = Receive("Thread-1")
receive_packets.start()
threads.append(receive_packets)

restrict_transmission = Restrict("Thread-2")
restrict_transmission.start()
threads.append(restrict_transmission)

send_my_packets = Send("Thread-3")
send_my_packets.start()
threads.append(send_my_packets)

djikstras_algo = Djikstra("Thread-4")
djikstras_algo.start()
threads.append(djikstras_algo)



# Method for ending threads borrowed from https://jaytaylor.com/blog/2011/01/28/how-to-have-threads-exit-with-ctrl-c-in-python/ by Jay Taylor
while len(threads) > 0:
    try:
        threads = [t.join(1) for t in threads if t is not None and t.isAlive()]
    except KeyboardInterrupt:
        for t in threads:
            t.end = True
        exit()