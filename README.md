# Heighliner

A simple spaceship navigation system inspired by the Dune universe. The Heighliner class provides functionality for managing cargo and navigating through folded space.

## Features

- Cargo management (loading/unloading)
- Space navigation with destination setting
- Space folding capability for interstellar travel
- Status reporting

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
from heighliner import Heighliner

# Create a new Heighliner spaceship
ship = Heighliner("Navigator", capacity=2000)

# Load cargo
ship.load_cargo(1500)

# Set destination and fold space
ship.set_destination("Arrakis")
ship.fold_space()

# Arrive at destination
destination = ship.arrive()
print(f"Arrived at {destination}")

# Unload cargo
ship.unload_cargo(1500)

# Check status
status = ship.get_status()
print(status)
```

## Running Tests

Run all tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=heighliner --cov-report=html
```

Run tests verbosely:
```bash
pytest -v
```
