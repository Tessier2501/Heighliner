"""
Test suite for Heighliner spaceship navigation system
"""
import pytest
from heighliner import Heighliner


class TestHeighlinerInitialization:
    """Tests for Heighliner initialization"""
    
    def test_init_with_default_capacity(self):
        """Test initialization with default capacity"""
        ship = Heighliner("Navigator")
        assert ship.name == "Navigator"
        assert ship.capacity == 1000
        assert ship.cargo == 0
        assert ship.destination is None
        assert ship.is_folded is False
    
    def test_init_with_custom_capacity(self):
        """Test initialization with custom capacity"""
        ship = Heighliner("Guild Heighliner", capacity=5000)
        assert ship.name == "Guild Heighliner"
        assert ship.capacity == 5000
        assert ship.cargo == 0
    
    def test_init_with_negative_capacity_raises_error(self):
        """Test that negative capacity raises ValueError"""
        with pytest.raises(ValueError, match="Capacity must be non-negative"):
            Heighliner("Invalid", capacity=-100)


class TestCargoOperations:
    """Tests for cargo loading and unloading"""
    
    def test_load_cargo_success(self):
        """Test successful cargo loading"""
        ship = Heighliner("Carrier", capacity=1000)
        result = ship.load_cargo(500)
        assert result is True
        assert ship.cargo == 500
    
    def test_load_cargo_multiple_times(self):
        """Test loading cargo in multiple batches"""
        ship = Heighliner("Carrier", capacity=1000)
        ship.load_cargo(300)
        ship.load_cargo(200)
        assert ship.cargo == 500
    
    def test_load_cargo_exceeds_capacity(self):
        """Test that loading cargo beyond capacity fails"""
        ship = Heighliner("Carrier", capacity=1000)
        ship.load_cargo(800)
        result = ship.load_cargo(300)
        assert result is False
        assert ship.cargo == 800
    
    def test_load_cargo_exactly_at_capacity(self):
        """Test loading cargo exactly at capacity"""
        ship = Heighliner("Carrier", capacity=1000)
        result = ship.load_cargo(1000)
        assert result is True
        assert ship.cargo == 1000
    
    def test_load_negative_cargo_raises_error(self):
        """Test that loading negative cargo raises ValueError"""
        ship = Heighliner("Carrier", capacity=1000)
        with pytest.raises(ValueError, match="Cargo amount must be positive"):
            ship.load_cargo(-100)
    
    def test_unload_cargo_success(self):
        """Test successful cargo unloading"""
        ship = Heighliner("Carrier", capacity=1000)
        ship.load_cargo(500)
        result = ship.unload_cargo(200)
        assert result is True
        assert ship.cargo == 300
    
    def test_unload_all_cargo(self):
        """Test unloading all cargo"""
        ship = Heighliner("Carrier", capacity=1000)
        ship.load_cargo(500)
        result = ship.unload_cargo(500)
        assert result is True
        assert ship.cargo == 0
    
    def test_unload_more_than_available(self):
        """Test that unloading more than available fails"""
        ship = Heighliner("Carrier", capacity=1000)
        ship.load_cargo(300)
        result = ship.unload_cargo(500)
        assert result is False
        assert ship.cargo == 300
    
    def test_unload_negative_cargo_raises_error(self):
        """Test that unloading negative cargo raises ValueError"""
        ship = Heighliner("Carrier", capacity=1000)
        with pytest.raises(ValueError, match="Cargo amount must be positive"):
            ship.unload_cargo(-100)


class TestNavigation:
    """Tests for navigation and space folding"""
    
    def test_set_destination(self):
        """Test setting a destination"""
        ship = Heighliner("Navigator")
        ship.set_destination("Arrakis")
        assert ship.destination == "Arrakis"
    
    def test_set_empty_destination_raises_error(self):
        """Test that setting empty destination raises ValueError"""
        ship = Heighliner("Navigator")
        with pytest.raises(ValueError, match="Destination cannot be empty"):
            ship.set_destination("")
    
    def test_set_none_destination_raises_error(self):
        """Test that setting None destination raises ValueError"""
        ship = Heighliner("Navigator")
        with pytest.raises(ValueError, match="Destination cannot be empty"):
            ship.set_destination(None)
    
    def test_fold_space_without_destination(self):
        """Test that folding space without destination fails"""
        ship = Heighliner("Navigator")
        result = ship.fold_space()
        assert result is False
        assert ship.is_folded is False
    
    def test_fold_space_with_destination(self):
        """Test successful space folding with destination"""
        ship = Heighliner("Navigator")
        ship.set_destination("Caladan")
        result = ship.fold_space()
        assert result is True
        assert ship.is_folded is True
    
    def test_fold_space_twice_fails(self):
        """Test that folding space twice fails"""
        ship = Heighliner("Navigator")
        ship.set_destination("Giedi Prime")
        ship.fold_space()
        result = ship.fold_space()
        assert result is False
    
    def test_arrive_without_folding(self):
        """Test that arriving without folding returns None"""
        ship = Heighliner("Navigator")
        result = ship.arrive()
        assert result is None
    
    def test_arrive_after_folding(self):
        """Test successful arrival after folding"""
        ship = Heighliner("Navigator")
        ship.set_destination("Kaitain")
        ship.fold_space()
        result = ship.arrive()
        assert result == "Kaitain"
        assert ship.is_folded is False
        assert ship.destination is None
    
    def test_complete_journey(self):
        """Test a complete journey from start to finish"""
        ship = Heighliner("Navigator", capacity=2000)
        
        # Load cargo
        ship.load_cargo(1500)
        assert ship.cargo == 1500
        
        # Set destination and fold space
        ship.set_destination("Arrakis")
        assert ship.fold_space() is True
        
        # Arrive at destination
        destination = ship.arrive()
        assert destination == "Arrakis"
        assert ship.is_folded is False
        
        # Unload cargo
        ship.unload_cargo(1500)
        assert ship.cargo == 0


class TestStatus:
    """Tests for status reporting"""
    
    def test_get_status_empty_ship(self):
        """Test status of an empty ship"""
        ship = Heighliner("Status Test")
        status = ship.get_status()
        
        assert status["name"] == "Status Test"
        assert status["capacity"] == 1000
        assert status["cargo"] == 0
        assert status["cargo_percentage"] == 0
        assert status["destination"] is None
        assert status["is_folded"] is False
    
    def test_get_status_loaded_ship(self):
        """Test status of a loaded ship"""
        ship = Heighliner("Status Test", capacity=1000)
        ship.load_cargo(750)
        status = ship.get_status()
        
        assert status["cargo"] == 750
        assert status["cargo_percentage"] == 75.0
    
    def test_get_status_during_journey(self):
        """Test status during a journey"""
        ship = Heighliner("Status Test")
        ship.load_cargo(500)
        ship.set_destination("Arrakis")
        ship.fold_space()
        
        status = ship.get_status()
        assert status["cargo"] == 500
        assert status["cargo_percentage"] == 50.0
        assert status["destination"] == "Arrakis"
        assert status["is_folded"] is True
    
    def test_get_status_zero_capacity(self):
        """Test status with zero capacity edge case"""
        ship = Heighliner("Edge Case", capacity=0)
        status = ship.get_status()
        assert status["cargo_percentage"] == 0
