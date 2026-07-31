import pytest

from psei.compliance import check_source


GUIDE_CASES = {
    "pages-5-6-formatting-and-comments": """
// this procedure swaps
// values of X and Y
PROCEDURE SWAP(BYREF X : INTEGER, Y : INTEGER)
   Temp ← X   // temporarily store X
   X ← Y
   Y ← Temp
ENDPROCEDURE
""",
    "pages-7-11-variables-and-arrays": """
CONSTANT HourlyRate = 6.50
DECLARE Counter : INTEGER
DECLARE StudentNames : ARRAY[1:30] OF STRING
DECLARE NoughtsAndCrosses : ARRAY[1:3,1:3] OF CHAR
Counter ← 0
StudentNames[1] ← "Ali"
NoughtsAndCrosses[2,3] ← 'X'
""",
    "pages-12-14-user-defined-types": """
TYPE Season = (Spring, Summer, Autumn, Winter)
TYPE TIntPointer = ^INTEGER
TYPE StudentRecord
   DECLARE LastName : STRING
   DECLARE YearGroup : INTEGER
ENDTYPE
TYPE LetterSet = SET OF CHAR
DEFINE Vowels ('A','E','I','O','U') : LetterSet
DECLARE Pupil : StudentRecord
DECLARE ThisSeason : Season
DECLARE MyPointer : TIntPointer
Pupil.LastName ← "Johnson"
ThisSeason ← Spring
""",
    "pages-15-17-common-operations": """
DECLARE ThisString : STRING
ThisString ← "ABCDEFGH"
OUTPUT RIGHT(ThisString, 3)
OUTPUT LENGTH("Happy Days")
OUTPUT MID(ThisString, 2, 3)
OUTPUT LCASE('W'), UCASE('h')
OUTPUT INT(27.5415), RAND(87)
""",
    "pages-18-21-selection-and-iteration": """
DECLARE Move : CHAR
DECLARE Position : INTEGER
CASE OF Move
   'W' : Position ← Position - 10
   'S' : Position ← Position + 10
   OTHERWISE :
      OUTPUT "Unknown"
ENDCASE
FOR Position ← 1 TO 10 STEP 2
   OUTPUT Position
NEXT Position
REPEAT
   Position ← Position - 1
UNTIL Position = 0
WHILE Position < 1
   Position ← Position + 1
ENDWHILE
""",
    "pages-22-24-procedures-and-functions": """
PROCEDURE Square(Size : INTEGER)
   FOR Side ← 1 TO 4
      OUTPUT Size
   NEXT Side
ENDPROCEDURE
FUNCTION Max(Number1 : INTEGER, Number2 : INTEGER) RETURNS INTEGER
   IF Number1 > Number2 THEN
      RETURN Number1
   ELSE
      RETURN Number2
   ENDIF
ENDFUNCTION
CALL Square(100)
OUTPUT Max(10, 20)
""",
    "pages-25-27-file-handling": """
DECLARE LineOfText : STRING
OPENFILE "FileA.txt" FOR READ
OPENFILE "FileB.txt" FOR WRITE
WHILE NOT EOF("FileA.txt")
   READFILE "FileA.txt", LineOfText
   WRITEFILE "FileB.txt", LineOfText
ENDWHILE
CLOSEFILE "FileA.txt"
CLOSEFILE "FileB.txt"
OPENFILE "StudentFile.Dat" FOR RANDOM
SEEK "StudentFile.Dat", 10
PUTRECORD "StudentFile.Dat", LineOfText
GETRECORD "StudentFile.Dat", LineOfText
CLOSEFILE "StudentFile.Dat"
""",
    "pages-28-29-object-oriented-programming": """
CLASS Pet
   PRIVATE Name : STRING
   PUBLIC PROCEDURE NEW(GivenName : STRING)
      Name ← GivenName
   ENDPROCEDURE
ENDCLASS
CLASS Cat INHERITS Pet
   PRIVATE Breed : STRING
   PUBLIC PROCEDURE NEW(GivenName : STRING, GivenBreed : STRING)
      SUPER.NEW(GivenName)
      Breed ← GivenBreed
   ENDPROCEDURE
ENDCLASS
DECLARE MyCat : Cat
MyCat ← NEW Cat("Kitty", "Shorthaired")
""",
}


@pytest.mark.parametrize(
    "source",
    GUIDE_CASES.values(),
    ids=GUIDE_CASES.keys(),
)
def test_guide_syntax_is_cambridge_2027_compliant(source):
    report = check_source(source.strip() + "\n")

    assert report.compliant, [
        diagnostic.format()
        for diagnostic in report.diagnostics
    ]
