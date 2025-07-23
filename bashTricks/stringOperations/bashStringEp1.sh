### Find a substtring in string
MAINVAR="full-text"
SUBSTR="text"
if echo "$MAINVAR" | grep -q "$SUBSTR"; then
    echo "Substring $SUBSTR found in $MAINVAR";
else
    echo "Substring is not present in the string";
fi

### Get a substtring with a start position & number of characrets to pick
GETSUBSTR=${MAINVAR:5:9}
echo $GETSUBSTR

### Replace character(s) in  a string
RPVAR=${MAINVAR//-/.} # replace - with . (dot)
echo $RPVAR
