PACKAGE    = apng2gif
CC         = gcc
CFLAGS     = -Wall -pedantic
CFLAGS_OPT = -O2
LIBS       = -lstdc++ -lm -lpng -lz

all :
	$(CC) $(CFLAGS) $(CFLAGS_OPT) -o apng2gif apng2gif.cpp -s $(LIBS)

.PHONY : clean

clean : 
	rm -rf apng2gif
