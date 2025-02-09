# Overview

This project is built using python, **FastAPI**, **RocksDB (Plyvel)**, and **Docker**.

---

## Features

- **Distributed Architecture** – Multiple instances (`web1`, `web2`, `web3`) for high availability.
- **Persistent Storage** – Uses RocksDB with WAL for durability.
- **Replication** – Asynchronous data replication across nodes.
- **Recovery Mechanism** – WAL replay for crash recovery.
- **Efficient Caching** – LRU cache for fast read operations.

---

## Project Structure

```

root/
│── src/                    # Source code for the application
│   ├── app.py              # Application entry point
│   ├── config.py           # Configuration and environment variables
│   ├── recovery.py         # Write-Ahead Log (WAL) recovery
│   ├── replication.py      # Replication manager
│   ├── routes.py           # API endpoints
│   ├── storage.py          # Persistent key-value store (RocksDB)
│── data/                   # Persistent storage for RocksDB
│── docker/                 # Docker-related files
│   ├── docker-compose.yml  # Docker configuration
│   ├── Dockerfile          # Dockerfile for building app container
│── .env                    # Environment variables
│── requirements.txt        # Python dependencies

```

---

## Getting Started

### Clone the Repository

```sh
git clone <repo-url>
cd <repo-name>
```

### Run with Docker

Build and start the containers:

```sh
cd docker
docker-compose up --build -d
```

## API Endpoints

### Base Url

```
http://127.0.0.1:5001
http://127.0.0.1:5002
http://127.0.0.1:5003
```

### Store a Key-Value Pair

```http
POST /put
{
  "key": "username",
  "value": "john_doe"
}
```

### Read a Value

```http
GET /read/{key}
```

### Batch Store Multiple Key-Value Pairs

```http
POST /batchput
[
  { "key": "user1", "value": "Alice" },
  { "key": "user2", "value": "Bob" }
]
```

### Read Key Range

```http
GET /readrange?start_key=user1&end_key=user2
```

### Delete a Key

```http
POST /delete
{
  "key": "username"
}
```

---

## Logging & Monitoring

```sh
docker logs moniepoint-app-1
```
