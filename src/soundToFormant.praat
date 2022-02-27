form Script arguments
	sentence filename
	sentence outfilename
	real timeStep 0
	natural formantMax 5
	positive hertzMax 5000
	positive windowLength 0.025
	positive preEmphasis 50
endform
file = Read from file: filename$
select file
formant = To Formant (burg)... timeStep formantMax hertzMax windowLength preEmphasis

Save as text file: outfilename$