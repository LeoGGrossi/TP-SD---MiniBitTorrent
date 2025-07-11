param(
    [string]$peerId = $(Read-Host "Enter peer ID (e.g. peer1)"),
    [int]$port = $(Read-Host "Enter port number (e.g. 9001)")
)

# Create fresh peer VM directory
New-Item -ItemType Directory -Path ".\peer_$peerId" -Force
Copy-Item "peer.py" -Destination ".\peer_$peerId"

$vagrantContent = @"
Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/focal64"
  config.vm.network "forwarded_port", guest: $port, host: $port
  
  config.vm.provider "virtualbox" do |vb|
    vb.memory = "1024"  # More RAM for file handling
    vb.cpus = 1
    vb.name = "bittorrent-peer-$peerId"
  end

  config.vm.provision "shell", inline: <<-SHELL
    apt-get update
    apt-get install -y python3
    mkdir -p /home/vagrant/project
    echo 'Peer $peerId ready - run manually with:'
    echo 'cd /home/vagrant/project && python3 peer.py'
  SHELL
end
"@

$vagrantContent | Out-File -FilePath ".\peer_$peerId\Vagrantfile" -Encoding ASCII

Write-Host "Starting peer $peerId VM..."
Set-Location ".\peer_$peerId"
vagrant up
vagrant ssh -c "cd /home/vagrant/project && python3 peer.py"