# Agent Skill: SSH to Remote Host via PuTTY + Docker Commands

## Goal
Provide a repeatable procedure for an agent/operator to connect to a remote host using PuTTY on Windows and run Docker commands over SSH.

## Preconditions
- PuTTY installed (putty.exe).
- Remote host IP/hostname and SSH port available.
- SSH username (and password or private key).
- Docker installed on the remote host.

## Connection (PuTTY)
1. Open **PuTTY**.
2. In **Host Name (or IP address)**, enter the remote IP/hostname.
3. Set **Port** (default 22) and **Connection type** = SSH.
4. (Optional) Save a session:
   - In **Saved Sessions**, enter a name and click **Save**.
5. (Optional, key auth) Go to:
   - **Connection > SSH > Auth > Credentials**
   - Browse and select your **.ppk** key file.
6. Click **Open** and accept the host key on first connection.
7. Login with the SSH username (and password if required).

## Verify Docker is available (remote)
```bash
whoami
hostname
docker ps
```

## Common Docker commands (remote)
```bash
# list containers
docker ps -a

# logs
docker logs -n 200 <container_name>

# exec into container
docker exec -it <container_name> sh

# compose (if installed)
docker compose ps
```

## Example: Run sync-client inside container (remote)
```bash
docker exec -i sync-client python sync_client.py 0_sync_test.sql
docker exec -i sync-client python sync_client.py 1_sync_bed_an_occupancy.sql
```

## Troubleshooting
- **Permission denied**: confirm SSH user, key, or password.
- **Host key mismatch**: remove old host key in PuTTY (Registry) or change session name.
- **Docker not found**: install Docker on remote host or ensure user is in `docker` group.
- **Container not found**: check `docker ps -a` to verify container name.

## Notes
- Prefer using container/service name instead of IP for inter-container communication in Docker networks.
- Keep sensitive credentials out of scripts; use environment variables or SSH keys.
