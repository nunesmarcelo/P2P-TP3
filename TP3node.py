#!/usr/bin/python3

#   TP 3 - Redes - P2P
#   Marcelo Nunes da Silva
#   Wanderson Sena

import select , socket , sys , os , threading , struct

class TP3node:
    def __init__(self):
        if(len(sys.argv) < 3): 
            print("./TP3node <porto-local> <banco-chave-valor> [ip1:porto1 [ip2:porto2 ...]]")
            os._exit(1)

        try:
            self.port = sys.argv[1]

            self.socketsList = {}
            self.portsList = {}

            self.receivedMessages = []

            # Read dict -> key value from file
            self.readDb()

            # Create server socket before start listen
            self.createGeneralSocket()

            # Read list of neighbors in argv
            self.readInputNeighbors()

            # Create select for listen I/O  (using select function)
            self.startListenIO()

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
            
            # Create a TCP/IP socket
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setblocking(0)

            # Bind the socket to the port
            server_address = ('', int(self.port))
            print (  'starting up on %s port %s' % server_address)
            server.bind(server_address)

            # Listen for incoming connections 
            server.listen()

            # Sockets from which we expect to read
            self.socketsList['0'] = server
            #self.portsList['0'] = 'server'
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except socket.error:
            os._exit(1)
     
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
                    self.portsList[ address ] = 0
                except ConnectionRefusedError:
                    print("Connection failure. " , address)
        except KeyboardInterrupt:
            raise KeyboardInterrupt

    def startListenIO(self):
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

                            # ID   KEYREQ TOPOREQ KEYFLOOD TOPOFLOOD RESP
                            # 4    5      6       7        8         9
                            valueType = struct.unpack('>h', data)[0] 
                            
                            # ID
                            if(valueType == 4):
                                portOrZero = struct.unpack('>h', sock.recv(2) )[0] # receive message type
                                print("Chegou mensagem tipo ID, porto:" , portOrZero)
                                if sock.getpeername() not in self.socketsList:
                                    print("não estava na lista!")
                                    os._exit(1)
                                self.portsList[ sock.getpeername() ] = portOrZero

                            # KEYREQ
                            elif(valueType == 5 ):
                                nseq = struct.unpack('>i', sock.recv(4) )[0] # unpack: > big-endian , i integer - 4 bytes
                                tamanho = struct.unpack('>h' , sock.recv(2))[0] # unpack: > big-endian , h short integer - 2 bytes
                                
                                searchedKey = ""
                                i=0
                                while( i < tamanho):
                                    searchedKey += bytes.decode( sock.recv(1) )
                                    i+=1

                                # Mounting KEYFLOOD MESSAGE 
                                self.createKEYFLOODorTOPOFLOOD(7,4,nseq,sock.getpeername()[0], self.portsList[ sock.getpeername() ], len(searchedKey) , searchedKey)

                            # TOPOREQ
                            elif(valueType == 6):
                               nseq = struct.unpack('>i', sock.recv(4) )[0] # unpack: > big-endian , i integer - 4 bytes
                               self.createKEYFLOODorTOPOFLOOD(6,4,nseq,sock.getpeername()[0] , self.socketsList(sock.getpeername()),0,"" )
                            # KEYFLOOD
                            elif(valueType == 7 or valueType == 8):
                                ttl = struct.unpack('>h', sock.recv(2) )[0]        # unpack: > big-endian , h short integer - 2 bytes
                                nseq = struct.unpack('>i', sock.recv(4) )[0]       # unpack: > big-endian , i integer - 4 bytes
                                ip_orig = socket.inet_ntoa( sock.recv(4) )         # Convert a 32-bit packed IPv4 address (a string four characters in length) to its standard dotted-quad string
                                porto_orig = struct.unpack('>h', sock.recv(2) )[0] # unpack: > big-endian , h short integer - 2 bytes
                                tamanho = struct.unpack('>h', sock.recv(2) )[0]    # unpack: > big-endian , h short integer - 2 bytes
                                
                                info = ""
                                i=0
                                while( i < tamanho):
                                    info += bytes.decode( sock.recv(1) )
                                    i+=1

                                self.createKEYFLOODorTOPOFLOOD(valueType,ttl,nseq,ip_orig,porto_orig,len(info),info)
                        else:
                            # Interpret empty result as closed connection
                            print (  'closing ', sock.getpeername(), ' after reading no data')
                            # Stop listening for input on the connection
                            del self.socketsList[sock.getpeername()]
                            sock.close()
        except KeyboardInterrupt:
            raise KeyboardInterrupt

    def replyToClient(self ,nseq, data , ip , port):
        # +---- 2 ---+-- 4 -+--- 2 ---+----------\\---------------+
        # | TIPO = 9 | NSEQ | TAMANHO | VALOR (at´e 400 carateres) |
        # +----------+------+---------+----------\\---------------+
        messageRESP = struct.pack('>h', 9) + struct.pack('>i', nseq) + struct.pack('>h', len(data)) 
        messageRESP += str.encode( data )

        # Temporary connection to send the message.
        try:
            tempSocket = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
            tempSocket.connect( ( ip, port ) )
            tempSocket.send( messageRESP )
            tempSocket.close()
            print("enviado: " , data)
        except socket.error:
            print("Connection failure with the port informed.")

    def createKEYFLOODorTOPOFLOOD(self , tipo , ttl, nseq , ip_orig , porto_orig , tamanho , info):
        #+---- 2 ------+- 2 -+-- 4 -+--- 4 ---+----- 2 ----+--- 2 ---+----------\\--------------+
        #| TIPO = 7, 8 | TTL | NSEQ | IP_ORIG | PORTO_ORIG | TAMANHO | INFO (até 400 carateres) |
        #+-------------+-----+------+---------+------------+---------+----------\\--------------+

        ttl -= 1
        # repeated message or ttl expired = failure.
        if( (ip_orig,porto_orig,nseq) in self.receivedMessages or ttl == 0):
            return

        self.receivedMessages.append( (ip_orig,porto_orig,nseq) )

        # If my db has this key, send this value to client:
        if( (tipo == 5 or tipo == 7) and info in self.db.keys()):
            # data = db value , ip = ip of sender , port = port that client gave me , nseq = came inside the package
            self.replyToClient(nseq ,  self.db[info] , ip_orig , porto_orig )
        if( tipo == 6 or tipo == 8):
            info += str( socket.gethostbyname(socket.getfqdn())) + ":" + str(self.port) + " "  
            tamanho += len( str( socket.gethostbyname(socket.getfqdn()) ) + ":" + str(self.port) + " "   )
            self.replyToClient(nseq , info , ip_orig , porto_orig)

        # Flood data
        message = (struct.pack('>h', tipo) +
            struct.pack('>h', ttl) +        # pack: > big-endian , h short integer - 2 bytes
            struct.pack('>i', nseq) +       # pack: > big-endian , i integer - 4 bytes
            socket.inet_aton( ip_orig ) +   # IPv4 address from dotted-quad string format (ex: ‘123.45.67.89’) to 32-bit packed binary format
            struct.pack('>h', porto_orig) + # pack: > big-endian , h short integer - 2 bytes
            struct.pack('>h', len(info)) +  # pack: > big-endian , h short integer - 2 bytes
            str.encode(info))
        
        for neighbor in self.socketsList:
            self.socketsList[ neighbor ].send(message)

            # broken pipe...
    



if __name__ == "__main__":
    try:
        node = TP3node()
    except KeyboardInterrupt:
        os._exit(0)