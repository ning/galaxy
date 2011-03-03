%define gemversion %(ruby -rlib/galaxy/version -e 'puts Galaxy::Version.split("-", 1)[0]' 2>/dev/null)
%define gemname galaxy

Name: %{gemname}
Summary: Software deployment tool
Version: %{gemversion}
Release: %(ruby -rlib/galaxy/version -e 'puts Galaxy::Version.split("-", 2)[1] || "final"' 2>/dev/null)
License: Apache License, version 2.0
Group: Development/Tools/Other
URL: http://github.com/ning/galaxy
BuildArch: noarch
Requires: ruby
BuildRoot: /tmp/galaxy-package
Provides: rubygem(%{gemname}) = %{gemversion}

Requires(pre): /usr/sbin/useradd, /usr/bin/getent
Requires(postun): /usr/sbin/userdel

%pre
/usr/bin/getent group xncore || /usr/sbin/groupadd -r xncore
/usr/bin/getent passwd xncore || /usr/sbin/useradd -r -m -d /home/xncore -s /sbin/nologin -g xncore xncore 

%define gem %(ruby -rlib/galaxy/version -e 'puts "galaxy-#{Galaxy::Version}.gem"')

# Use rpmbuild --define "_gonsole_url gonsole.prod.company.com" to customize
# galaxy.{client,agent}.console in galaxy.conf
%{?!_gonsole_url: %define _gonsole_url GONSOLE_URL}

# Use rpmbuild --define "_gepo_url http://gepo.company.com/config/trunk/prod" to customize
# galaxy.agent.config-root in galaxy.conf
%{?!_gepo_url: %define _gepo_url GEPO_URL}

# Use rpmbuild --define "_gepobin_url http://gepo.company.com/binaries" to customize
# galaxy.agent.config-root in galaxy.conf
%{?!_gepobin_url: %define _gepobin_url GEPOBIN_URL}

%description
Galaxy is a lightweight software deployment and management tool used to manage the Java cores and Apache httpd instances that make up the Ning platform.

%prep

%build

%install
mkdir -p %{buildroot}/var/cache/gem
cp pkg/%{gem} %{buildroot}/var/cache/gem
mkdir -p %{buildroot}/etc/rc.d/init.d
cp -r build/start-scripts/* %{buildroot}/etc/rc.d/init.d
find %{buildroot}/etc/rc.d/init.d -type f | xargs chmod a+x

%clean
rm -rf %{buildroot}

%files
%defattr(-, root, root, -)
/var/cache/gem/*
/etc/rc.d/init.d/*

%post
# Stop and disable the agent (/etc/galaxy.conf required)
[ -f /etc/galaxy.conf ] && service galaxy-agent stop
chkconfig galaxy-agent off

# Stop and disable the gonsole (/etc/galaxy.conf required)
[ -f /etc/galaxy.conf ] && service galaxy-console stop
chkconfig galaxy-console off

# Don't kill... On Linux jails, this will affect other zones.
# We have to trust the pid...
## Kill rogue Galaxy processes
#killed_some=
#for pid in `ps -ef | grep galaxy | grep -v grep | grep -v rpm | awk '{print $2}'`
#do
#    kill $pid
#    killed_some=true
#done
#[ ! -z $killed_some ] && sleep 5
#for pid in `ps -ef | grep galaxy | grep -v grep | grep -v rpm | awk '{print $2}'`
#do
#    kill -9 $pid
#done

# Install the Galaxy gem
gem install /var/cache/gem/%{gem}

# Write Galaxy configuration
# We assume that it is an agent by default. You'll need to update this template
# on the gonsole
if [ ! -f "/etc/galaxy.conf" ]; then
            cat <<EOF > /etc/galaxy.conf
#
# Galaxy client properties
#
galaxy.client.console: %_gonsole_url

##
## Galaxy console properties
##
#galaxy.console.log: SYSLOG
#galaxy.console.log-level: INFO
#galaxy.console.ping-interval: 90
#galaxy.console.user: xncore
#galaxy.console.pid-file: /home/xncore/galaxy-console.pid

#
# Galaxy agent properties
#
galaxy.agent.console: %_gonsole_url
galaxy.agent.config-root: %_gepo_url
galaxy.agent.binaries-root: %_gepobin_url
galaxy.agent.deploy-dir: /home/xncore/deploy
galaxy.agent.data-dir: /home/xncore/data
galaxy.agent.log: SYSLOG
galaxy.agent.log-level: INFO
galaxy.agent.announce-interval: 60
galaxy.agent.user: xncore
galaxy.agent.pid-file: /home/xncore/galaxy-agent.pid
EOF
fi

# Create /etc/rc.d files for Galaxy agent
/sbin/chkconfig --add galaxy-agent

# Turn on the agent (/etc/galaxy.conf required)
[ -f /etc/galaxy.conf ] && /sbin/service galaxy-agent start
/sbin/chkconfig galaxy-agent on

# The console is not turned on by default
# /sbin/chkconfig --add galaxy-console

%preun
# Stop Galaxy services
[ -f /etc/galaxy.conf ] && service galaxy-agent stop
[ -f /etc/galaxy.conf ] && service galaxy-console stop

# Remove Galaxy services
/sbin/chkconfig --del galaxy-agent
/sbin/chkconfig --del galaxy-console

%postun
# remove the user account
/usr/sbin/userdel xncore
# Uninstall the Galaxy gem
gem uninstall -v=%{version} %{name}
# rpm -Uvh will install first and uninstall the old version afterwards
#/bin/rm -f /etc/galaxy.conf
