import math
from typing import List

class ANNPrey:
    def __init__(self):
        self.input_size = 81
        self.hidden_size = 8
        self.output_size = 6
        
        self.hidden_weights: List[List[float]] = [[0.0] * self.input_size for _ in range(self.hidden_size)]
        self.hidden_biases: List[float] = [0.0] * self.hidden_size
        self.output_weights: List[List[float]] = [[0.0] * self.hidden_size for _ in range(self.output_size)]
        self.output_biases: List[float] = [0.0] * self.output_size

    def set_weights_from_chromosome(self, chromosome: List[float]):
        expected_chromosome_length = (
            (self.hidden_size * self.input_size)
            + self.hidden_size
            + (self.output_size * self.hidden_size)
            + self.output_size
        )
        if len(chromosome) < expected_chromosome_length:
            padding_length = expected_chromosome_length - len(chromosome)
            chromosome = list(chromosome) + [0.0] * padding_length
        
        offset = self._set_hidden_layer_parameters(chromosome)
        self._set_output_layer_parameters(chromosome, offset)

    def _set_hidden_layer_parameters(self, chromosome: List[float]) -> int:
        chromosome_index = 0
        for hidden_neuron_idx in range(self.hidden_size):
            for input_idx in range(self.input_size):
                self.hidden_weights[hidden_neuron_idx][input_idx] = chromosome[chromosome_index]
                chromosome_index += 1
                
        for hidden_neuron_idx in range(self.hidden_size):
            self.hidden_biases[hidden_neuron_idx] = chromosome[chromosome_index]
            chromosome_index += 1
        return chromosome_index

    def _set_output_layer_parameters(self, chromosome: List[float], offset: int):
        chromosome_index = offset
        for output_neuron_idx in range(self.output_size):
            for hidden_neuron_idx in range(self.hidden_size):
                self.output_weights[output_neuron_idx][hidden_neuron_idx] = chromosome[chromosome_index]
                chromosome_index += 1
                
        for output_neuron_idx in range(self.output_size):
            self.output_biases[output_neuron_idx] = chromosome[chromosome_index]
            chromosome_index += 1

    def get_chromosome(self) -> List[float]:
        chromosome = []
        for hidden_neuron_idx in range(self.hidden_size):
            chromosome.extend(self.hidden_weights[hidden_neuron_idx])
        chromosome.extend(self.hidden_biases)
        for output_neuron_idx in range(self.output_size):
            chromosome.extend(self.output_weights[output_neuron_idx])
        chromosome.extend(self.output_biases)
        return chromosome
    @staticmethod
    def _sigmoid(net_input: float) -> float:
        if net_input > 20.0:
            return 1.0
        elif net_input < -20.0:
            return 0.0
        return 1.0 / (1.0 + math.exp(-net_input))

    @staticmethod
    def _softmax(logits: List[float]) -> List[float]:
        max_logit = max(logits)
        exponential_logits = [math.exp(logit - max_logit) for logit in logits]
        sum_exponential_logits = sum(exponential_logits)
        if sum_exponential_logits == 0.0:
            return [1.0 / len(logits)] * len(logits)
        return [exp_val / sum_exponential_logits for exp_val in exponential_logits]

    def compute(self, input_vector: List[float]) -> List[float]:
        hidden_activations = self._forward_hidden_layer(input_vector)
        raw_outputs = self._forward_output_layer(hidden_activations)
        return self._softmax(raw_outputs)

    def _forward_hidden_layer(self, input_vector: List[float]) -> List[float]:
        hidden_activations = [0.0] * self.hidden_size
        for hidden_neuron_idx in range(self.hidden_size):
            weighted_sum = sum(
                input_vector[input_idx] * self.hidden_weights[hidden_neuron_idx][input_idx]
                for input_idx in range(self.input_size)
            )
            hidden_activations[hidden_neuron_idx] = self._sigmoid(weighted_sum + self.hidden_biases[hidden_neuron_idx])
        return hidden_activations

    def _forward_output_layer(self, hidden_activations: List[float]) -> List[float]:
        raw_outputs = [0.0] * self.output_size
        for output_neuron_idx in range(self.output_size):
            weighted_sum = sum(
                hidden_activations[hidden_neuron_idx] * self.output_weights[output_neuron_idx][hidden_neuron_idx]
                for hidden_neuron_idx in range(self.hidden_size)
            )
            raw_outputs[output_neuron_idx] = weighted_sum + self.output_biases[output_neuron_idx]
        return raw_outputs
