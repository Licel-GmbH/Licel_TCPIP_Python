
from Licel import  licel_tcpip, licel_LaserSync

ip = "127.0.0.1"
port = 2055 
DEFAULT_PASSWORD = "Administrator"
def main():
    

    ethernetController = licel_tcpip.EthernetController (ip, port)
    ethernetController.openConnection()
    LaserSyncConfig = licel_LaserSync.LaserSyncConfig("Timing.ini")
    print(LaserSyncConfig.LaserSyncIniConfigPath)
    LaserSyncConfig.readConfig()
    print(LaserSyncConfig.Config.MasterCycles)
    LaserSync = licel_LaserSync.LaserSync(ethernetController)

    
    print(ethernetController.getCapabilities())
    print(LaserSync.getStoredConfig())
    print(LaserSync.setparam(LaserSyncConfig.Config))
    print(LaserSync.storeConfig(LaserSyncConfig.Config, DEFAULT_PASSWORD ))
    print(LaserSync.getStoredConfig())


    



if __name__ == "__main__":
    main()
