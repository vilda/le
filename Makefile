
# Based on http://savetheions.com/2010/01/20/packaging-python-applicationsmodules-for-debian/

BINDIR = $(DESTDIR)/usr/bin
clean:
	rm -f *.py[co] */*.py[co]
install:
	mkdir -p $(BINDIR)
	cp le $(BINDIR)/
uninstall:
	rm -f $(BINDIR)/le

