# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
	config.vm.define "docker" do |docker|
		docker.vm.box = "cdempsey1221/ndms-rocky9-docker-amd64-virtualbox"
		docker.vm.box_version = "1.0.1"
		docker.vm.hostname = 'docker-vm'
		docker.ssh.username = 'vagrant'
		docker.ssh.password = 'vagrant'
		docker.ssh.insert_key = 'true'
		config.vm.synced_folder "../.", "/vagrant", mount_options: ["dmode=777"], type: "virtualbox"
		define_network_stack(docker)
		docker.vm.provider "virtualbox" do |vb|
			vb.memory = "2048"
			vb.cpus = "2"
		end
	end
end

def define_network_stack(docker)
	docker.vm.network "forwarded_port", guest: 22, host: 2245, id: "ssh", auto_correct: false
	docker.vm.network "forwarded_port", guest: 8080, host: 8080, id: "nginxWebPort", auto_correct: false
	docker.vm.network "private_network", ip: "192.168.60.68", virtualbox__intnet: "docker_net"
end
