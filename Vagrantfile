# -*- mode: ruby -*-
# vi: set ft=ruby :

# Specify minimum Vagrant version and Vagrant API version
Vagrant.require_version '>= 1.6.0'
VAGRANTFILE_API_VERSION = '2'

# Create and configure the VMs
Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  # Always use Vagrant's default insecure key
  config.ssh.insert_key = false

  # Don't check for box updates
  config.vm.box_check_update = false

  # Specify the hostname of the VM
  config.vm.hostname = "patzilla-testdrive"

  # Specify the Vagrant box to use
  config.vm.box = "debian/stretch64"
  #config.vm.box = "ubuntu/bionic64"

  # Configure network
  config.vm.network "private_network", ip: "192.168.50.50"

  # Configure host specifications
  config.vm.provider "virtualbox" do |v|
    v.memory = 2048
    v.cpus = 4
  end

  # Mount source code directory
  config.vm.synced_folder ".", "/opt/patzilla-testdrive"

end # Vagrant.configure
