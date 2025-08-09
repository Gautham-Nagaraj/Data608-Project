# Stock Roulette API (game-api)

This service implements the backend for the Stock Roulette game, providing RESTful endpoints for game sessions, stock selections, trades, and an admin dashboard.

ssh connection:
5432
8000

## Setup
0. connect to  ubuntu ec2
```
ssh -R 0.0.0.0:11435:visaggpu02.cs.ucalgary.ca:11434 -i "<pem_file>.pem" ubuntu@<public_ip>
```

1. **Clone repository**:
    ```bash
   git clone https://github.com/Gautham-Nagaraj/Data608-Project.git
   cd Data608-Project/game-api
    ````

2. Setup ubuntu ec2
```bash
./setup-ubuntu-vm.sh
```

3. **Configure environment**:

   * Copy `.env.example` to `.env`:

     ```bash
     cp .env.example .env
     ```
   * Fill in `DATABASE_URL`, `SECRET_KEY`, etc.

4. **Run migrations**:

   ```bash
   uv run migrate
   ```

5. **Start the server**:

   * Development (with hot reload):

     ```bash
     uv run dev
     ```
   * Production:

     ```bash
     uv run start
     ```

## Database

* Managed via Alembic migrations in `alembic/`.