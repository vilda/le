
%define _topdir	 	TOPDIR
%define name		logentries
%define release		RELEASE
%define version 	VERSION
%define buildroot %{_topdir}/%{name}-%{version}-root

BuildRoot:		%{buildroot}
Summary: 		Logentries agent
License: 		GPL
Name: 			%{name}
Version: 		%{version}
Release: 		%{release}
Source: 		%{name}-%{version}.tar.gz
Prefix: 		/usr
Group: 			Administration/Tools
Requires:		python-setuptools

%description
A command line utility for a convenient access to logentries logging infrastructure.

%prep
%setup -q

%build

%install
python setup.py install --root $RPM_BUILD_ROOT --install-lib=/usr/share/logentries --install-scripts=/usr/share/logentries
mkdir -p $RPM_BUILD_ROOT/usr/bin
mkdir -p $RPM_BUILD_ROOT/etc/.le
cp ca-certs.pem $RPM_BUILD_ROOT/etc/.le
ln -s /usr/share/logentries/le $RPM_BUILD_ROOT/usr/bin
ln -s le  $RPM_BUILD_ROOT/usr/bin/le-init
ln -s le $RPM_BUILD_ROOT/usr/bin/le-reinit
ln -s le $RPM_BUILD_ROOT/usr/bin/le-register
ln -s le $RPM_BUILD_ROOT/usr/bin/le-monitor
ln -s le $RPM_BUILD_ROOT/usr/bin/le-follow
ln -s le $RPM_BUILD_ROOT/usr/bin/le-ls
ln -s le $RPM_BUILD_ROOT/usr/bin/le-rm
ln -s le $RPM_BUILD_ROOT/usr/bin/le-push
ln -s le $RPM_BUILD_ROOT/usr/bin/le-pull


%files
%defattr(-,root,root)
/usr/bin/*
/usr/share/logentries/*
/etc/.le
