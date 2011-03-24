
# Based on http://savetheions.com/2010/01/20/packaging-python-applicationsmodules-for-debian/

BINDIR = $(DESTDIR)/usr/bin
clean:
	rm -f *.py[co] */*.py[co]
install:
	mkdir -p $(BINDIR)
	cp le $(BINDIR)/
	ln -s le $(BINDIR)/le-init
	ln -s le $(BINDIR)/le-reinit
	ln -s le $(BINDIR)/le-register
	ln -s le $(BINDIR)/le-monitor
	ln -s le $(BINDIR)/le-follow
	ln -s le $(BINDIR)/le-ls
	ln -s le $(BINDIR)/le-rm
	ln -s le $(BINDIR)/le-push
	ln -s le $(BINDIR)/le-pull
uninstall:
	rm -f $(BINDIR)/le
	rm -f $(BINDIR)/le-init
	rm -f $(BINDIR)/le-reinit
	rm -f $(BINDIR)/le-register
	rm -f $(BINDIR)/le-monitor
	rm -f $(BINDIR)/le-follow
	rm -f $(BINDIR)/le-ls
	rm -f $(BINDIR)/le-rm
	rm -f $(BINDIR)/le-push
	rm -f $(BINDIR)/le-pull

