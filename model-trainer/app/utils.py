import torch
import os


def setup_gpu():
    """
    Configure PyTorch to use the GPU if available.

    This function checks for GPU availability and reports the device that will be used.

    Returns:
        torch.device: The device to use for training.
    """
    print("Configuring PyTorch device...")
    if torch.cuda.is_available():
        device = torch.device('cuda')
        print(f"GPU available: {torch.cuda.get_device_name(0)}")
        print(f"Number of GPUs: {torch.cuda.device_count()}")
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        device = torch.device('mps')
        print("Apple Silicon MPS device available.")
    else:
        device = torch.device('cpu')
        print("No GPU/MPS found. Will use CPU.")
    return device


def select_directory(base_path, prompt):
    """
    Prompt the user to select a directory from a list.

    Args:
        base_path (str): The base path containing directories to choose from.
        prompt (str): The prompt message for the user.

    Returns:
        str: The selected directory path, or None if no selection was made.
    """
    print(f"Selecting directory from {base_path}")
    print(f"Directory contents: {os.listdir(base_path)}")
    directories = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
    if not directories:
        print(f"No directories found in {base_path}")
        return None

    print(f"{prompt}")
    for i, directory in enumerate(directories):
        print(f"{i+1}. {directory}")

    while True:
        try:
            choice = input("Enter the number of your choice: ")
            index = int(choice) - 1
            if 0 <= index < len(directories):
                selected = os.path.join(base_path, directories[index])
                print(f"Selected directory: {selected}")
                return selected
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")
