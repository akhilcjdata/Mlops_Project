"""Test script for model training functionality."""

import pytest


def test_model_training():
    """Test that model training can be imported and instantiated."""
    from src.model.train_model import ModelTrainer
    
    trainer = ModelTrainer()
    assert trainer is not None


def test_model_training_with_data():
    """Test model training with sample data."""
    from src.model.train_model import ModelTrainer
    
    trainer = ModelTrainer()
    
    # Test with sample data
    X_train = [[1, 2], [3, 4], [5, 6]]
    y_train = [1, 0, 1]
    
    trainer.fit(X_train, y_train)
    assert trainer is not None


if __name__ == "__main__":
    test_model_training()
    test_model_training_with_data()
    print("All tests passed!")
