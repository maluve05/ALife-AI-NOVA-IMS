"""
ANNprey.py

Pure mathematical Feed-Forward Artificial Neural Network (ANN) execution path.
Operates deterministically. Computes priority activation/probability distribution
over the 6 motor action channels.
"""
import math
from typing import List

class ANNPrey:
    def __init__(self):
        """
        Initializes an empty neural network.
        Inputs: 81 (80 vision inputs + 1 hunger input)
        Hidden layer: 8 neurons
        Output layer: 6 neurons
        """
        self.input_size = 81
        self.hidden_size = 8
        self.output_size = 6
        
        # Dimensions:
        # hidden_weights: 8 rows (neurons) x 81 columns (inputs)
        # hidden_biases: 8 elements
        # output_weights: 6 rows (neurons) x 8 columns (hidden)
        # output_biases: 6 elements
        self.hidden_weights: List[List[float]] = [[0.0] * self.input_size for _ in range(self.hidden_size)]
        self.hidden_biases: List[float] = [0.0] * self.hidden_size
        self.output_weights: List[List[float]] = [[0.0] * self.hidden_size for _ in range(self.output_size)]
        self.output_biases: List[float] = [0.0] * self.output_size

    def set_weights_from_chromosome(self, chromosome: List[float]):
        """
        Populates the weights and biases from a flat 1D chromosome list of size 710.
        710 = (8 * 81) + 8 + (6 * 8) + 6
        """
        expected_len = (self.hidden_size * self.input_size) + self.hidden_size + (self.output_size * self.hidden_size) + self.output_size
        if len(chromosome) < expected_len:
            # Pad with zeros if short (should not happen under normal run)
            chromosome = list(chromosome) + [0.0] * (expected_len - len(chromosome))
        
        idx = 0
        
        # 1. Input-to-Hidden weights (8 * 81 = 648)
        for i in range(self.hidden_size):
            for j in range(self.input_size):
                self.hidden_weights[i][j] = chromosome[idx]
                idx += 1
                
        # 2. Hidden biases (8)
        for i in range(self.hidden_size):
            self.hidden_biases[i] = chromosome[idx]
            idx += 1
            
        # 3. Hidden-to-Output weights (6 * 8 = 48)
        for i in range(self.output_size):
            for j in range(self.hidden_size):
                self.output_weights[i][j] = chromosome[idx]
                idx += 1
                
        # 4. Output biases (6)
        for i in range(self.output_size):
            self.output_biases[i] = chromosome[idx]
            idx += 1

    def get_chromosome(self) -> List[float]:
        """
        Flattens current weights and biases back into a single 1D chromosome list.
        """
        chromosome = []
        # 1. Input-to-Hidden weights
        for i in range(self.hidden_size):
            chromosome.extend(self.hidden_weights[i])
        # 2. Hidden biases
        chromosome.extend(self.hidden_biases)
        # 3. Hidden-to-Output weights
        for i in range(self.output_size):
            chromosome.extend(self.output_weights[i])
        # 4. Output biases
        chromosome.extend(self.output_biases)
        return chromosome

    @staticmethod
    def _tanh(x: float) -> float:
        """Hyperbolic tangent activation function."""
        # Avoid overflow/underflow issues
        if x > 20.0:
            return 1.0
        elif x < -20.0:
            return -1.0
        return math.tanh(x)

    @staticmethod
    def _softmax(x_vec: List[float]) -> List[float]:
        """Softmax activation function to turn raw values into probability distributions."""
        max_val = max(x_vec)  # Stability subtraction
        exps = [math.exp(x - max_val) for x in x_vec]
        sum_exps = sum(exps)
        if sum_exps == 0.0:
            return [1.0 / len(x_vec)] * len(x_vec)
        return [e / sum_exps for e in exps]

    def compute(self, input_vector: List[float]) -> List[float]:
        """
        Performs forward propagation.
        :param input_vector: List of 81 float inputs (80 vision + 1 hunger)
        :returns: List of 6 floats representing probability distribution over actions.
        """
        # Hidden layer activation: tanh(W_h * x + b_h)
        hidden_activations = [0.0] * self.hidden_size
        for i in range(self.hidden_size):
            dot_product = sum(input_vector[j] * self.hidden_weights[i][j] for j in range(self.input_size))
            hidden_activations[i] = self._tanh(dot_product + self.hidden_biases[i])
            
        # Output layer activation: softmax(W_o * h + b_o)
        raw_outputs = [0.0] * self.output_size
        for i in range(self.output_size):
            dot_product = sum(hidden_activations[j] * self.output_weights[i][j] for j in range(self.hidden_size))
            raw_outputs[i] = dot_product + self.output_biases[i]
            
        return self._softmax(raw_outputs)
