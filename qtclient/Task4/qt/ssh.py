import paramiko

def sshCommando(hostname, port, username, password, command):
    sshClient =paramiko.SSHClient()

    sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    sshClient.load_system_host_keys()
    sshClient.connect(hostname, port ,username,password)
    stdin,stdout, stderr=sshClient.exec_command(command)
    print(stdout.read())



