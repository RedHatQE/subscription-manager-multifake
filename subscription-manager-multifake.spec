Name:		subscription-manager-multifake
Version:	0.2
Release:	1%{?dist}
Summary:	Use subscription-manager to register multiple (fake) systems

Group:		Development/Python
License:	GPLv3+
URL:		https://github.com/RedHatQE/subscripiton-manager-multifake
Source0:	%{name}-%{version}.tar.gz
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
BuildArch:  noarch

BuildRequires:	python-devel
Requires:	subscription-manager-migration-data

%description
%summary

%prep
%setup -q

%build

%install
mkdir -p $RPM_BUILD_ROOT%{_bindir}
cp %{name}.py $RPM_BUILD_ROOT%{_bindir}/%{name}

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%doc COPYING
%attr(0755, root, root) %{_bindir}/%{name}

%changelog
* Mon Sep 09 2013 Vitaly Kuznetsov <vitty@redhat.com> 0.2-1
- new package built with tito


