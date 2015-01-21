COMPILER=fsc
INTERPRETER=scala

# Scala compiler parameters
FLAGS=-deprecation -feature

LIBS=lib/luaj-jse-3.0-alpha1.jar

# Uncomment below to try the new libs
# LIBS=lib/luaj-jse-3.0.jar

MAIN=runtime.Main
CLASSES=classes
SOURCE=scala/*.scala scala/gui/*.scala scala/test/*.scala

# Documenters
DOCUMENTATION=doc/
DOCUMENTER_SCALA=scaladoc
DOCUMENTER_LUA=luadoc

build:
	@mkdir -p $(CLASSES)
	$(COMPILER) $(FLAGS) -d $(CLASSES) -cp $(LIBS) $(SOURCE)

run: build
	$(INTERPRETER) -cp $(CLASSES):$(LIBS) $(MAIN)

clean:
	rm -rf $(CLASSES)
	rm -rf $(DOCUMENTATION)

exit:
	$(COMPILER) -shutdown

doc-scala:
	@mkdir -p $(DOCUMENTATION)/scala/
	$(DOCUMENTER_SCALA) -cp $(CLASSES):$(LIBS) -d $(DOCUMENTATION)/scala/ $(SOURCE)

doc-lua:
	@mkdir -p $(DOCUMENTATION)/lua/
	cp Board.scala $(DOCUMENTATION)chakes.lua
	cd $(DOCUMENTATION); luadoc -d lua/ chakes.lua
	rm -f $(DOCUMENTATION)lib.lua
