
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
mkdir -p $RPM_BUILD_ROOT/usr/bin
cp le $RPM_BUILD_ROOT/usr/bin

%files
%defattr(-,root,root)
/usr/bin/le

%post
/sbin/chkconfig --add logentries

%preun
if [ $1 -eq 0 ] ; then
	/sbin/service logentries stop >/dev/null 2>&1
	/sbin/chkconfig --del <script>
fi

%postun
if [ "$1" -ge "1" ] ; then
	/sbin/service logentries condrestart >/dev/null 2>&1 || :
fi

