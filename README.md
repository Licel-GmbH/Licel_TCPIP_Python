# **Licel_TCPIP Python**  

**The Licel_TCPIP python library was developed and tested with python 3.10.11 .** 

**running this library with python version 3.8 will result in error** 
## Installing requirements: 
- pip install -r requirements.txt
## run sampleAcquis.py example : 

before running the example,\
set IP = " " and PORT = " " variables present in sampleAcquis.py line 10 and 11 to your desired IP and PORT 
- python3 sampleAcquis.py 

This example programme does the following:

- Open a connection to the rack specified by "IP" and "PORT"
- Get the identification string from the controller
- Select Transient recorder N° specified by "TR"
- Get transient recorder hardware information for the selected transient recorder 
- Set the input voltage range to "-100mV"
- Set the Threshold Mode "ON"
- Set the discriminator level to 8 
- Start the currently selected transient recorder acquisition 
- Stop the acquisition and wait for it to finish.  
- Get the shot number for each memory    
- Read a 13000 bin long trace of analogue data   
- Read a 4000 bin long trace of analogue squared data  
-  process raw analogue and analogue squared data and displays: 
- - scaled analogue data,
- - analogue standard deviation,
- - analogue mean error
- Read a 13000 bin long trace of photon counting data   
- Read a 4000 bin long trace of photon counting squared data  
-  process raw photon counting and photon counting squared data and displays: 
- - scaled photon counting data,
- - analogue photon counting deviation,
- - analogue photon counting error

**To view the next displays of data please press the exit button or "Q" on your keyboard**