### Gavel CI
Example CI service for JobServ.

## Local Development Environment
For a quick **development** setup, most environments may take the following steps:

#### Initializing
The following script establishes a simple local development installation

```bash
./run.sh setup
```
*[docker], [openssl], and [mkcert] must be installed*

#### Registering
Registering the gavel-ci development environment happens outside of installation:

  - Step 1: Add '/etc/hosts' entry `127.0.0.1 api.gavelci.us gavelci.us`
  - Step 2: Establish Github Application, Token, and Access
    - register a [Github App] with the local URL, `https://gavelci.us/`, and the
      local callback URL, `https://gavelci.us/auth/gh-authorized`
    - create a [Github Personal Access Token] with complete access
    - expose the local `api` to Github with [ngrok]: `$ ngrok http 9700`
    - retain the Github Client ID, Github Client Secret, Personal Access
      Token, and ngrok `http` URL for the next steps
  - Step 3: Update local `.env` file values:
    - `GITHUB_CLIENT_ID`
    - `GITHUB_CLIENT_SECRET`
    - `JOBSERV_URL` # this should be the http link from ngrok
  - Step 4: Start up application with: `$ docker-compose up`
  - Step 5: Register JobServ Worker(s)
   
     Register a worker with any linux machine with:
    
   ```bash
     $ mkdir jobserv-worker && cd jobserv-worker
     $ curl https://api.gavelci.us/worker > jobserv_worker.py
     $ chmod +x jobserv_worker.py
     $ ./jobserv_worker.py register --hostname=d http://<xxx>.ngrok.io amd64
     $ ./jobserv_worker.py loop
   ```
  - Step 6: Enlist JobServ Worker(s)
   
      Enlist a worker from the host machine with:

   ```bash
     $ docker exec -it $(docker ps --filter name=api -q) flask worker enlist d
   ```
   *you're now ready to set up a [Gavel-CI Project] and kick off your first build*
 
 Look to [Jobserv] for more information regarding workers and projects!

[docker]: https://github.com/docker/docker-ce
[Gavel-CI Project]: https://github.com/foundriesio/jobserv/blob/master/docs/docker-compose.md#setting-up-a-project
[Gavel-CI UI]: https://gavelci.us
[Github App]: https://github.com/settings/applications/new
[Github Personal Acccess Token]: https://github.com/settings/tokens/new
[Jobserv]: https://github.com/foundriesio/jobserv
[mkcert]: https://github.com/FiloSottile/mkcert
[ngrok]: https://ngrok.com
[openssl]: https://github.com/openssl/openssl