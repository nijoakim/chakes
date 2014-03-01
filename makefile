COMPILER=fsc
FLAGS=-deprecation
LIBS=lib/luaj-jse-3.0-alpha1.jar
INTERPRETER=scala
DOCUMENTER=scaladoc
DOCUMENTATION=doc
MAIN=runtime.Main
CLASSES=classes

build:
	@mkdir -p $(CLASSES)
	$(COMPILER) $(FLAGS) -d $(CLASSES) -cp $(LIBS) *.scala

run: build
	$(INTERPRETER) -cp $(CLASSES):$(LIBS) $(MAIN)

clean:
	rm -rf $(CLASSES)
	rm -rf $(DOCUMENTATION)

exit:
	$(COMPILER) -shutdown

document:
	@mkdir -p $(DOCUMENTATION)
	$(DOCUMENTER) -cp $(CLASSES):$(LIBS) -d $(DOCUMENTATION) *.scala
