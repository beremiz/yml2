110 DATA "Meier", "Uhlmannstrasse 42", "Laupheim"
120 DATA "Schmidt", "Haupstrasse 23", "Bad Waldsee"
1000 FOR I=1 TO 2 STEP 1
1010 READ NAME$, STREET$, VILLAGE$
1020 PRINT "INSERT INTO address (name, street, village) VALUES ('" + NAME$ + "', '" + STREET$ + "', '" + VILLAGE$ + "');"
1030 NEXT I