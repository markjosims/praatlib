form Script arguments
	sentence filename
	real timeStep 0
	positive hertzMin 75
	positive hertzMax 600
	positive windowLength 0.01
endform
file = Read from file: filename$
select file
pitch = To Pitch... timeStep hertzMin hertzMax
select pitch
matrix = To Matrix
pitchFilename$ = replace$ (filename$, ".wav", "PITCH.Matrix", 0)
Save as text file: pitchFilename$