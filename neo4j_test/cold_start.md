# This is what you do if you haven't done anything:
1. Open terminal
2. Type `cd ./neo4j_test`
3. Ensure Docker Desktop is running, then run `docker compose up --build` from the terminal
4. Wait until all containers have started, then navigate to `localhost:15433`
5. Authenticate with email `atvars.apinis@student.howest.be` and password `AtvarsViola` (or change them in the compose.yml file before restarting the services)
6. Right-click on the "Servers" drop-down on the left side of the screen, hover over "Register...", then select "Server"
7. In "General",  enter the name of the server (this can be anything you want)
8. Open the "Connection" tab, and enter "postgres" for the "Host name/address". Then, enter "AtvarsViola" for both the username and password. Finally, check "Save Password?"
9. Click "Save"
10. You should see a new PostGres server (Elephant icon). Click on the dropdown icon, then right-click on Databases. Click on Create -> Database, enter the name "TaleMachine", and click "Save"


