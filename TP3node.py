#!/usr/bin/python3

#   TP 3 - Redes - P2P
#   Marcelo Nunes da Silva
#   Wanderson Sena

import select , socket , sys , os , threading , struct

class TP3node:
    def __init__(self):
        if(len(sys.argv) < 3): 
            os._exit()

        # { 'ip:port' : {'socket': <socket> , 'type': 'server/servent/client'} }
        self.socketsList = {}
        self.typesList = {}

        # Read dict -> key value from file
        self.readDb()

        # Create server socket before start listen
        self.createGeneralSocket()

        # Read list of neighbors in argv
        self.readInputNeighbors()

        # Create socket for listen connections (using select function)
        self.startListenConnections()


        print(self.socketsList)
        print(self.typesList)
        
        
    def readDb(self):
        try:
            self.db = {}

            with open(sys.argv[2]) as dbFile:
                line = dbFile.readline()
                while line:
                    if(line[0] != "#"):
                        self.db[ line.split(" ")[0] ] =  " ".join( line.split(" ")[1:]).replace('\n','')
                    line = dbFile.readline()

            #print(self.db)
        except AttributeError:
            print("File not found!")
        except Exception as e:
            print(e)

    def createGeneralSocket(self):
        self.port = sys.argv[1]

        # Create a TCP/IP socket
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setblocking(0)

        # Bind the socket to the port
        server_address = ('', int(self.port))
        print (  'starting up on %s port %s' % server_address)
        server.bind(server_address)

        # Listen for incoming connections - 1000 = arbitrary value. =)
        server.listen(1000)

        # Sockets from which we expect to read
        self.socketsList['0'] = server
        self.typesList['0'] = 'server'
     
    def readInputNeighbors(self):
        addresses = sys.argv[3:]
        for address in set(addresses):
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                conn.connect( (address.split(':')[0] , int( address.split(':')[1]) ) ) 

                # > big-endian, padrão do TCP/IP
                # h short integer - 2 bytes
                messageId = struct.pack('>h', 4) + struct.pack('>h', 0)   

                # messageId is used to warn the other side
                conn.send( messageId )
                self.socketsList[ address ] = conn
                self.typesList[ address ] = 'servent'
            except ConnectionRefusedError:
                print("Connection failure. " , address)

    def startListenConnections(self):
        while(self.socketsList):
            # Get the list sockets which are readable
            read_sockets, write_sockets, error_sockets = select.select( [ self.socketsList[sock] for sock in self.socketsList ], [], [])
		
            for sock in read_sockets:
                # If is a new connection
                if sock is self.socketsList['0']:
                    # A "readable" server socket is ready to accept a connection
                    connection, client_address = sock.accept()
                    print ('new connection from: ', client_address)
                    connection.setblocking(0)
                    self.socketsList[client_address] = connection
                # Else -> data coming
                else:
                    data = sock.recv(2) # receive message type
                    
                    if data:
                        messageType = struct.unpack('>h', data)[0]
                        print(messageType)
                        if(messageType == 4):
                            print("Chegou id!")
                            portOrZero = struct.unpack('>h', sock.recv(2) )[0] # receive message type
                            print("Port:" , portOrZero)
                            if sock.getpeername() not in self.socketsList:
                                print("não estava na lista!")
                                os._exit(1)
                            if portOrZero == 0:
                                self.typesList[ sock.getpeername() ] = 'servent'
                            else:
                                self.typesList[ sock.getpeername() ] = 'client'
                                # tratar casos de cliente, salvar porto para enviar dados.

                        print (  'received "%s" from %s' % (data, sock.getpeername()))
                        # Add output channel for response
                        

                    else:
                        # Interpret empty result as closed connection
                        print (  'closing', client_address, 'after reading no data')
                        # Stop listening for input on the connection
                        del self.socketsList[sock.getpeername()]
                        sock.close()







if __name__ == "__main__":
    try:
        node = TP3node()
    except KeyboardInterrupt:
        os._exit(0)

# while inputs:

#     # Wait for at least one of the sockets to be ready for processing
#     #print (  '\nwaiting for the next event')
#     readable, writable, exceptional = select.select(inputs, outputs, inputs)

#     # Handle inputs
#     for s in readable:
        
#         if s is server:
#             # A "readable" server socket is ready to accept a connection
#             connection, client_address = s.accept()
#             print (  'new connection from', client_address)
#             connection.setblocking(0)
#             inputs.append(connection)

#             # Give the connection a queue for data we want to send
#             message_queues[connection] = queue.Queue()

#         else:
#             data = bytes.decode( s.recv(1024) )
#             if data:
#                 # A readable client socket has data
#                 print (  'received "%s" from %s' % (data, s.getpeername()))
#                 message_queues[s].put(data)
#                 # Add output channel for response
#                 if s not in outputs:
#                     outputs.append(s)

#             else:
#                 # Interpret empty result as closed connection
#                 print (  'closing', client_address, 'after reading no data')
#                 # Stop listening for input on the connection
#                 if s in outputs:
#                     outputs.remove(s)
#                 inputs.remove(s)
#                 s.close()

#                 # Remove message queue
#                 del message_queues[s]
            
#     # Handle outputs
#     for s in writable:
#         try:
#             next_msg = message_queues[s].get_nowait()
#         except queue.Empty:
#             # No messages waiting so stop checking for writability.
#             print (  'output queue for', s.getpeername(), 'is empty')
#             outputs.remove(s)
#         else:
#             print (  'sending "%s" to %s' % (next_msg, s.getpeername()))
#             s.send( str.encode( next_msg) )
    
#     # Handle "exceptional conditions"
#     for s in exceptional:
#         print (  'handling exceptional condition for', s.getpeername())
#         # Stop listening for input on the connection
#         inputs.remove(s)
#         if s in outputs:
#             outputs.remove(s)
#         s.close()

#         # Remove message queue
#         del message_queues[s]