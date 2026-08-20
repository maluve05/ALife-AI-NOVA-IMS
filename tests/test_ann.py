import unittest
import math
from Alife_Simulation.code.ANNprey import ANNPrey

class TestANNPrey(unittest.TestCase):
    def setUp(self):
        self.ann = ANNPrey()

    def test_dimensions(self):
        self.assertEqual(self.ann.input_size, 81)
        self.assertEqual(self.ann.hidden_size, 8)
        self.assertEqual(self.ann.output_size, 6)
        self.assertEqual(len(self.ann.hidden_weights), 8)
        self.assertEqual(len(self.ann.hidden_weights[0]), 81)
        self.assertEqual(len(self.ann.output_weights), 6)
        self.assertEqual(len(self.ann.output_weights[0]), 8)

    def test_chromosome_decoding_and_encoding(self):
        # 8 * 81 + 8 + 6 * 8 + 6 = 648 + 8 + 48 + 6 = 710 parameters
        expected_len = 710
        test_chromo = [float(i) / 100.0 for i in range(expected_len)]
        
        self.ann.set_weights_from_chromosome(test_chromo)
        encoded = self.ann.get_chromosome()
        
        self.assertEqual(len(encoded), expected_len)
        for original, extracted in zip(test_chromo, encoded):
            self.assertAlmostEqual(original, extracted, places=5)

    def test_short_chromosome_padding(self):
        short_chromo = [1.0] * 100
        self.ann.set_weights_from_chromosome(short_chromo)
        encoded = self.ann.get_chromosome()
        self.assertEqual(len(encoded), 710)
        self.assertEqual(encoded[0], 1.0)
        self.assertEqual(encoded[-1], 0.0)

    def test_sigmoid_bounds(self):
        self.assertEqual(self.ann._sigmoid(100.0), 1.0)
        self.assertEqual(self.ann._sigmoid(-100.0), 0.0)
        self.assertAlmostEqual(self.ann._sigmoid(0.0), 0.5, places=5)

    def test_softmax_probabilities(self):
        logits = [2.0, 1.0, 0.1, -1.0, 0.0, 0.5]
        probs = self.ann._softmax(logits)
        self.assertEqual(len(probs), 6)
        self.assertAlmostEqual(sum(probs), 1.0, places=5)
        self.assertTrue(all(p >= 0.0 for p in probs))
        # Largest logit should have largest probability
        self.assertEqual(probs.index(max(probs)), 0)

    def test_forward_pass_execution(self):
        test_input = [0.5] * 81
        test_chromo = [0.1] * 710
        self.ann.set_weights_from_chromosome(test_chromo)
        
        output = self.ann.compute(test_input)
        self.assertEqual(len(output), 6)
        self.assertAlmostEqual(sum(output), 1.0, places=5)
        self.assertTrue(all(p >= 0.0 for p in output))

if __name__ == "__main__":
    unittest.main()
