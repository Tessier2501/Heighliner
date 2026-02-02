"""
Heighliner - A simple spaceship navigation system
Inspired by the Dune universe
"""


class Heighliner:
    """A Heighliner spaceship capable of transporting cargo across space"""
    
    def __init__(self, name, capacity=1000):
        """
        Initialize a Heighliner spaceship
        
        Args:
            name (str): The name of the spaceship
            capacity (int): Maximum cargo capacity in tons
        """
        if capacity < 0:
            raise ValueError("Capacity must be non-negative")
        self.name = name
        self.capacity = capacity
        self.cargo = 0
        self.destination = None
        self.is_folded = False
    
    def _validate_amount(self, amount):
        """
        Validate that cargo amount is positive
        
        Args:
            amount (int): Amount to validate
            
        Raises:
            ValueError: If amount is negative
        """
        if amount < 0:
            raise ValueError("Cargo amount must be positive")
    
    def load_cargo(self, amount):
        """
        Load cargo onto the spaceship
        
        Args:
            amount (int): Amount of cargo to load in tons
            
        Returns:
            bool: True if cargo was loaded successfully, False otherwise
        """
        self._validate_amount(amount)
        
        if self.cargo + amount > self.capacity:
            return False
        
        self.cargo += amount
        return True
    
    def unload_cargo(self, amount):
        """
        Unload cargo from the spaceship
        
        Args:
            amount (int): Amount of cargo to unload in tons
            
        Returns:
            bool: True if cargo was unloaded successfully, False otherwise
        """
        self._validate_amount(amount)
        
        if amount > self.cargo:
            return False
        
        self.cargo -= amount
        return True
    
    def set_destination(self, destination):
        """
        Set the destination for the spaceship
        
        Args:
            destination (str): The destination planet/system
        """
        if not destination:
            raise ValueError("Destination cannot be empty")
        self.destination = destination
    
    def fold_space(self):
        """
        Engage space folding to travel to destination
        
        Returns:
            bool: True if space folding was successful, False otherwise
        """
        if not self.destination:
            return False
        
        if self.is_folded:
            return False
        
        self.is_folded = True
        return True
    
    def arrive(self):
        """
        Arrive at destination and exit folded space
        
        Returns:
            str: The destination arrived at, or None if not in folded space
        """
        if not self.is_folded:
            return None
        
        arrived_at = self.destination
        self.is_folded = False
        self.destination = None
        return arrived_at
    
    def get_status(self):
        """
        Get the current status of the spaceship
        
        Returns:
            dict: Current status information
        """
        return {
            "name": self.name,
            "capacity": self.capacity,
            "cargo": self.cargo,
            "cargo_percentage": (self.cargo / self.capacity * 100) if self.capacity > 0 else 0,
            "destination": self.destination,
            "is_folded": self.is_folded
        }
