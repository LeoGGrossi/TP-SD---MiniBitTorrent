# Create fresh tracker VM
$trackerFiles = @("tracker.py", "README.md")  # Only essential files

# Create temp directory with just tracker files
New-Item -ItemType Directory -Path .\tracker_vm -Force
Copy-Item $trackerFiles -Destination .\tracker_vm

$vagrantContent = @"
Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/focal64"
  config.vm.network "forwarded_port", guest: 8000, host: 8000
  
  config.vm.provider "virtualbox" do |vb|
    vb.memory = "512"
    vb.cpus = 1
    vb.name = "bittorrent-tracker"
  end

  config.vm.provision "shell", inline: <<-SHELL
    apt-get update
    apt-get install -y python3
    mkdir -p /home/vagrant/project
    echo 'Tracker ready - run manually with:'
    echo 'cd /home/vagrant/project && python3 tracker.py'
  SHELL
end
"@

$vagrantContent | Out-File -FilePath .\tracker_vm\Vagrantfile -Encoding ASCII

Write-Host "Starting tracker VM..."
Set-Location .\tracker_vm
vagrant up
vagrant ssh -c "cd /home/vagrant/project && python3 tracker.py"