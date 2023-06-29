import socket

'''
To do 
def openSecureConnection() 
def readResponse()
def GetPushData()
'''
class licelTCP(Exception): 

    run_PushThreads = False

    def __init__(self, ip: str, port : int) -> None:
        self.licelSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.licelPushSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.licelSocket.settimeout(2) # 1sec timeout 
        self.sockFile=self.licelSocket.makefile('rw')
        self.ip = ip
        self.port = port 
        self.pushPort = port + 1 
        
    
    def openConnection(self) -> None:
        try:
            self.licelSocket.connect((self.ip, self.port))
        except socket.timeout: 
            raise socket.timeout ("\nConnection timeout to IP: "+self.ip + " PORT: "+str(self.port))
        return
        

    def shutdownConnection(self) -> None: 
        self.licelSocket.close()
        return
    
    def openPushConnection(self) -> None:
        self.licelPushSocket.connect((self.ip, self.pushPort))
        return

    def shutdownPushConnection(self) -> None: 
        self.licelPushSocket.close()
        return

    def writeCommand(self,command: str) -> None:
        command = command+"\r\n"
        self.licelSocket.send(command.encode())
        return

    def readResponse(self) -> str: 
        try:
            # note that sockFile.readline() change \r\n to only \n 
            response = str(self.sockFile.readline()) 
            return response
        except socket.timeout: 
            return "response timeout"
    
    def recvall(self, n) -> bytearray:
        # Helper function to recv 2*n bytes or return None if EOF is hit
        data = bytearray()
        while len(data) < 2*n:
            packet = self.licelSocket.recv(2*n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data
    
    def recvPushData(self, n,queue) -> bytearray:
        # Helper function to recv 2*n bytes or return None if EOF is hit
        data = bytearray()
        while self.run_PushThreads:
            packet = self.licelPushSocket.recv(2*n)
            if packet:
                queue.put(packet)
                   
        return data
