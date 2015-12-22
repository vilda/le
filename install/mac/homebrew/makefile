VERSION=$(shell cd ../../../ && dpkg-parsechangelog --show-field Version)
SHA256SUM=$(shell cd /tmp && rm v${VERSION}.tar.gz && curl -s -O https://github.com/logentries/le/archive/v${VERSION}.tar.gz && sha256sum v${VERSION}.tar.gz | cut -f 1 -d ' ')

logentries.rb: logentries.rb.in
	sed -e s/@VERSION@/${VERSION}/ -e s/@SHA256SUM@/${SHA256SUM}/ logentries.rb.in > logentries.rb
