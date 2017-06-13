# kit_cannibalization
---
Generates report for cannibalization of implant kits 
to determine how many valid kits can be made from the invalid serials
in inventory by breaking out each kit serial and analyzing their contents.

Author: Ian Doarn

Contributors:
  - Patrick K. Schenkel
  - Tom Johnson
  - Natasha Askew

## Usage
------

```commandline
python cannibalize.py KIT_ID Serial1 Serial2 Serial3 ...
```

KIT_ID is the kit's product id, for example: 57-5988-012-00
'Serial1 Serial2 Serial3 ...' are the invalid serials associated with the
given kit id. Kit 57-5988-012-00 has 7 serial on hand, 6 of which are
invalid. So the input would look like:

```commandline
python analyze.py 57-5988-012-00 1 3 4 7 11 12
```

