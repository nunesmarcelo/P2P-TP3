#!/usr/bin/python3

#   TP 3 - Redes - P2P
#   Marcelo Nunes da Silva
#   Wanderson Sena


import socket , sys , os , struct , select

class TP3client:
    def __init__(self):
        if(len(sys.argv) < 3): 
            os._exit()

        self.port = sys.argv[1]
        self.serverIp = sys.argv[2]
        self.socketsList = { }
        self.socketsList['stdin'] = sys.stdin
        self.nseq = 0

        # Create accept socket and the socket to communicate with the servent.
        self.createInitialSockets()

        # Start to listen the user commands and the answer received from the servents
        self.listenCommandsAndAnswers()

    def createInitialSockets(self):
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create a TCP/IP socket
                client.setblocking(0)
                # Bind the socket to the port
                myaddress = ('', int(self.port))
                print (  'starting up on %s port %s' % myaddress)
                client.bind(myaddress)
                # Listen for incoming connections - 1000 =  high arbitrary value. =)
                client.listen(1000)

                self.socketsList['0'] = client
            except socket.error as e:
                print ('Could not bind the socket connection ' , e)
                os._exit(1)

            # Servent socket
            try:
                servent = socket.socket(socket.AF_INET, socket.SOCK_STREAM)# Create a TCP/IP socket
                servent.connect( ( self.serverIp.split(':')[0] , int( self.serverIp.split(':')[1] ) ) ) # connect to servent

                # > big-endian, padrão do TCP/IP
                # h short integer - 2 bytes
                messageId = struct.pack('>h', 4) + struct.pack('>h', int(self.port))   

                # messageId is used to warn the other side
                servent.send( messageId )
                # Sockets from which we expect to read
                self.socketsList[ self.serverIp]  = servent
            except ConnectionRefusedError:
                print("Connection failure. " , self.serverIp)
            except socket.error:
                print ('Could not connect to chat server ')
                os._exit(1)
            
    def listenCommandsAndAnswers(self):
        try:
            while(1):
                # Get the list sockets which are readable
                read_sockets, write_sockets, error_sockets = select.select( [ self.socketsList[sockeet] for sockeet in self.socketsList ], [], [])
                for sock in read_sockets:
                    # If is a new connection
                    if sock is self.socketsList['stdin']:
                        print(">>  " , end=" ")
                        command = sock.readline()
                        print(command)

                        if (command[0] == "?" and " " in command):
                            # read command and remove \n or \0 to avoid mistakes
                            searchedKey = command[2:].replace('\0',"").replace('\n',"")

                            messageKEYREQ = struct.pack('>h', 5) + struct.pack('>i', self.nseq) + struct.pack('>h', len(searchedKey)) 
                            messageKEYREQ += str.encode(searchedKey)
                            # Ask for the value in the key entered by the user
                            self.socketsList[self.serverIp].send( messageKEYREQ )

                        elif(command == "Q"):
                            raise KeyboardInterrupt
                        else:
                            print("Comando desconhecido")

                        #self.socketsList[ self.serverIp ].send()
                    elif sock is self.socketsList['0']:
                        # A "readable" server socket is ready to accept a connection
                        connection, client_address = sock.accept()
                        print ('new connection from: ', client_address)
                        connection.setblocking(0)
                        self.socketsList[client_address] = connection
                    else:
                        data = sock.recv(2) # receive message type
                        if data: # Connection is open yet
                            #               ID   KEYREQ TOPOREQ KEYFLOOD TOPOFLOOD RESP
                            #Valor de tipo  4    5      6       7        8         9
                            valueType = struct.unpack('>h', data)[0] 
                            if valueType == 9:
                                nseq = struct.pack('>i', sock.recv(2))[0]
                                tamanho =  struct.pack('>h', sock.recv(2))[0]
                                

                                # Terminar de receber o RESP no cliente... servidor já pegou a key, achou pra ele, e está 
                                #enviando de novo!!!! =)
                                i=0
                                 = ""
                                while(i < tamanho):

                                    i+=1
                        else:
                            raise KeyboardInterrupt
        except KeyboardInterrupt:
            print("Closing connections...")
            for x in self.socketsList:
                self.socketsList[x].close()
            os._exit(0)

if __name__ == "__main__":
    try:
        node = TP3client()
    except KeyboardInterrupt:
        for x in self.socketsList:
                self.socketsList[x].close()
        os._exit(0)