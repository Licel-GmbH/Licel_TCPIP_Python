# Review 2023-07-15

## licel data.py

warum wird der Aufwand mit numpy.zeros  betrieben?


loop entfernen z.B. combine_Analog_Datasets_16bit und array funktionen benutzen

## licel_tcpip.py

\# note that sockFile.readline() change \r\n to only \n 
            response = str(self.sockFile.readline()) 
Ist das konfigurierbar? 

## licel_tr_tcpip.py

Das prüfen des Responses muss auf den Anfang bezogen werden und darf nur auf keinen Fall den Terminator beinhalten. Bei einigen Befehlen wird am Ende noch undokumentierte Debuginformation angehängt und die darf nicht zu einem Absturz des Programmes führen.

## sampleAquis.py

Da sind offensichtlich mehrere Funktionen die da herausgezogen werden können.


*Ausserdem scheint das Datenmodel nicht richtig zu sein.*

`TRType = Rack.TRtype()` ist einfach falsch egal wie man es nimmt. In einem Rack sind TR, PMT , APD usw. TRType macht nur Sinn auf einem TR object.

