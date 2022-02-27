form Script arguments
	sentence filename
	sentence outfilename
	positive start
	positive end
	real timeStep 0
	positive hertzMin 75
	positive hertzMax 600
	positive windowLength 0.01
endform
sound = Read from file: filename$
select sound
pitch = To Pitch... timeStep hertzMin hertzMax
select sound
plus pitch
pointproc=To PointProcess (cc)
select sound
plus pitch
plus pointproc
report$ = Voice report: start, end, 50, 600, 1.3, 1.6, 0.03, 0.45
report_filename$ = outfilename$
report$ > 'report_filename$'