#!/usr/bin/python3

#   TP 3 - Redes - P2P
#   Marcelo Nunes da Silva
#   Wanderson Sena

import select , socket , sys , os , threading , struct

class TP3node:
    def __init__(self):
        if(len(sys.argv) < 3): 
            os._exit()

        try:
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

        except KeyboardInterrupt:
            print("Removendo IPs...")
            for x in self.socketsList:
                self.socketsList[x].close() 
            os._exit(1)
        
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
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            print(e)

    def createGeneralSocket(self):
        try:
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
        except KeyboardInterrupt:
            raise KeyboardInterrupt
     
    def readInputNeighbors(self):
        try:
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
                    self.typesList[ address ] = 0
                except ConnectionRefusedError:
                    print("Connection failure. " , address)
        except KeyboardInterrupt:
            raise KeyboardInterrupt

    def startListenConnections(self):
        try:
            while(self.socketsList):
                # Get the list of sockets which are readable
                read_sockets, write_sockets, error_sockets = select.select( [ self.socketsList[sock] for sock in self.socketsList ], [], [])
            
                for sock in read_sockets:
                    # If is a new connection
                    if sock is self.socketsList['0']:
                        # A "readable" server socket is ready to accept a connection
                        connection, client_address = sock.accept()
                        print ('new connection from: ', client_address)
                        connection.setblocking(0)
                        self.socketsList[client_address] = connection
                    # Else -> data is coming
                    else:
                        data = sock.recv(2)
                        
                        if data: # Connection is open yet
                            #               ID   KEYREQ TOPOREQ KEYFLOOD TOPOFLOOD RESP
                            #Valor de tipo  4    5      6       7        8         9
                            valueType = struct.unpack('>h', data)[0] 

                            if(valueType == 4):
                                portOrZero = struct.unpack('>h', sock.recv(2) )[0] # receive message type
                                print("Chegou mensagem tipo ID, porto:" , portOrZero)
                                if sock.getpeername() not in self.socketsList:
                                    print("não estava na lista!")
                                    os._exit(1)
                                self.typesList[ sock.getpeername() ] = portOrZero

                            elif(valueType == 5):
                                nseq = struct.unpack('>i', sock.recv(4) )[0] # unpack: > big-endian , i integer - 4 bytes
                                tamanho = struct.unpack('>h' , sock.recv(2))[0] # unpack: > big-endian , h short integer - 2 bytes
                                
                                searchedKey = ""
                                i=0
                                while( i < tamanho):
                                    searchedKey += bytes.decode( sock.recv(1) )
                                    i+=1

                                if(searchedKey in self.db.keys()):
                                    # data = db value , ip = ip of sender , port = port that client gave me , nseq = came inside the package
                                    self.replyToClient(self.db[searchedKey] , sock.getpeername()[0] , self.typesList[ sock.getpeername() ] , nseq)
                        else:
                            # Interpret empty result as closed connection
                            print (  'closing ', sock.getpeername(), ' after reading no data')
                            # Stop listening for input on the connection
                            del self.socketsList[sock.getpeername()]
                            sock.close()
        except KeyboardInterrupt:
            raise KeyboardInterrupt

    def replyToClient(self , data , ip , port , nseq):
        # +---- 2 ---+-- 4 -+--- 2 ---+----------\\---------------+
        # | TIPO = 9 | NSEQ | TAMANHO | VALOR (at´e 400 carateres) |
        # +----------+------+---------+----------\\---------------+
        messageRESP= struct.pack('>h', 9) + struct.pack('>i', nseq) + struct.pack('>h', len(data)) 
        messageRESP += str.encode( data )

        # Temporary connection to send the message.
        tempSocket = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
        tempSocket.connect( ( ip, port ) )
        tempSocket.send( messageKEYREQ )
        tempSocket.close()


# testsock = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
# testsock.connect(( sock.getpeername()[0] , portOrZero ))

# messageId = struct.pack('>h', 4) + struct.pack('>h', 0)   # pack : > big-endian , h short integer - 2 bytes
# # messageId is used to warn the other side
# testsock.send( messageId )




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