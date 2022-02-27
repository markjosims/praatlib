form Script arguments
	sentence filename
endform
file = Read from file: filename$
select file
tg = To TextGrid: "phoneme word lemma gloss speaker", ""
tgFilename$ = replace$ (filename$, ".wav", ".TextGrid", 0)

Save as text file: tgFilename$