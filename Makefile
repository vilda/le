
# Based on http://savetheions.com/2010/01/20/packaging-python-applicationsmodules-for-debian/

BINDIR = $(DESTDIR)/usr/bin
clean:
	rm -f *.py[co] */*.py[co]
install:
	mkdir -p $(BINDIR)
	cp le $(BINDIR)/
	ln -s le $(BINDIR)/le-monitor
uninstall:
	rm -f $(BINDIR)/le
	rm -f $(BINDIR)/le-monitor

