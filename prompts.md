> cool that's great, Now i want to improvise our project by adding a new markddown file.\
  \There are two main puprposes of this file: one is for the next claude agents/claude conversations i run (similar to this) 
  to have a clear undersadning on the project than just relyting on high-level stuff available. The second purpose is for me 
  to understand what we did so far in detail. This detail need not involve extensive debugging or error fixing but maybe 
  something on a high level like for example: we faced X issue we resolved it using Y mcp.
   I know that we do have claude.md for that purpose but i feel i will be over expanding it if i add too much info. I am 
  saying this because i don't know how many times claude.md will be called internally. I feel now that it is only called at 
  the beginning of the conversation and later whenver it feels like it needs to.  \
  \I want to get best recommendations from you for this. Right now my thinking is to use something below context, please 
  understand that my thinking might be trivial and in-efficent, so correct me if i am wrong regarding the best practices.\
  1. use the #memorize command suggested by claude i saw earlier. However i don't know exactly what this does.\
  2. To use /compact or just after every long conversation generate text for the two puprposes i said earlier and put it 
  separately in some file like progress.md and reference it myself when neceessary and also refere it with @ inside claude.md
   but still i am not sure if i will burn too many tokens if i do the latter.