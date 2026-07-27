import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import os
from datetime import datetime

class ModelTrainer:
    """
    A model training class that handles model loading, training, evaluation, and saving.
    """
    
    def __init__(self, model, device='cpu'):
        """
        Initialize the trainer.
        
        Args:
            model: PyTorch model to train
            device: Device to run training ('cpu' or 'cuda')
        """
        self.model = model
        self.device = device
        self.criterion = nn.CrossEntropyLoss()  # Default loss function
        self.optimizer = optim.Adam(model.parameters(), lr=0.001)
        self.scheduler = optim.lr_scheduler.StepLR(self.optimizer, step_size=10, gamma=0.1)
        
    def set_loss_function(self, loss_fn):
        """Set custom loss function."""
        self.criterion = loss_fn
        
    def set_optimizer(self, optimizer):
        """Set custom optimizer."""
        self.optimizer = optimizer
        
    def set_learning_rate(self, lr):
        """Set learning rate."""
        for param_group in self.optimizer.param_groups:
            param_group['lr'] = lr
            
    def train_epoch(self, train_loader):
        """
        Train for one epoch.
        
        Args:
            train_loader: DataLoader for training data
            
        Returns:
            dict with training metrics
        """
        self.model.train()
        total_loss = 0
        correct = 0
        total = 0
        
        for batch_idx, (inputs, targets) in enumerate(train_loader):
            inputs, targets = inputs.to(self.device), targets.to(self.device)
            
            # Zero gradients
            self.optimizer.zero_grad()
            
            # Forward pass
            outputs = self.model(inputs)
            loss = self.criterion(outputs, targets)
            
            # Backward pass and optimize
            loss.backward()
            self.optimizer.step()
            
            # Update metrics
            total_loss += loss.item()
            _, predicted = outputs.max(1)
            total += targets.size(0)
            correct += predicted.eq(targets).sum().item()
            
        avg_loss = total_loss / len(train_loader)
        accuracy = 100. * correct / total
        return {'loss': avg_loss, 'accuracy': accuracy}
    
    def evaluate(self, val_loader):
        """
        Evaluate the model on validation data.
        
        Args:
            val_loader: DataLoader for validation data
            
        Returns:
            dict with evaluation metrics
        """
        self.model.eval()
        total_loss = 0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for inputs, targets in val_loader:
                inputs, targets = inputs.to(self.device), targets.to(self.device)
                outputs = self.model(inputs)
                loss = self.criterion(outputs, targets)
                
                total_loss += loss.item()
                _, predicted = outputs.max(1)
                total += targets.size(0)
                correct += predicted.eq(targets).sum().item()
        
        avg_loss = total_loss / len(val_loader)
        accuracy = 100. * correct / total
        return {'loss': avg_loss, 'accuracy': accuracy}
    
    def train(self, train_loader, val_loader, num_epochs=10, save_path=None):
        """
        Train the model for multiple epochs.
        
        Args:
            train_loader: DataLoader for training data
            val_loader: DataLoader for validation data
            num_epochs: Number of training epochs
            save_path: Path to save the model
            
        Returns:
            dict with training history
        """
        history = {
            'train_loss': [],
            'train_accuracy': [],
            'val_loss': [],
            'val_accuracy': []
        }
        
        print(f"Starting training on {self.device}...")
        print(f"Total epochs: {num_epochs}")
        
        for epoch in range(num_epochs):
            # Train
            train_metrics = self.train_epoch(train_loader)
            
            # Evaluate
            val_metrics = self.evaluate(val_loader)
            
            # Log metrics
            history['train_loss'].append(train_metrics['loss'])
            history['train_accuracy'].append(train_metrics['accuracy'])
            history['val_loss'].append(val_metrics['loss'])
            history['val_accuracy'].append(val_metrics['accuracy'])
            
            print(f"Epoch {epoch+1}/{num_epochs} - "
                  f"Train Loss: {train_metrics['loss']:.4f}, "
                  f"Train Acc: {train_metrics['accuracy']:.2f}%, "
                  f"Val Loss: {val_metrics['loss']:.4f}, "
                  f"Val Acc: {val_metrics['accuracy']:.2f}%")
            
            # Learning rate scheduler
            self.scheduler.step()
        
        # Save model
        if save_path:
            self.save_model(save_path)
            
        return history
    
    def save_model(self, path):
        """
        Save the model to disk.
        
        Args:
            path: Path to save the model
        """
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epoch': 0,
            'history': None
        }, path)
        print(f"Model saved to {path}")
    
    def save_checkpoint(self, path, epoch, history):
        """
        Save a checkpoint with training history.
        
        Args:
            path: Path to save the checkpoint
            epoch: Current epoch
            history: Training history
        """
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epoch': epoch,
            'history': history
        }, path)
        print(f"Checkpoint saved to {path}")
    
    def load_model(self, path):
        """
        Load model from checkpoint.
        
        Args:
            path: Path to the checkpoint
        """
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        print(f"Model loaded from {path}")


def main():
    """
    Main training function with example usage.
    """
    # Example: Create a simple model
    model = nn.Sequential(
        nn.Linear(10, 64),
        nn.ReLU(),
        nn.Dropout(0.5),
        nn.Linear(64, 10)
    )
    
    # Example: Create dummy data
    X = torch.randn(1000, 10)
    y = torch.randint(0, 10, (1000,))
    
    # Create data loaders
    train_size = int(0.8 * len(X))
    train_dataset = TensorDataset(X[:train_size], y[:train_size])
    val_dataset = TensorDataset(X[train_size:], y[train_size:])
    
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=32)
    
    # Initialize trainer
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    trainer = ModelTrainer(model, device=device)
    
    # Train the model
    history = trainer.train(
        train_loader=train_loader,
        val_loader=val_loader,
        num_epochs=10,
        save_path=f'models/model_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pth'
    )
    
    # Final evaluation
    final_metrics = trainer.evaluate(val_loader)
    print(f"\nFinal Validation - Loss: {final_metrics['loss']:.4f}, Accuracy: {final_metrics['accuracy']:.2f}%")


if __name__ == '__main__':
    main()
