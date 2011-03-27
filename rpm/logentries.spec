
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
Requires(post):		chkconfig
Requires(preun):	chkconfig
Requires(preun):	initscripts

%description
A command line utility for a convenient access to logentries logging infrastructure.

%prep
%setup -q

%build

%install
mkdir -p $RPM_BUILD_ROOT/usr/bin $RPM_BUILD_ROOT/etc/init.d
cp le $RPM_BUILD_ROOT/usr/bin
cp rpm/logentries $RPM_BUILD_ROOT/etc/init.d
ln -s le $RPM_BUILD_ROOT/usr/bin/le-monitordaemon
ln -s le $RPM_BUILD_ROOT/usr/bin/le-init
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
/etc/init.d/*

%post
/sbin/chkconfig --add logentries

%preun
if [ $1 -eq 0 ] ; then
	/sbin/service logentries stop >/dev/null 2>&1
	/sbin/chkconfig --del logentries
fi

%postun
if [ "$1" -ge "1" ] ; then
	/sbin/service logentries condrestart >/dev/null 2>&1 || :
fi

