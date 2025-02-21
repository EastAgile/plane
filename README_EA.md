# Installation (for EA fork) - only need to perform once
- Create the root directory
```
mkdir plane-selfhost
cd plane-selfhost
```

- Save env vars to load later, create `.env` file with these lines
```
export GIT_REPO="EastAgile/plane"
export BRANCH="ea_main"
export CUSTOM_BUILD="true"
```

- Load the env vars
```
source .env
```

- Fetch initial setup script
```
curl -fsSL -o setup.sh https://raw.githubusercontent.com/EastAgile/plane/ea_main/deploy/selfhost/install.sh
chmod +x setup.sh
```

- Install (choose y/Yes if asked)
```
./setup.sh install
```

- Update `plane-app/plane.env`, mostly these keys (note the https for `WEB_URL` and `CORS_ALLOWED_ORIGINS`)
```
APP_DOMAIN=plane.expansionplan.ai

NGINX_PORT=9999
WEB_URL=https://${APP_DOMAIN}
CORS_ALLOWED_ORIGINS=https://${APP_DOMAIN}
```

- Update `plane-app/docker-compose.yaml`, prepending `/mnt/slow_safe/plane-selfhost/docker_volumes/` (or where you want all volume data in) before each volume path, something like below.
- Also comment out `proxy:` part if needed (like on knowledge servers already with a proxy)
```
plane-db:
    volumes:
      - /mnt/slow_safe/plane-selfhost/docker_volumes/pgdata:/var/lib/postgresql/data

plane-redis:
    volumes:
      - /mnt/slow_safe/plane-selfhost/docker_volumes/redisdata:/data

plane-mq:
    volumes:
      - /mnt/slow_safe/plane-selfhost/docker_volumes/rabbitmq_data:/var/lib/rabbitmq

plane-minio:
    volumes:
      - /mnt/slow_safe/plane-selfhost/docker_volumes/uploads:/export

api:
    volumes:
      - /mnt/slow_safe/plane-selfhost/docker_volumes/logs_api:/code/plane/logs

worker:
    volumes:
      - /mnt/slow_safe/plane-selfhost/docker_volumes/logs_worker:/code/plane/logs

beat-worker:
    volumes:
      - /mnt/slow_safe/plane-selfhost/docker_volumes/logs_beat-worker:/code/plane/logs

migrator:
    volumes:
      - /mnt/slow_safe/plane-selfhost/docker_volumes/logs_migrator:/code/plane/logs
```

- Start stack
```
./setup.sh start
```

# Migrate PT data

- Clone the scripts repo https://github.com/EastAgile/PT-emigration, `cd` into it

- Follow the instructions there to run a PT export

- Compress the results (one `pivotal_tracker_data.db` file and one `attachments` folder) into a zip file

- Copy `/plane/sample.env` to `/plane/.env`, make modifications if needed but default values are good

- Compress the whole `plane` directory (still in the script repo) into another zip file

- Bring both zip files to the server where plane selfhost is running via docker, unzip them to a separate folder, cd into it. Make sure the hierarchy looks like this
```
attachments
config.py
.env
pivotal_tracker_data.db
requirements.txt
run_migration.py
scripts
utils.py
```

- Create new python environment and install dependencies
```
python3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
```

- Verify connections
```
python utils.py
```

- If everything looks good, run the migration process
```
python run_migration.py
```

# Maintenance (for EA fork)

- Update the codebase as needed and push to the github repo

- Go to `plane-selfhost` directory and `source .env` to load env vars again

- Perform the update (will stop the docker stack, pull new code and build them). Also type y/Yes when asked
```
./setup.sh upgrade
```

- Check plane env again as the upgrade often override the `https` back to `http` for `WEB_URL` and `CORS_ALLOWED_ORIGINS`
```
nano plane-app/plane.env
```

- Start the stack again
```
./setup.sh start
```


# Configure custom Slack webhook

- Go to https://api.slack.com/apps/A08DC5CF5AT/incoming-webhooks

- At the bottom, click "Add New Webhook to Workspace" and follow the steps

- Note the webhook url (`https://hooks.slack.com/... `)

- Visit the plane workspace settings page as a workspace owner

- Click on "Webhooks" section and "Add webhook" (or edit existing ones)

- Select either all events or individual events

- Select either all projects or selected projects

- Create or save (update)