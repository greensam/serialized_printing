#! /bin/sh 

mkdir pdfs

for i in {1..5}
do
    echo $i
    pdflatex -output-directory=pdfs -jobname="serialize_$i" "\def\SERIAL{$i} \input{serialize.tex}" > /dev/null 2>&1
done

rm pdfs/*.aux pdfs/*.log

# "/System/Library/Automator/Combine PDF Pages.action/Contents/Resources/join.py" combined.pdf pdfs/serialize_*.pdf

# rm -r pdfs

